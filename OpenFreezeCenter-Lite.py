#!/usr/bin/env python3
"""Open Freeze Center Lite launcher.

    sudo ./OpenFreezeCenter-Lite.py            interactive menu
    sudo ./OpenFreezeCenter-Lite.py status     one command, then exit
    ./OpenFreezeCenter-Lite.py --simulate      no hardware needed
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ofcl.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
