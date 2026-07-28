"""Command line interface.

    openfreezecenter-lite                 interactive menu
    openfreezecenter-lite profile auto    one thing, then exit

Every command that changes something writes the setting to the config file
and then to the EC, so a scripted change and a change made through the menu
leave the machine in the same state.
"""

import argparse
import json
import os
import sys

from . import __version__
from . import config as cfg
from . import profiles
from . import prompt
from . import setup as setup_module
from . import views
from .ec import ECError, EmbeddedController, SimulatedController, ensure_interface
from .monitor import Monitor
from .terminal import Terminal

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NO_EC = 2


def print_ec_error(term, error):
    term.line()
    term.line(term.paint(error.title, "bold", "red"))
    term.line()
    term.line(error.detail)
    if error.hint:
        term.line()
        term.line(error.hint)


class Context(object):
    """What every command needs: a terminal, an EC, and the settings."""

    def __init__(self, term, controller, config):
        self.term = term
        self.controller = controller
        self.config = config

    def save(self):
        cfg.save(self.config)

    def apply(self):
        profiles.apply_profile(self.controller, self.config)

    def save_and_apply(self, message=None):
        self.save()
        self.apply()
        if message:
            self.done(message)

    def done(self, message):
        self.term.line("  " + self.term.paint("ok", "green") + "  " + message)

    def warn(self, message):
        self.term.line("  " + self.term.paint("!", "yellow") + "   " + message)


###############################################################################
# Commands
###############################################################################


def command_status(context, args):
    monitor = Monitor(context.controller, context.config)
    try:
        reading = monitor.sample()
    except ECError:
        reading = None

    if args.json:
        payload = context.config.to_dict()
        payload["curve_in_force"] = dict(
            zip(("cpu", "gpu"), profiles.curve_for(context.config))
        )
        payload["reading"] = reading.to_dict() if reading else None
        print(json.dumps(payload, indent=2, sort_keys=True))
        return EXIT_OK

    for line in views.status_lines(
        context.term, context.config, context.controller, monitor, reading
    ):
        context.term.line(line)
    if reading is None:
        context.warn("Sensors could not be read.")
    return EXIT_OK


def command_monitor(context, args):
    term = context.term
    monitor = Monitor(context.controller, context.config, interval=args.interval)

    if args.json:
        for reading in monitor.run(args.count):
            print(json.dumps(reading.to_dict(), sort_keys=True))
            sys.stdout.flush()
        return EXIT_OK

    views.live_monitor(term, context.config, monitor, args.plain, args.count)
    return EXIT_OK


def command_profile(context, args):
    config = context.config
    if args.offset is not None:
        config.basic_offset = cfg.clamp(args.offset, cfg.OFFSET_MIN, cfg.OFFSET_MAX)

    if args.name is None and args.offset is None:
        context.term.line("  " + views.profile_summary(config))
        return EXIT_OK

    if args.name is not None:
        config.profile = args.name
        if args.name == cfg.PROFILE_BASIC and args.offset is None:
            context.warn(
                "Basic is the auto curve shifted by %+d%%; set another shift with "
                "--offset." % config.basic_offset
            )

    config.normalise()
    context.save_and_apply("Profile is now " + views.profile_summary(config) + ".")
    return EXIT_OK


def command_booster(context, args):
    config = context.config
    if args.state is None:
        context.term.line("  Cooler Booster is %s." % ("on" if config.cooler_booster else "off"))
        return EXIT_OK

    enabled = not config.cooler_booster if args.state == "toggle" else args.state == "on"
    config.cooler_booster = enabled
    context.save()
    profiles.apply_cooler_booster(context.controller, config, enabled)
    context.done("Cooler Booster %s." % ("on" if enabled else "off"))
    return EXIT_OK


def command_battery(context, args):
    config = context.config
    if args.percent is None:
        context.term.line("  Battery charge limit is %d%%." % config.battery_threshold)
        return EXIT_OK

    config.battery_threshold = cfg.clamp(args.percent, cfg.BATTERY_MIN, cfg.BATTERY_MAX)
    if config.battery_threshold != args.percent:
        context.warn(
            "Clamped to %d%%; the EC accepts %d to %d."
            % (config.battery_threshold, cfg.BATTERY_MIN, cfg.BATTERY_MAX)
        )
    context.save()
    profiles.apply_battery_threshold(
        context.controller, config, config.battery_threshold
    )
    context.done("Battery charge limit set to %d%%." % config.battery_threshold)
    context.warn("Some models only apply a new limit after a reboot.")
    return EXIT_OK


def _parse_speeds(text):
    parts = [part for part in text.replace(",", " ").split() if part]
    values = [int(part) for part in parts]
    if len(values) != cfg.FAN_POINTS:
        raise ValueError("expected %d values, got %d" % (cfg.FAN_POINTS, len(values)))
    return values


