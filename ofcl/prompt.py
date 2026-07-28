"""Reading answers from a person.

The old script asked with bare `input()` and recursed on a bad answer, so a
typo three levels down eventually hit the recursion limit and a Ctrl-D
printed a traceback.  These loop instead, and turn end-of-input into `Abort`,
which the command layer catches and turns into a clean exit.
"""


class Abort(Exception):
    """The user pressed Ctrl-C or Ctrl-D."""


def _read(term, question):
    """Print the question through the terminal, then read a line.

    The prompt does not go to `input()` directly so that it passes through the
    same encoding fallback as everything else this prints.
    """
    term.write(term.paint("?", "cyan") + " " + question + ": ")
    term.flush()
    try:
        return input().strip()
    except (EOFError, KeyboardInterrupt):
        raise Abort()


def text(term, question, default=""):
    suffix = " [%s]" % default if default else ""
    answer = _read(term, question + suffix)
    return answer or default


def confirm(term, question, default=True):
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        answer = _read(term, question + suffix).lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        term.line("  Answer y or n.")


def integer(term, question, low, high, default=None):
    while True:
        answer = text(term, "%s (%d to %d)" % (question, low, high),
                      "" if default is None else str(default))
        if not answer:
            continue
        try:
            value = int(answer)
        except ValueError:
            term.line("  That is not a whole number.")
            continue
        if low <= value <= high:
            return value
        term.line("  Out of range: pick between %d and %d." % (low, high))


def choose(term, question, options, default=None):
    """Ask a numbered multiple-choice question.

    `options` is a list of (key, label, description); the chosen key comes
    back.  Numbers and unambiguous name prefixes are both accepted, because
    typing `a` for Auto is what everybody tries first.
    """
    term.line()
    term.line("  " + term.paint(question, "bold"))
    described = any(option[2] for option in options)
    pad = max(len(option[1]) for option in options)
    for index, option in enumerate(options, 1):
        key, label, description = option
        marker = term.paint(" *", "green") if key == default else "  "
        row = "   %s %d) %s" % (marker, index, label.ljust(pad) if described else label)
        if description:
            row += "  " + term.paint(description, "dim")
        term.line(row)
    term.line()

    while True:
        answer = text(term, "Choice", "" if default is None else str(default))
        if not answer:
            continue
        if answer.isdigit():
            index = int(answer)
            if 1 <= index <= len(options):
                return options[index - 1][0]
        else:
            lowered = answer.lower()
            matches = [
                option[0]
                for option in options
                if option[0].lower().startswith(lowered)
                or option[1].lower().startswith(lowered)
            ]
            if len(matches) == 1:
                return matches[0]
        term.line("  Pick one of the numbers above.")


def speed_list(term, question, current):
    """Ask for seven comma-separated fan speeds, offering the current ones."""
    from . import config as cfg

    shown = ", ".join(str(value) for value in current)
    while True:
        answer = text(term, question, shown)
        parts = [part for part in answer.replace(",", " ").split() if part]
        try:
            values = [int(part) for part in parts]
        except ValueError:
            term.line("  Whole numbers only, separated by spaces or commas.")
            continue
        if len(values) != cfg.FAN_POINTS:
            term.line("  Give exactly %d values." % cfg.FAN_POINTS)
            continue
        if any(value < cfg.SPEED_MIN or value > cfg.SPEED_MAX for value in values):
            term.line(
                "  Each value must be between %d and %d."
                % (cfg.SPEED_MIN, cfg.SPEED_MAX)
            )
            continue
        return values
