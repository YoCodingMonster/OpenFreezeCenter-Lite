"""Sensor polling and history.

One EC snapshot per tick feeds every reading, and a bounded history buffer
backs the sparklines.  The GUI does this on a GLib timer; here it is a plain
generator the caller drives, so nothing outside the standard library is
needed and Ctrl-C lands where you would expect it.
"""

import time
from collections import deque

from .ec import u16, rpm_from_period

HISTORY_SECONDS = 60


class Reading(object):
    """One poll: temperatures in degrees C, fan speeds in RPM."""

    __slots__ = ("cpu_temp", "gpu_temp", "cpu_rpm", "gpu_rpm", "timestamp")

    def __init__(self, cpu_temp, gpu_temp, cpu_rpm, gpu_rpm, timestamp=None):
        self.cpu_temp = cpu_temp
        self.gpu_temp = gpu_temp
        self.cpu_rpm = cpu_rpm
        self.gpu_rpm = gpu_rpm
        self.timestamp = time.time() if timestamp is None else timestamp

    def to_dict(self):
        return {
            "time": self.timestamp,
            "cpu_temp": self.cpu_temp,
            "gpu_temp": self.gpu_temp,
            "cpu_rpm": self.cpu_rpm,
            "gpu_rpm": self.gpu_rpm,
        }


class Monitor(object):
    """Polls the EC, keeping a rolling history and the extremes seen so far."""

    def __init__(self, controller, config, interval=0.5):
        self.controller = controller
        self.config = config
        # A floor, because `--interval 0` would otherwise spin the CPU faster
        # than the EC can answer.
        self.interval = max(0.05, float(interval))

        points = max(2, int(HISTORY_SECONDS / self.interval))
        self.cpu_history = deque(maxlen=points)
        self.gpu_history = deque(maxlen=points)

        # Seeded past any real temperature so the first reading replaces them.
        self.cpu_min = self.gpu_min = 999
        self.cpu_max = self.gpu_max = 0
        self.latest = None

    def reset_extremes(self):
        self.cpu_min = self.gpu_min = 999
        self.cpu_max = self.gpu_max = 0
        if self.latest is not None:
            self._record_extremes(self.latest)

    def _record_extremes(self, reading):
        self.cpu_min = min(self.cpu_min, reading.cpu_temp)
        self.cpu_max = max(self.cpu_max, reading.cpu_temp)
        self.gpu_min = min(self.gpu_min, reading.gpu_temp)
        self.gpu_max = max(self.gpu_max, reading.gpu_temp)

    def sample(self):
        """Take one reading and fold it into the history."""
        hardware = self.config.hardware
        snapshot = self.controller.snapshot()
        reading = Reading(
            cpu_temp=snapshot[hardware.cpu_temp_address],
            gpu_temp=snapshot[hardware.gpu_temp_address],
            cpu_rpm=rpm_from_period(u16(snapshot, hardware.cpu_rpm_address)),
            gpu_rpm=rpm_from_period(u16(snapshot, hardware.gpu_rpm_address)),
        )
        self.latest = reading
        self._record_extremes(reading)
        self.cpu_history.append(reading.cpu_temp)
        self.gpu_history.append(reading.gpu_temp)
        return reading

    def run(self, count=None):
        """Yield readings forever, or `count` of them, one per interval.

        The wait is measured from the start of each tick, so a slow read does
        not make the interval drift.
        """
        taken = 0
        while count is None or taken < count:
            started = time.time()
            yield self.sample()
            taken += 1
            if count is not None and taken >= count:
                return
            remaining = self.interval - (time.time() - started)
            if remaining > 0:
                time.sleep(remaining)
