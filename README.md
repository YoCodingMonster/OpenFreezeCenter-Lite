# OpenFreezeCenter-Lite (OFCl)
OpenFreezeCenter-Lite allows users to read/write and control the EC of laptops, specially MSI!

# INSTALLATION
- Install ECTweaker library version 2 and above for python from https://pypi.org/project/ECTweaker/ by following instructions on properly setting it up!
- Make sure ```secure boot``` is disabled.
- run script ```OpenFreezeCenter-Lite.py``` with sudo like ```sudo python3 OpenFreezeCenter-Lite.py```
- There are 2 outcomes.
  - If the EC read/write is not enabled on your OS, the system will enable it and restart. in this run script can show ```read/write``` error and ```FileNotFound``` error, Don't worry, just let the system restart.
  - If the EC read/write is enabled on your OS, the script will generate ```config.py``` file, which contains the configuration for fan curves and their addresses.
- DONE!

# Updating to newer release!
- Just replace the old ```OFC-l.py``` with new ```OFC-l.py``` and you are done.
- If the release notes doe's not say to modify the ```config.py``` then no need to touch that file for updating, if it's mentioned in the release notes, just follow them!

# Functions
- ```set_fan_mode()``` - Set the ```Fan Profile```
  - Auto
  - Advanced ```Complete manual mode```
    - To adjust the fan speeds, just edit the integer (1 to 150) in last lines in file ```config.py```. Dont worry you won't mess it up!
    - ```[0, 50, 75, 100, 125, 150, 150, 0, 50, 75, 100, 125, 150, 150]]``` - Example Fan curve
    - These are FAN speed at ```LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST``` Temperatures.
    - First 7 are CPU speeds, Last 7 are GPU speeds.
  - Cooler Booster toogle ```Switch between on/off state```. When toogled off will return back to the profile which was set before it.
  
- ```monitoring()``` - Displays current CPU and GPU Temperatures and RPM's.
  - Runs in endless loop with 0.5 sec refresh time.
  - To end the monitoring, press any ```key interrupt``` in terminal like ```control + c```

- ```bct()``` - Change the Upper Battery Charge limit from between 50 to 100.

## Supported Laptop models (tested)
- MSI GP76 (11UG)
- MSI GF65
- MSI GF63 THIN (11UC, 11SC)
- MSI Creator Z16HX Studio

## Supported Linux Distro (tested)
- Ubuntu
- Kubuntu
- Fedora Workstation
- Debian

## Issue format
- ISSUE # [CPU] - [LAPTOP MODEL] - [LINUX DISTRO]
  - ```Example``` ISSUE # i7-11800H - MSI GP76 11UG - UBUNTU 23.05

## Feedback
- Please provide suggestions under the Feedback discussion tab!

## Goals
- [X] Fan Control
- [X] Basic temperature and RPM monitoring
- [X] Battery Threshold
- [ ] Webcam control
