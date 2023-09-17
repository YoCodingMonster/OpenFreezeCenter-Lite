# OpenFreezeCenter-Lite
OpenFreezeCenter-Lite allows users to read/write and control the EC of laptops, specially MSI!

# INSTALLATION
- Install ECTweaker library version 1.3 and above for python from https://pypi.org/project/ECTweaker/ by following instructions on properly setting it up!
- Make sure ```secure boot``` is disabled.
- run the ```OpenFreezeCenter.py``` with sudo.
- DONE!

# How to Use
- If running for the first time, there are 2 outcomes.
  - If the EC read/write is not enabled on your OS, the system will restart.
  - If the EC read/write is enabled on your OS, the system will not restart and run your script.
- Set the ```Fan Profile``` to.
  - Auto
  - Basic ```-20, -10, 0, +10, +20``` to the auto fan speeds
  - Advanced ```Complete manual mode```
    - To adjust the fan speeds this mode just edit the integer (1 to 150) for these lines in code. Dont worry you won't mess it up!
    - ```ADV_SPEED_CPU = [0, 50, 75, 100, 125, 150, 150] # CPU FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST CPU TEMP```
    - ```ADV_SPEED_GPU = [0, 50, 75, 100, 125, 150, 150] # GPU FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST GPU TEMP```
  - Cooler Booster toogle ```Switch between on/off state```

## Issue format
- ISSUE # [CPU] - [LAPTOP MODEL] - [LINUX DISTRO]
  - ```Example``` ISSUE # i7-11800H - MSI GP76 11UG - UBUNTU 23.05

## Feedback
- Please provide suggestions under the Feedback discussion tab!

## Goals
- [X] Fan Control
- [ ] Basic temperature and RPM monitoring
- [ ] Battery Threshold
