# OpenFreezeCenter-Lite
OpenFreezeCenter-Lite allows users to read/write and control the EC of laptops, specially MSI!

# INSTALLATION
- Install ECTweaker library version 2 and above for python from https://pypi.org/project/ECTweaker/ by following instructions on properly setting it up!
- Make sure ```secure boot``` is disabled.
- run the ```OpenFreezeCenter.py``` with sudo like ```sudo python3 OpenFreezeCenter.py```
- DONE!

# How to Use
- If running for the first time, there are 2 outcomes.
  - If the EC read/write is not enabled on your OS, the system will restart.
  - If the EC read/write is enabled on your OS, the system will not restart and run your script. If running for the first time, will generate ```config.py``` file, which contains the configuration for fan curves and tehir address.
- Set the ```Fan Profile``` to.
  - Auto
  - Advanced ```Complete manual mode```
    - To adjust the fan speeds this mode just edit the integer (1 to 150) for these lines in file ```config.py```. Dont worry you won't mess it up!
    - ```[0, 50, 75, 100, 125, 150, 150, 0, 50, 75, 100, 125, 150, 150]]``` - Example Fan curve
    - ```FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST TEMP```
    - ```First 7 are CPU speeds, Last 7 are GPU speeds```
  - Cooler Booster toogle ```Switch between on/off state```. When toogled off will return back to the profile which was set before it.

## Issue format
- ISSUE # [CPU] - [LAPTOP MODEL] - [LINUX DISTRO]
  - ```Example``` ISSUE # i7-11800H - MSI GP76 11UG - UBUNTU 23.05

## Feedback
- Please provide suggestions under the Feedback discussion tab!

## Goals
- [X] Fan Control
- [ ] Basic temperature and RPM monitoring
- [ ] Battery Threshold
- [ ] Webcam control
