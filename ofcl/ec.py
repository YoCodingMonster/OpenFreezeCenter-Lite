"""Access to the MSI embedded controller through the ec_sys debugfs interface.

Everything the program knows about the hardware funnels through
`EmbeddedController`.  Reads go through `snapshot()`, which pulls the whole
256 byte EC address space in a single open/read, so one poll costs one file
open however many values are shown.

Older releases of Lite reached the EC through the third-party ECTweaker
package.  This talks to debugfs directly instead: one less thing to install,
one less thing to break, and it works on any kernel that has ec_sys — which
is every kernel this program has ever supported.
"""

import errno
import os
import random
import subprocess

EC_IO_PATH = "/sys/kernel/debug/ec/ec0/io"
DEBUGFS_PATH = "/sys/kernel/debug"
EC_SIZE = 256

# The EC reports fan speed as a period; this is the constant the MSI firmware
# uses to turn that period into RPM.
RPM_CONSTANT = 478000

MODPROBE_HINT = (
    "Load the ec_sys module with write support:\n"
    "    sudo modprobe ec_sys write_support=1\n"
    "Run install.sh once to make that setting persist across reboots."
)


class ECError(Exception):
    """An EC access problem worth showing the user in full."""

    def __init__(self, title, detail, hint=""):
        super(ECError, self).__init__(title)
        self.title = title
        self.detail = detail
        self.hint = hint

    def report(self):
        """The message as it is printed on the terminal."""
        lines = [self.title, "", self.detail]
        if self.hint:
            lines += ["", self.hint]
        return "\n".join(lines)


class ECUnavailable(ECError):
    """The debugfs EC interface is not there at all."""


class ECPermissionDenied(ECError):
    """We are not running with enough privilege to touch the EC."""


class ECWriteUnsupported(ECError):
    """The ec_sys module was loaded without write_support=1."""


def _describe_oserror(exc, path, writing):
    if isinstance(exc, FileNotFoundError):
        return ECUnavailable(
            "Embedded controller not available",
            "%s does not exist, so the fan controller cannot be reached." % path,
            MODPROBE_HINT,
        )
    if isinstance(exc, PermissionError):
        return ECPermissionDenied(
            "Permission denied",
            "%s can only be read and written by root." % path,
            "Start the program with sudo.",
        )
    if writing and exc.errno == errno.EINVAL:  # what ec_sys returns read-only
        return ECWriteUnsupported(
            "Embedded controller is read-only",
            "The ec_sys module was loaded without write support, so fan "
            "profiles cannot be changed.",
            "Add 'options ec_sys write_support=1' to "
            "/etc/modprobe.d/ec_sys.conf and reboot.",
        )
    return ECError("Embedded controller error", str(exc))


class EmbeddedController(object):
    """Reads and writes single EC bytes, plus whole-space snapshots."""

    simulated = False

    def __init__(self, path=EC_IO_PATH):
        self.path = path

    def check(self):
        """Raise an ECError describing why the EC is unusable, or return None."""
        try:
            with open(self.path, "rb") as handle:
                handle.read(1)
        except OSError as exc:
            raise _describe_oserror(exc, self.path, writing=False)
        if not os.access(self.path, os.W_OK):
            raise ECPermissionDenied(
                "Permission denied",
                "%s is not writable by this process." % self.path,
                "Start the program with sudo.",
            )
        return None

    def snapshot(self):
        """Return the whole EC address space as `bytes`."""
        try:
            with open(self.path, "rb") as handle:
                data = handle.read(EC_SIZE)
        except OSError as exc:
            raise _describe_oserror(exc, self.path, writing=False)
        if len(data) < EC_SIZE:
            data = data.ljust(EC_SIZE, b"\x00")
        return data

    def read_u8(self, address):
        return self.snapshot()[address]

    def write_u8(self, address, value):
        self.write_many([(address, value)])

    def write_many(self, pairs):
        """Write several (address, value) pairs through one open file handle."""
        pairs = list(pairs)
        if not pairs:
            return
        try:
            with open(self.path, "r+b") as handle:
                for address, value in pairs:
                    handle.seek(address)
                    handle.write(bytes(bytearray([max(0, min(255, int(value)))])))
        except OSError as exc:
            raise _describe_oserror(exc, self.path, writing=True)


class SimulatedController(EmbeddedController):
    """An in-memory EC, so the program can be tried out without MSI hardware.

    Enabled with --simulate.  Temperatures wander around a baseline and fan
    RPM loosely follows them, which is enough to exercise the readouts.
    """

    simulated = True

    def __init__(self):
        super(SimulatedController, self).__init__(path="<simulated>")
        self._memory = bytearray(EC_SIZE)
        self._temps = [52.0, 46.0]

    def check(self):
        return None

    def snapshot(self):
        for index in range(2):
            self._temps[index] += random.uniform(-3.0, 3.2)
            self._temps[index] = max(35.0, min(94.0, self._temps[index]))
        cpu_temp, gpu_temp = (int(value) for value in self._temps)
        self._memory[0x68] = cpu_temp
        self._memory[0x80] = gpu_temp
        for address, temp in ((0xC8, cpu_temp), (0xCA, gpu_temp)):
            rpm = 1200 + (temp - 35) * 55
            period = int(RPM_CONSTANT / max(rpm, 1))
            self._memory[address] = (period >> 8) & 0xFF
            self._memory[address + 1] = period & 0xFF
        return bytes(self._memory)

    def write_many(self, pairs):
        for address, value in pairs:
            self._memory[address] = max(0, min(255, int(value)))


###############################################################################
# Getting the interface to exist in the first place
###############################################################################


def _run(command):
    """Run a command, discarding its output. True if it exited cleanly."""
    try:
        with open(os.devnull, "wb") as null:
            return subprocess.call(command, stdout=null, stderr=subprocess.STDOUT) == 0
    except OSError:
        return False


def ensure_interface():
    """Try to make `EC_IO_PATH` usable, and report what happened.

    Returns a list of the steps that were taken, so the caller can tell the
    user why the machine suddenly grew a debugfs mount.  Everything here needs
    root; as a normal user it does nothing and the caller's `check()` produces
    the real message.
    """
    steps = []
    if os.access(EC_IO_PATH, os.W_OK):
        return steps
    if os.geteuid() != 0:
        return steps

    if not os.path.ismount(DEBUGFS_PATH) and os.path.isdir(DEBUGFS_PATH):
        if _run(["mount", "-t", "debugfs", "none", DEBUGFS_PATH]):
            steps.append("mounted debugfs on " + DEBUGFS_PATH)

    if not os.path.exists(EC_IO_PATH):
        if _run(["modprobe", "ec_sys", "write_support=1"]):
            steps.append("loaded the ec_sys module with write support")
    elif not os.access(EC_IO_PATH, os.W_OK):
        # Loaded read-only, which is the default. Reloading is the only way to
        # turn write support on without a reboot.
        if _run(["modprobe", "-r", "ec_sys"]) and _run(
            ["modprobe", "ec_sys", "write_support=1"]
        ):
            steps.append("reloaded ec_sys with write support")
    return steps


###############################################################################
# Snapshot helpers
###############################################################################


def u16(snapshot, address):
    """Read a big-endian 16 bit value out of a snapshot."""
    return (snapshot[address] << 8) | snapshot[address + 1]


def rpm_from_period(period):
    """Convert the EC's fan period reading into RPM (0 when the fan is idle)."""
    if period <= 0:
        return 0
    return RPM_CONSTANT // period
