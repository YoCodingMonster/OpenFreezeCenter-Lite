#!/usr/bin/env bash
#
# Open Freeze Center Lite installer.
#
#   ./install.sh              install (or update) and set up EC access
#   ./install.sh --uninstall  remove everything this script installed
#
# Run it from the directory you unpacked, as your normal user; it asks for
# sudo only for the steps that need it.
#
# There is nothing to compile and nothing to download: the program is plain
# Python with no third-party imports, which is what lets it run on
# distributions far older than the GTK version supports.

set -eu

PREFIX=/opt/openfreezecenter-lite
BIN=/usr/local/bin/openfreezecenter-lite
ALIAS=/usr/local/bin/ofc-lite
SERVICE=/etc/systemd/system/openfreezecenter-lite.service
MODPROBE_CONF=/etc/modprobe.d/ec_sys.conf
MODULES_CONF=/etc/modules-load.d/ec_sys.conf

SOURCE_DIR=$(cd "$(dirname "$0")" && pwd)

say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m==>\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m==>\033[0m %s\n' "$*" >&2; exit 1; }

if [ "$(id -u)" -eq 0 ]; then
    die "Run this as your normal user, not with sudo. It asks for sudo when it needs it."
fi

if ! command -v sudo >/dev/null; then
    die "sudo is not installed. Install it, or copy the steps in this script by hand as root."
fi

###############################################################################
# Uninstall
###############################################################################

if [ "${1:-}" = "--uninstall" ]; then
    say "Removing Open Freeze Center Lite"
    if [ -e "$SERVICE" ]; then
        sudo systemctl disable --now openfreezecenter-lite.service 2>/dev/null || true
    fi
    sudo rm -rf "$PREFIX" "$BIN" "$ALIAS" "$SERVICE"
    sudo rm -f "$MODPROBE_CONF" "$MODULES_CONF"
    command -v systemctl >/dev/null && sudo systemctl daemon-reload 2>/dev/null || true
    say "Removed. Settings in ~/.config/openfreezecenter were left alone."
    exit 0
fi

###############################################################################
# Python
#
# Anything from 3.5 onwards works; the code deliberately avoids f-strings and
# dataclasses so that stays true on old long-term-support releases.
###############################################################################

check_python() {
    command -v python3 >/dev/null || die "python3 is not installed. Install it and re-run."
    python3 - <<'PY' || die "Python 3.5 or newer is required."
import sys
if sys.version_info < (3, 5):
    sys.exit("  found Python %d.%d" % sys.version_info[:2])
print("  Python %d.%d OK" % sys.version_info[:2])
PY
}

###############################################################################
# EC access
###############################################################################

setup_ec() {
    say "Configuring embedded controller access"

    if ! grep -qs '^options ec_sys write_support=1' "$MODPROBE_CONF"; then
        echo 'options ec_sys write_support=1' | sudo tee "$MODPROBE_CONF" >/dev/null
        say "  wrote $MODPROBE_CONF"
    fi

    # modules-load.d is a systemd thing; /etc/modules is what sysvinit reads.
    if [ -d /etc/modules-load.d ]; then
        if ! grep -qs '^ec_sys$' "$MODULES_CONF"; then
            echo 'ec_sys' | sudo tee "$MODULES_CONF" >/dev/null
            say "  wrote $MODULES_CONF"
        fi
    elif [ -f /etc/modules ]; then
        if ! grep -qs '^ec_sys$' /etc/modules; then
            echo 'ec_sys' | sudo tee -a /etc/modules >/dev/null
            say "  added ec_sys to /etc/modules"
        fi
    fi

    # debugfs is mounted by default on modern systemd, and not at all on some
    # older or minimal systems.
    if ! mount | grep -qs 'on /sys/kernel/debug '; then
        sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null || true
        if ! grep -qs '^debugfs' /etc/fstab; then
            echo 'debugfs /sys/kernel/debug debugfs defaults 0 0' | sudo tee -a /etc/fstab >/dev/null
            say "  added debugfs to /etc/fstab"
        fi
    fi

    # Load it now, so there is no reboot between installing and using it. If it
    # is already loaded read-only, reload it with write support.
    if sudo test -e /sys/kernel/debug/ec/ec0/io && ! sudo test -w /sys/kernel/debug/ec/ec0/io; then
        sudo modprobe -r ec_sys 2>/dev/null || true
    fi
    if sudo modprobe ec_sys write_support=1 2>/dev/null; then
        say "  ec_sys loaded with write support"
    else
        warn "  could not load ec_sys now; it will load on the next boot"
    fi

    if sudo test -w /sys/kernel/debug/ec/ec0/io; then
        say "  EC read/write confirmed"
    else
        warn "  EC not writable yet — disable Secure Boot, reboot, then try again"
    fi
}

###############################################################################
# Install
###############################################################################

install_files() {
    say "Installing to $PREFIX"
    if [ ! -f "$SOURCE_DIR/OpenFreezeCenter-Lite.py" ] || [ ! -d "$SOURCE_DIR/ofcl" ]; then
        die "Run this script from the folder containing OpenFreezeCenter-Lite.py and ofcl/"
    fi

    sudo rm -rf "$PREFIX"
    sudo install -d "$PREFIX"
    sudo cp -r "$SOURCE_DIR/OpenFreezeCenter-Lite.py" "$SOURCE_DIR/ofcl" "$PREFIX/"
    sudo find "$PREFIX" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    sudo chmod +x "$PREFIX/OpenFreezeCenter-Lite.py"

    # The launcher elevates itself, because the EC is root-only — but not for
    # the commands that never touch it, so `--help` and `--simulate` do not
    # ask for a password.
    sudo tee "$BIN" >/dev/null <<'LAUNCHER'
#!/bin/sh
# Open Freeze Center Lite launcher: elevates only when it has to.
APP=/opt/openfreezecenter-lite/OpenFreezeCenter-Lite.py

if [ "$(id -u)" -eq 0 ]; then
    exec python3 "$APP" "$@"
fi

for arg in "$@"; do
    case "$arg" in
        --simulate|--help|-h|--version|config)
            exec python3 "$APP" "$@"
            ;;
    esac
done

exec sudo -- python3 "$APP" "$@"
LAUNCHER
    sudo chmod +x "$BIN"
    sudo ln -sf "$BIN" "$ALIAS"

    # Optional: re-apply the saved profile at boot, since the EC forgets it.
    # SUDO_USER is how the program finds the settings of a real person when it
    # is started by the system rather than by you.
    if command -v systemctl >/dev/null; then
        sudo tee "$SERVICE" >/dev/null <<SERVICE_FILE
[Unit]
Description=Apply Open Freeze Center Lite fan profile
After=multi-user.target

[Service]
Type=oneshot
Environment=SUDO_USER=$(id -un)
ExecStart=$BIN apply
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICE_FILE
        sudo systemctl daemon-reload 2>/dev/null || true
    fi
}

###############################################################################

check_python
setup_ec
install_files

say "Done."
cat <<NEXT

  Run it with:
      openfreezecenter-lite            (or: ofc-lite)

  A few things it can do without the menu:
      openfreezecenter-lite status
      openfreezecenter-lite profile advanced
      openfreezecenter-lite monitor
      openfreezecenter-lite battery 80

  To try it out without touching the hardware:
      openfreezecenter-lite --simulate

  Settings live in ~/.config/openfreezecenter/config.json
NEXT

if [ -e "$SERVICE" ]; then
cat <<NEXT
  To re-apply your profile automatically on every boot:
      sudo systemctl enable openfreezecenter-lite.service
NEXT
fi
