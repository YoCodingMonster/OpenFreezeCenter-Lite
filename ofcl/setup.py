"""First-run setup.

Two questions, the same two the GUI asks: which side of Intel's 11th
generation the processor is on, and where the auto fan curve should come
from.  Everything else has a sensible default and can be changed later.
"""

from . import config as cfg
from . import profiles
from . import prompt
from .ec import ECError

CPU_QUESTION = (
    "The EC uses different registers on either side of Intel's 11th\n"
    "  generation. Pick the wrong one and fan control will not take effect."
)

CURVE_QUESTION = (
    "Read the curve the firmware is using right now, or start from a\n"
    "  known-good generic curve. To capture MSI's own curve: boot Windows,\n"
    "  set the fan profile to Auto there, then come back and read it."
)


def run(term, controller, existing=None):
    """Ask the setup questions and return a saved Config."""
    term.line()
    term.line(term.rule("Set up Open Freeze Center Lite"))

    default_gen = "11+" if existing is None else (
        "11+" if existing.hardware.cpu_gen_11_plus else "10-"
    )
    term.line()
    term.line("  " + term.paint(CPU_QUESTION, "dim"))
    generation = prompt.choose(
        term,
        "Processor generation",
        [
            ("11+", "11th gen", "Intel 11th generation or newer, or AMD"),
            ("10-", "10th gen", "Intel 10th generation or older"),
        ],
        default=default_gen,
    )
    config = cfg.Config(
        hardware=cfg.Hardware.for_cpu_generation(generation == "11+")
    )

    term.line()
    term.line("  " + term.paint(CURVE_QUESTION, "dim"))
    source = prompt.choose(
        term,
        "Auto fan curve",
        [
            ("ec", "Read", "take the curve the EC is holding right now"),
            ("generic", "Generic", "%s / %s"
             % (", ".join(str(v) for v in cfg.DEFAULT_AUTO_CPU),
                ", ".join(str(v) for v in cfg.DEFAULT_AUTO_GPU))),
        ],
        default="ec",
    )

    if source == "ec":
        try:
            cpu, gpu = profiles.read_auto_curve(controller, config)
        except ECError as error:
            term.line("  " + term.paint("Could not read the EC: " + error.title, "yellow"))
            term.line("  " + term.paint("Falling back to the generic curve.", "yellow"))
        else:
            if any(cpu) or any(gpu):
                config.auto_cpu, config.auto_gpu = cpu, gpu
            else:
                term.line(
                    "  " + term.paint(
                        "The EC curve reads as all zeroes; using the generic curve.",
                        "yellow",
                    )
                )

    config.advanced_cpu = list(config.auto_cpu)
    config.advanced_gpu = list(config.auto_gpu)
    config.normalise()
    cfg.save(config)

    term.line()
    term.line("  Settings written to " + term.paint(cfg.config_path(), "bold"))
    term.line()
    return config
