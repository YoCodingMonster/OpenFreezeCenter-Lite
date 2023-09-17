# OpenFreezeCenter-Lite
OpenFreezeCenter-Lite allows users to read/write and control the EC of laptops, specially MSI!

# INSTALLATION
- Install ECTweaker library version 1.3 and above for python from https://pypi.org/project/ECTweaker/ by following instructions on properly setting it up!
- Make sure ```secure boot``` is disabled.
- Make Sure that you have ```Auto``` fan profile set on laptop.
  - You can do this by booting up windows an choosing ```Auto``` fan profile and then booting back to linux.
  - This needs to be done just once in your lifetime. But to do this is important.
- run the ```OpenFreezeCenter.py``` with sudo.
- DONE!

# How to Use
- Set the ```Fan Profile``` to.
  - Auto
  - Basic ```-20, -10, 0, +10, +20``` to the auto fan speeds
  - Advanced ```Complete manual mode```
    - To adjust the fan speeds this mode just edit the integer (1 to 150) for these lines in code. Dont worry you won't mess it up!
    - ```ADV_SPEED_CPU = [0, 40, 48, 56, 64, 72, 80] # CPU FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST CPU TEMP```
    - ```ADV_SPEED_GPU = [0, 48, 56, 64, 72, 79, 86] # GPU FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST GPU TEMP```

  - Cooler Booster toogle ```Switch between on/off state```

## Issue format
- ISSUE # [CPU] - [LAPTOP MODEL] - [LINUX DISTRO]
  - ```Example``` ISSUE # i7-11800H - MSI GP76 11UG - UBUNTU 23.05

## Feedback
- Please provide suggestions under the Feedback discussion tab!

## Goals
- [X] Fan Control
- [ ] Remove dependency on Windows to fetch vendor ```Auto``` fan curve
- [ ] Basic temperature and RPM monitoring
- [ ] EC Map View
- [ ] Battery Threshold
