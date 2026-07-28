"""Turning a Config into EC register writes."""

from . import config as cfg

PROFILE_LABELS = {
    cfg.PROFILE_AUTO: "Auto",
    cfg.PROFILE_BASIC: "Basic",
    cfg.PROFILE_ADVANCED: "Advanced",
}

PROFILE_DESCRIPTIONS = {
    cfg.PROFILE_AUTO: "Hand fan control back to the firmware curve.",
    cfg.PROFILE_BASIC: "The auto curve shifted up or down by a fixed amount.",
    cfg.PROFILE_ADVANCED: "Your own curve, set point by point.",
}


def curve_for(config, profile=None):
    """Return the (cpu, gpu) fan curve a profile resolves to, as percentages.

    Nothing here mutates `config`.  The old code applied the Basic offset by
    modifying the stored list in place, so switching to Basic twice applied
    the offset twice.
    """
    profile = profile or config.profile
    if profile == cfg.PROFILE_ADVANCED:
        cpu, gpu = config.advanced_cpu, config.advanced_gpu
        offset = 0
    else:
        # Basic is documented as an offset from the auto curve, so that is
        # what it is: the previous build offset an all-zero curve instead,
        # which drove the fans to a flat line near 0%.
        cpu, gpu = config.auto_cpu, config.auto_gpu
        offset = config.basic_offset if profile == cfg.PROFILE_BASIC else 0

    def shift(values):
        return [cfg.clamp(value + offset, cfg.SPEED_MIN, cfg.SPEED_MAX) for value in values]

    return shift(cpu), shift(gpu)


def uses_curve(config, which):
    """Whether the selected profile is driven by the auto or advanced curve.

    Editing a curve the profile does not use is stored but changes nothing on
    the machine, and saying so beats silently doing nothing.
    """
    if config.profile == cfg.PROFILE_ADVANCED:
        return which == "advanced"
    if config.profile == cfg.PROFILE_BASIC:
        return which == "auto"
    return False  # Auto: the firmware runs the fans, not us


def profile_writes(config):
    """The (address, value) pairs that put the EC into the configured profile."""
    hardware = config.hardware
    if config.profile == cfg.PROFILE_AUTO:
        mode = hardware.profile_auto_value
    else:
        mode = hardware.profile_manual_value

    writes = [(hardware.profile_address, mode)]
    cpu, gpu = curve_for(config)
    writes += list(zip(hardware.cpu_fan_speed_address, cpu))
    writes += list(zip(hardware.gpu_fan_speed_address, gpu))
    return writes


def cooler_booster_write(config, enabled):
    hardware = config.hardware
    value = hardware.cooler_booster_on if enabled else hardware.cooler_booster_off
    return (hardware.cooler_booster_address, value)


def battery_threshold_write(config, threshold):
    """Battery threshold is stored with bit 7 set, hence the +128."""
    threshold = cfg.clamp(int(threshold), cfg.BATTERY_MIN, cfg.BATTERY_MAX)
    return (config.hardware.battery_threshold_address, threshold + 128)


def apply_profile(controller, config):
    """Write the profile, its curve, and the cooler booster state to the EC."""
    writes = profile_writes(config)
    writes.append(cooler_booster_write(config, config.cooler_booster))
    controller.write_many(writes)


def apply_cooler_booster(controller, config, enabled):
    controller.write_many([cooler_booster_write(config, enabled)])


def apply_battery_threshold(controller, config, threshold):
    controller.write_many([battery_threshold_write(config, threshold)])


def apply_all(controller, config):
    """Everything the config describes, in one pass — used by `apply`."""
    writes = profile_writes(config)
    writes.append(cooler_booster_write(config, config.cooler_booster))
    writes.append(battery_threshold_write(config, config.battery_threshold))
    controller.write_many(writes)


def read_auto_curve(controller, config):
    """Read whatever curve the EC currently holds, for 'import from firmware'."""
    snapshot = controller.snapshot()
    hardware = config.hardware
    cpu = [snapshot[address] for address in hardware.cpu_fan_speed_address]
    gpu = [snapshot[address] for address in hardware.gpu_fan_speed_address]
    return cpu, gpu


def active_profile(controller, config):
    """What the EC itself currently reports, as (profile, cooler_booster).

    The profile register only distinguishes auto from manual, so a manual
    reading is reported as whichever manual profile the config has selected.
    """
    snapshot = controller.snapshot()
    hardware = config.hardware
    mode = snapshot[hardware.profile_address]
    if mode == hardware.profile_auto_value:
        profile = cfg.PROFILE_AUTO
    elif mode == hardware.profile_manual_value:
        profile = (
            config.profile
            if config.profile != cfg.PROFILE_AUTO
            else cfg.PROFILE_ADVANCED
        )
    else:
        profile = None
    booster = snapshot[hardware.cooler_booster_address] == hardware.cooler_booster_on
    return profile, booster
