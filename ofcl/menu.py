"""The interactive menu, shown when the program is run with no command.

The old script asked one question, did one thing and exited, so setting a
profile and then checking a temperature meant starting it twice.  This stays
open until you quit, and every screen ends back here.
"""

import sys

from . import config as cfg
from . import profiles
from . import prompt
from . import setup as setup_module
from . import views
from .ec import ECError
from .monitor import Monitor


def run(context):
    term = context.term
    if not (term.interactive and sys.stdin.isatty()):
        sys.stderr.write(
            "The menu needs a terminal. Run a command instead, for example:\n"
            "    openfreezecenter-lite status\n"
            "    openfreezecenter-lite --help\n"
        )
        return 1

    actions = [
        ("profile", "Fan profile", _profile),
        ("booster", "Cooler Booster", _booster),
        ("curves", "Fan curves", _curves),
        ("battery", "Battery limit", _battery),
        ("monitor", "Monitoring", _monitor),
        ("status", "Status", _status),
        ("setup", "Re-run setup", _setup),
        ("quit", "Quit", None),
    ]

    while True:
        _header(context)
        try:
            choice = prompt.choose(
                term,
                "What would you like to do?",
                [(key, label, "") for key, label, _ in actions],
            )
        except prompt.Abort:
            term.line()
            return 0

        if choice == "quit":
            return 0
        handler = dict((key, function) for key, _, function in actions)[choice]
        try:
            handler(context)
        except prompt.Abort:
            term.line()
        except KeyboardInterrupt:
            term.line()
        except ECError as error:
            term.line()
            term.line(term.paint(error.title, "bold", "red"))
            term.line(error.detail)
            if error.hint:
                term.line()
                term.line(error.hint)


def _header(context):
    term = context.term
    config = context.config
    term.line()
    term.line(term.rule("Open Freeze Center Lite"))
    line = "  " + term.paint(views.profile_summary(config), "bold")
    line += term.paint("   battery limit %d%%" % config.battery_threshold, "dim")
    try:
        monitor = Monitor(context.controller, config)
        reading = monitor.sample()
    except ECError:
        pass
    else:
        line += "   CPU %d%s   GPU %d%s" % (
            reading.cpu_temp, term.degree, reading.gpu_temp, term.degree
        )
    term.line(line)


###############################################################################
# Menu actions
###############################################################################


def _profile(context):
    config = context.config
    choice = prompt.choose(
        context.term,
        "Fan profile",
        [
            (name, profiles.PROFILE_LABELS[name], profiles.PROFILE_DESCRIPTIONS[name])
            for name in cfg.PROFILE_ORDER
        ],
        default=config.profile,
    )
    config.profile = choice
    if choice == cfg.PROFILE_BASIC:
        config.basic_offset = prompt.integer(
            context.term,
            "Shift from the auto curve, in percent",
            cfg.OFFSET_MIN,
            cfg.OFFSET_MAX,
            default=config.basic_offset,
        )
    config.normalise()
    context.save_and_apply("Profile is now " + views.profile_summary(config) + ".")


def _booster(context):
    config = context.config
    enabled = prompt.confirm(
        context.term,
        "Run both fans flat out, whatever the profile says?",
        default=not config.cooler_booster,
    )
    config.cooler_booster = enabled
    context.save()
    profiles.apply_cooler_booster(context.controller, config, enabled)
    context.done("Cooler Booster %s." % ("on" if enabled else "off"))


def _curves(context):
    term = context.term
    config = context.config

    while True:
        term.line()
        term.line(term.rule("Advanced curve"))
        term.line()
        for line in views.curve_lines(term, config.advanced_cpu, config.advanced_gpu):
            term.line(line)

        choice = prompt.choose(
            term,
            "Fan curves",
            [
                ("cpu", "CPU", "set the seven CPU points"),
                ("gpu", "GPU", "set the seven GPU points"),
                ("copy", "Copy", "replace the advanced curve with the auto curve"),
                ("read", "Read", "store the firmware's current curve as Auto"),
                ("back", "Back", ""),
            ],
            default="back",
        )

        if choice == "back":
            return

        edited = "advanced"
        if choice == "cpu":
            config.advanced_cpu = prompt.speed_list(
                term, "CPU fan speeds, coolest first", config.advanced_cpu
            )
        elif choice == "gpu":
            config.advanced_gpu = prompt.speed_list(
                term, "GPU fan speeds, coolest first", config.advanced_gpu
            )
        elif choice == "copy":
            config.advanced_cpu = list(config.auto_cpu)
            config.advanced_gpu = list(config.auto_gpu)
        elif choice == "read":
            edited = "auto"
            cpu, gpu = profiles.read_auto_curve(context.controller, config)
            if any(cpu) or any(gpu):
                config.auto_cpu, config.auto_gpu = cpu, gpu
                context.done("Auto curve read from the EC.")
            else:
                context.warn("The EC curve reads as all zeroes; nothing imported.")

        config.normalise()
        context.save()
        if profiles.uses_curve(config, edited):
            context.apply()
            context.done("Curve applied.")
        elif config.profile == cfg.PROFILE_AUTO:
            context.warn(
                "Stored only — the Auto profile leaves the fans to the firmware."
            )
        else:
            context.warn(
                "Stored only — the %s profile does not use that curve."
                % profiles.PROFILE_LABELS[config.profile]
            )


def _battery(context):
    config = context.config
    config.battery_threshold = prompt.integer(
        context.term,
        "Stop charging at",
        cfg.BATTERY_MIN,
        cfg.BATTERY_MAX,
        default=config.battery_threshold,
    )
    context.save()
    profiles.apply_battery_threshold(
        context.controller, config, config.battery_threshold
    )
    context.done("Battery charge limit set to %d%%." % config.battery_threshold)
    context.warn("Some models only apply a new limit after a reboot.")


def _monitor(context):
    context.term.line()
    views.live_monitor(
        context.term, context.config, Monitor(context.controller, context.config)
    )


def _status(context):
    monitor = Monitor(context.controller, context.config)
    try:
        reading = monitor.sample()
    except ECError:
        reading = None
    for line in views.status_lines(
        context.term, context.config, context.controller, monitor, reading
    ):
        context.term.line(line)
    prompt.text(context.term, "Press enter to go back")


def _setup(context):
    context.config = setup_module.run(
        context.term, context.controller, context.config
    )
    context.apply()
    context.done("Setup complete and applied.")