def command_curve(context, args):
    config = context.config
    changed = set()

    if args.read_from_ec:
        cpu, gpu = profiles.read_auto_curve(context.controller, config)
        if any(cpu) or any(gpu):
            config.auto_cpu, config.auto_gpu = cpu, gpu
            changed.add("auto")
            context.done("Auto curve read from the EC.")
        else:
            context.warn("The EC curve reads as all zeroes; nothing imported.")

    if args.copy_from_auto:
        config.advanced_cpu = list(config.auto_cpu)
        config.advanced_gpu = list(config.auto_gpu)
        changed.add("advanced")
        context.done("Advanced curve copied from Auto.")

    for option, attribute, label in (
        (args.cpu, "advanced_cpu", "CPU"),
        (args.gpu, "advanced_gpu", "GPU"),
    ):
        if option is None:
            continue
        try:
            setattr(config, attribute, _parse_speeds(option))
        except ValueError as error:
            context.term.line(
                "  " + context.term.paint("error", "red")
                + "  %s curve: %s" % (label, error)
            )
            return EXIT_ERROR
        changed.add("advanced")
        context.done("%s curve set." % label)

    if changed:
        config.normalise()
        context.save()
        if any(profiles.uses_curve(config, which) for which in changed):
            context.apply()

    term = context.term
    term.line()
    term.line(term.rule("Advanced curve"))
    term.line()
    for line in views.curve_lines(term, config.advanced_cpu, config.advanced_gpu):
        term.line(line)
    term.line()
    term.line(term.rule("Auto curve"))
    term.line()
    for line in views.curve_lines(term, config.auto_cpu, config.auto_gpu):
        term.line(line)
    term.line()
    if changed and not any(profiles.uses_curve(config, which) for which in changed):
        context.warn(_stored_only(config, changed))
    return EXIT_OK


def _stored_only(config, changed):
    """Why a curve edit did not reach the fans."""
    if config.profile == cfg.PROFILE_AUTO:
        return "Stored only — the Auto profile leaves the fans to the firmware."
    if "advanced" in changed:
        return (
            "Stored only — the Basic profile runs the auto curve, not the "
            "advanced one. Switch with `profile advanced`."
        )
    return "Stored only — the profile in force does not use that curve."


def command_apply(context, args):
    profiles.apply_all(context.controller, context.config)
    context.done(
        "Applied %s, battery limit %d%%."
        % (views.profile_summary(context.config), context.config.battery_threshold)
    )
    return EXIT_OK


def command_setup(context, args):
    context.config = setup_module.run(
        context.term, context.controller, context.config
    )
    context.apply()
    context.done("Setup complete and applied.")
    return EXIT_OK


def command_config(context, args):
    if args.what == "path":
        print(cfg.config_path())
    else:
        print(json.dumps(context.config.to_dict(), indent=2, sort_keys=True))
    return EXIT_OK


def command_menu(context, args):
    from . import menu

    return menu.run(context)


###############################################################################
# Argument parsing
###############################################################################


def _global_flags():
    """Options accepted both before and after the command name.

    `--simulate status` and `status --simulate` should both work, so these
    live on every subparser as well as on the top level.  The defaults are
    SUPPRESSed: without that, a subparser re-applying its own default would
    wipe out a flag that was given before the command name.
    """
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--simulate",
        action="store_true",
        default=argparse.SUPPRESS,
        help="run against a fake embedded controller, on any machine",
    )
    common.add_argument(
        "--no-colour", "--no-color",
        dest="no_colour",
        action="store_true",
        default=argparse.SUPPRESS,
        help="never emit colour escape sequences",
    )
    common.add_argument(
        "--ascii",
        action="store_true",
        default=argparse.SUPPRESS,
        help="draw with plain ASCII instead of block characters",
    )
    return common


