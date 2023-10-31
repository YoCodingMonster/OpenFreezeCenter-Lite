# OpenFreezeCenter-Lite (OFC-l)
- OpenFreezeCenter-Lite allows users to read/write and control the EC of laptops, specially MSI!
  # OpenFreezeCenter (OFC)
  - Same thing just with GUI
  - https://github.com/YoCodingMonster/OpenFreezeCenter

# INSTALLATION (Only first time)
- Creating virtual environment. the path i will be using is ```/home/pm/Desktop/OFC-l```. Here ```OFC-l``` is the folder with script.
  ```
  python3 -m pip install --user virtualenv
  python3 -m venv /home/pm/Desktop/OFC-l
  cd /home/pm/Desktop/OFC-l
  ```
- Install ```ECTweaker``` library, version 2.3 or above.
  ```
  bin/pip3 install ectweaker
  ```
- Make sure ```secure boot``` is disabled.
- Opening virtual environment. the path i will be using is ```/home/pm/Desktop/OFC-l```. Here ```OFC-l``` is the folder with script.
  ```
  cd /home/pm/Desktop/OFC-l
  sudo nohup bin/python3 OpenFreezeCenter-Lite.py
  ```
- There are 2 outcomes.
  - If the EC read/write is not enabled on your OS, the system will enable it and restart and follow up with the second point.
  - If the EC read/write is enabled on your OS, the script will generate ```config.py``` file, which contains the configuration for fan curves and their addresses.
- DONE!

# UPDATING
- Save your AUTO and ADVANCED speeds and in notepad and delete the old ```config.py``` file and then only try the new script.
- Opening virtual environment. the path i will be using is ```/home/pm/Desktop/OFC-l```. Here ```OFC-l``` is the folder with script.
  ```
  cd /home/pm/Desktop/OFC-l
  bin/pip3 install ectweaker -U
  sudo bin/python3 OpenFreezeCenter-Lite.py
  ```
- After you have run the script and new ```config.py``` file is created, paste the new values in the AUTO_SPEED and ADV_SPEED vales place.

# RUNNING
- Opening virtual environment. the path i will be using is ```/home/pm/Desktop/OFC-l```. Here ```OFC-l``` is the folder with script.
  ```
  cd /home/pm/Desktop/OFC-l
  sudo bin/python3 OpenFreezeCenter-Lite.py
  ```
- Close the terminal and enjoy!!

## Supported Laptop models (tested)
- MSI GP76 11UG

## Supported Linux Distro (tested)
- Ubuntu

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
