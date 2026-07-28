"""Terminal output that degrades instead of breaking.

Three things vary between the machines this has to run on: whether the
terminal understands colour, whether it can print box-drawing and block
characters, and how wide it is.  All three are decided once, here, and
everything else asks this module rather than assuming a modern xterm.

Nothing is drawn with curses: a serial console, a `screen` session on a
decade-old server, and output redirected to a log file all have to work, and
the redraw this needs is four lines of ANSI.
"""

import os
import shutil
import sys

# Only the eight original colours, which every colour-capable terminal since
# the 1980s has had.
STYLES = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
}

HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CLEAR_LINE = "\033[2K"
LINE_UP = "\033[1A"

# No blank at the bottom of either ramp: a space in the middle of a sparkline
# reads as missing data rather than as a low reading.
BLOCKS = "▁▂▃▄▅▆▇█"
ASCII_BLOCKS = "._-=+*#@"

# Applied to every line before it is written, when the terminal cannot take
# UTF-8.  A message written months from now with an em dash in it should not
# be able to end the program with a UnicodeEncodeError on a machine running
# in the POSIX locale.
PLAIN = {
    ord("—"): "-",
    ord("–"): "-",
    ord("·"): "*",
    ord("…"): "...",
    ord("’"): "'",
    ord("°"): "",
}


def _supports_ansi(stream):
    """Whether escape sequences mean anything on this stream.

    Cursor movement is a separate question from colour: `--no-colour` on a
    real terminal should still redraw the monitor in place rather than
    scrolling a new block past every half second.
    """
    if not hasattr(stream, "isatty") or not stream.isatty():
        return False
    return os.environ.get("TERM", "") not in ("", "dumb")


def _supports_unicode(stream):
    if os.environ.get("OFC_ASCII"):
        return False
    encoding = getattr(stream, "encoding", None) or ""
    if "utf" not in encoding.lower().replace("-", ""):
        return False
    try:
        BLOCKS.encode(encoding)
    except (UnicodeError, LookupError):
        return False
    return True


class Terminal(object):
    """What this particular terminal can do, and how to write to it."""

    def __init__(self, stream=None, colour=None, ascii_only=False):
        self.stream = stream or sys.stdout
        self.interactive = hasattr(self.stream, "isatty") and self.stream.isatty()
        self.ansi = _supports_ansi(self.stream)
        if colour is None:
            colour = bool(os.environ.get("FORCE_COLOR")) or (
                self.ansi and os.environ.get("NO_COLOR") is None
            )
        self.colour = colour
        self.unicode = not ascii_only and _supports_unicode(self.stream)
        self.blocks = BLOCKS if self.unicode else ASCII_BLOCKS
        self.degree = "°C" if self.unicode else "C"

    @property
    def width(self):
        try:
            return max(40, shutil.get_terminal_size((80, 24)).columns)
        except (AttributeError, OSError, ValueError):
            return 80

    ###########################################################################
    # Writing
    ###########################################################################

    def paint(self, text, *styles):
        if not self.colour or not styles:
            return text
        prefix = "".join(STYLES.get(style, "") for style in styles)
        return prefix + text + STYLES["reset"]

    def plain(self, text):
        """`text` reduced to something this terminal can definitely encode."""
        if self.unicode:
            return text
        return text.translate(PLAIN).encode("ascii", "replace").decode("ascii")

    def write(self, text=""):
        self.stream.write(self.plain(text))

    def line(self, text=""):
        self.stream.write(self.plain(text) + "\n")

    def flush(self):
        try:
            self.stream.flush()
        except (IOError, ValueError):
            pass

    def rule(self, title="", width=None):
        width = width or min(self.width, 78)
        dash = "─" if self.unicode else "-"
        if not title:
            return dash * width
        head = dash * 2 + " " + title + " "
        return head + dash * max(0, width - _display_length(head))

    ###########################################################################
    # In-place redraw, for `monitor`
    ###########################################################################

    def hide_cursor(self):
        if self.ansi:
            self.write(HIDE_CURSOR)
            self.flush()

    def show_cursor(self):
        if self.ansi:
            self.write(SHOW_CURSOR)
            self.flush()

    def redraw(self, lines, previous):
        """Reprint a block of lines over the previous one.

        `previous` is how many lines are already on screen; the return value
        is how many are there now, to be handed back on the next call.  When
        the output is not a terminal the block is simply appended, which is
        what you want in a log file.
        """
        in_place = self.ansi
        if in_place and previous:
            # Up one line and wipe it, once per line already printed, leaving
            # the cursor at the start of where the block began.
            self.write((LINE_UP + CLEAR_LINE) * previous + "\r")
        for text in lines:
            self.line((CLEAR_LINE if in_place else "") + text)
        self.flush()
        return len(lines) if in_place else 0


###############################################################################
# Small drawing helpers
###############################################################################


def _display_length(text):
    """Length of `text` ignoring any escape sequences it contains."""
    length = 0
    skipping = False
    for char in text:
        if skipping:
            skipping = char not in "m"
            continue
        if char == "\033":
            skipping = True
            continue
        length += 1
    return length


def sparkline(values, term, width=None, low=None, high=None):
    """A one-line history graph, most recent value on the right."""
    values = list(values)
    blocks = term.blocks
    if not values:
        return ""
    if width is not None and len(values) > width:
        values = values[-width:]
    low = min(values) if low is None else low
    high = max(values) if high is None else high
    if high <= low:
        high = low + 1
    span = float(high - low)
    out = []
    for value in values:
        level = int(round((value - low) / span * (len(blocks) - 1)))
        out.append(blocks[max(0, min(len(blocks) - 1, level))])
    return "".join(out)


def bar(value, maximum, width, term):
    """A horizontal bar, used for fan curve points."""
    if maximum <= 0:
        return " " * width
    filled = int(round(min(value, maximum) / float(maximum) * width))
    if term.unicode:
        return "█" * filled + "░" * (width - filled)
    return "#" * filled + "." * (width - filled)


def temperature_style(temp):
    """Cool, warm, hot — the same thresholds the GUI colours its charts by."""
    if temp >= 85:
        return ("bold", "red")
    if temp >= 70:
        return ("yellow",)
    return ("green",)


def table(rows, term, indent="  "):
    """Left-aligned label/value pairs, values lined up under each other."""
    if not rows:
        return []
    pad = max(len(str(label)) for label, _ in rows)
    return [
        indent + term.paint(str(label).ljust(pad), "dim") + "  " + str(value)
        for label, value in rows
    ]
