"""The blocks of text the program prints.

Kept apart from the commands so the same readout can be shown by `status`, by
`monitor` redrawing it twice a second, and by the interactive menu.
"""

import time

from . import config as cfg
from . import profiles
from .terminal import bar, sparkline, table, temperature_style

POINT_LABELS = (
    "1 idle",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7 hottest",
)


def _rpm(value):
    return "%5d rpm" % value if value else "   off    "


def sensor_lines(term, monitor, reading, graph=True):
    """Temperatures, fan speeds, extremes, and the rolling history."""
    lines = []
    label_width = 5
    graph_width = max(20, min(term.width - 34, 60))

    for name, temp, rpm, low, high, history in (
        (
            "CPU",
            reading.cpu_temp,
            reading.cpu_rpm,
            monitor.cpu_min,
            monitor.cpu_max,
            monitor.cpu_history,
        ),
        (
            "GPU",
            reading.gpu_temp,
            reading.gpu_rpm,
            monitor.gpu_min,
            monitor.gpu_max,
            monitor.gpu_history,
        ),
    ):
        head = "  " + term.paint(name.ljust(label_width), "bold")
        head += term.paint("%3d%s" % (temp, term.degree), *temperature_style(temp))
        head += "   " + _rpm(rpm)
        head += term.paint(
            "   min %d  max %d" % (low if low != 999 else temp, high), "dim"
        )
        lines.append(head)
        if graph:
            spark = sparkline(history, term, width=graph_width)
            lines.append("  " + " " * label_width + term.paint(spark, "cyan"))
    return lines


def curve_lines(term, cpu, gpu, note=""):
    """The seven CPU and seven GPU points, drawn as bars."""
    width = max(10, min(term.width - 34, 40))
    lines = []
    for name, values in (("CPU fan", cpu), ("GPU fan", gpu)):
        lines.append("  " + term.paint(name, "bold"))
        for label, value in zip(POINT_LABELS, values):
            lines.append(
                "    %-10s %s %3d%%"
                % (label, term.paint(bar(value, 100, width, term), "cyan"), value)
            )
    if note:
        lines.append("  " + term.paint(note, "dim"))
    return lines


def profile_summary(config):
    """One line describing the profile, for headers and confirmations."""
    text = profiles.PROFILE_LABELS[config.profile]
    if config.profile == cfg.PROFILE_BASIC:
        text += " (%+d%%)" % config.basic_offset
    if config.cooler_booster:
        text += " + Cooler Booster"
    return text


def status_lines(term, config, controller, monitor=None, reading=None):
    """Everything `status` prints: settings, hardware state, sensors."""
    lines = [term.rule("Open Freeze Center Lite"), ""]

    try:
        reported, booster = profiles.active_profile(controller, config)
    except Exception:  # noqa: BLE001 - the caller reports EC failures properly
        reported = booster = None

    profile_text = profile_summary(config)
    if reported is not None and reported != config.profile:
        profile_text += term.paint(
            "   (the EC is currently in %s)" % profiles.PROFILE_LABELS[reported], "yellow"
        )
    booster_text = "on" if config.cooler_booster else "off"
    if booster is not None and booster != config.cooler_booster:
        booster_text += term.paint(
            "   (the EC reports %s)" % ("on" if booster else "off"), "yellow"
        )

    rows = [
        ("Profile", profile_text),
        ("Cooler Booster", booster_text),
        ("Battery limit", "%d%%" % config.battery_threshold),
        ("Settings", cfg.config_path()),
    ]
    if controller.simulated:
        rows.append(("Controller", term.paint("simulated — no hardware touched", "yellow")))
    lines += table(rows, term)

    cpu, gpu = profiles.curve_for(config)
    lines += ["", term.rule("Fan curve in force"), ""]
    lines += curve_lines(
        term,
        cpu,
        gpu,
        note="Auto profile: the firmware decides, these are the stored points."
        if config.profile == cfg.PROFILE_AUTO
        else "",
    )

    if reading is not None and monitor is not None:
        lines += ["", term.rule("Sensors"), ""]
        lines += sensor_lines(term, monitor, reading, graph=False)
    lines.append("")
    return lines


def monitor_lines(term, config, monitor, reading):
    """The block `monitor` redraws on every tick."""
    lines = [term.rule("Monitoring"), ""]
    lines += sensor_lines(term, monitor, reading)
    lines += [
        "",
        "  "
        + term.paint(profile_summary(config), "magenta")
        + term.paint("    last %ds  ·  Ctrl-C to stop" % monitor_span(monitor), "dim"),
    ]
    return lines


def monitor_span(monitor):
    """How many seconds of history are actually on screen."""
    return max(1, int(round(len(monitor.cpu_history) * monitor.interval)))


def live_monitor(term, config, monitor, plain=False, count=None):
    """Draw readings until the count runs out or the user interrupts.

    Shared by `monitor` and the menu so both stop cleanly and both fall back
    to one line per reading where a redraw would only scroll — a terminal
    with no cursor control, or output going to a file.
    """
    plain = plain or not term.ansi
    previous = 0
    term.hide_cursor()
    try:
        for reading in monitor.run(count):
            if plain:
                term.line(plain_reading(term, reading))
                term.flush()
            else:
                previous = term.redraw(
                    monitor_lines(term, config, monitor, reading), previous
                )
    except KeyboardInterrupt:
        term.line()
    finally:
        term.show_cursor()


def plain_reading(term, reading):
    """One reading on one line, for logs and dumb terminals."""
    return "%s  CPU %3d%s %5d rpm   GPU %3d%s %5d rpm" % (
        time.strftime("%H:%M:%S", time.localtime(reading.timestamp)),
        reading.cpu_temp, term.degree, reading.cpu_rpm,
        reading.gpu_temp, term.degree, reading.gpu_rpm,
    )