def build_parser():
    common = _global_flags()
    parser = argparse.ArgumentParser(
        prog="openfreezecenter-lite",
        description="Fan and battery control for MSI laptops, from the terminal.",
        epilog="Run with no command for an interactive menu.",
        parents=[common],
    )
    parser.add_argument("--version", action="version", version="OFC-l " + __version__)

    subparsers = parser.add_subparsers(dest="command")

    def add(name, help_text):
        return subparsers.add_parser(name, help=help_text, parents=[common])

    status = add("status", "show settings and current sensors")
    status.add_argument("--json", action="store_true", help="machine-readable output")
    status.set_defaults(handler=command_status)

    monitor = add("monitor", "live temperatures and fan speeds")
    monitor.add_argument(
        "-i", "--interval", type=float, default=0.5, metavar="SECONDS",
        help="seconds between readings (default: 0.5)",
    )
    monitor.add_argument(
        "-n", "--count", type=int, default=None, metavar="N",
        help="stop after N readings (default: until Ctrl-C)",
    )
    monitor.add_argument(
        "--plain", action="store_true",
        help="one line per reading instead of a redrawn display",
    )
    monitor.add_argument(
        "--json", action="store_true", help="one JSON object per reading"
    )
    monitor.set_defaults(handler=command_monitor)

    profile = add("profile", "select the fan profile")
    profile.add_argument(
        "name", nargs="?", choices=list(cfg.PROFILE_ORDER),
        help="auto, basic or advanced; omit to show the current one",
    )
    profile.add_argument(
        "--offset", type=int, metavar="PERCENT",
        help="shift for the Basic profile, %d to %d" % (cfg.OFFSET_MIN, cfg.OFFSET_MAX),
    )
    profile.set_defaults(handler=command_profile)

    booster = add("booster", "Cooler Booster on or off")
    booster.add_argument(
        "state", nargs="?", choices=("on", "off", "toggle"),
        help="omit to show the current state",
    )
    booster.set_defaults(handler=command_booster)

    curve = add("curve", "show or set the fan curves")
    curve.add_argument("--cpu", metavar="A,B,C,D,E,F,G", help="seven CPU fan speeds")
    curve.add_argument("--gpu", metavar="A,B,C,D,E,F,G", help="seven GPU fan speeds")
    curve.add_argument(
        "--copy-from-auto", action="store_true",
        help="replace the advanced curve with the auto curve",
    )
    curve.add_argument(
        "--read-from-ec", action="store_true",
        help="store the curve the firmware is holding as the auto curve",
    )
    curve.set_defaults(handler=command_curve)

    battery = add("battery", "battery charge limit")
    battery.add_argument(
        "percent", nargs="?", type=int,
        help="%d to %d; omit to show the current limit"
        % (cfg.BATTERY_MIN, cfg.BATTERY_MAX),
    )
    battery.set_defaults(handler=command_battery)

    apply_parser = add("apply", "write the saved settings to the EC (use at boot)")
    apply_parser.set_defaults(handler=command_apply)

    setup_parser = add("setup", "re-run first-time setup")
    setup_parser.set_defaults(handler=command_setup, needs_config=False)

    config_parser = add("config", "show the settings file")
    config_parser.add_argument(
        "what", nargs="?", choices=("show", "path"), default="show"
    )
    config_parser.set_defaults(
        handler=command_config, needs_ec=False, needs_config=False
    )

    return parser


###############################################################################
# Entry point
###############################################################################


def _open_controller(term, simulate, needs_ec):
    if simulate:
        return SimulatedController()

    controller = EmbeddedController()
    if not needs_ec:
        return controller

    for step in ensure_interface():
        term.line("  " + term.paint(step, "dim"))
    try:
        controller.check()
    except ECError as error:
        print_ec_error(term, error)
        if os.geteuid() != 0:
            term.line()
            term.line("This program needs root to reach the embedded controller:")
            command = sys.argv[0] if "/" in sys.argv[0] else os.path.basename(sys.argv[0])
            term.line("    sudo %s" % " ".join([command] + sys.argv[1:]))
        term.line()
        term.line("To look around without any hardware, add --simulate.")
        term.line()
        return None
    return controller


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    term = Terminal(
        colour=False if getattr(args, "no_colour", False) else None,
        ascii_only=getattr(args, "ascii", False),
    )

    handler = getattr(args, "handler", command_menu)
    needs_ec = getattr(args, "needs_ec", True)

    controller = _open_controller(term, getattr(args, "simulate", False), needs_ec)
    if controller is None:
        return EXIT_NO_EC
    if controller.simulated:
        # On stderr, so `config path` and the --json output stay pipeable.
        sys.stderr.write("simulated hardware - nothing is really being set\n")

    config = cfg.load()
    if config is None:
        if not getattr(args, "needs_config", True):
            # `setup` is about to write one, and `config` can describe the
            # defaults without any file existing.
            config = cfg.Config()
        elif sys.stdin.isatty():
            term.line("No settings yet, so let us make some.")
            config = setup_module.run(term, controller)
        else:
            term.flush()
            sys.stderr.write(
                "No settings file at %s.\n"
                "Run `openfreezecenter-lite setup` from a terminal first.\n"
                % cfg.config_path()
            )
            return EXIT_ERROR

    context = Context(term, controller, config)
    try:
        return handler(context, args)
    except prompt.Abort:
        term.line()
        return EXIT_OK
    except KeyboardInterrupt:
        term.line()
        return EXIT_OK
    except ECError as error:
        print_ec_error(term, error)
        return EXIT_NO_EC
