#! /usr/bin/python3

import os
import ECTweaker as ECT

AUTO_SPEED = [0,40,48,56,64,72,80,0,48,56,64,72,79,86]
# AUTO_SPEED_CREATED HERE

# CPU_FAN_PROFILE_BYTE             VALUES[0][0]   BYTE ADDRESS              FAN PROFILES BYTE AND VALUES
# CPU_FAN_PROFILE_VALUE_AUTO       VALUES[0][1]   BYTE VALUE
# CPU_FAN_PROFILE_VALUE_ADVANCED   VALUES[0][2]   BYTE VALUE

# CPU_COOLER_BOOSTER_BYTE          VALUES[1][0]   BYTE ADDRESS              COOLER BOOSTER BYTE AND VALUES
# CPU_COOLER_BOOSTER_VALUE         VALUES[1][1]   BYTE VALUE [off]
# CPU_COOLER_BOOSTER_VALUE         VALUES[1][2]   BYTE VALUE [on]

# CPU_FAN_SPEED_1_BYTE             VALUES[2][0]   BYTE ADDRESS              CPU FAN SPEEDS ADDRESS
# CPU_FAN_SPEED_2_BYTE             VALUES[2][1]   BYTE ADDRESS
# CPU_FAN_SPEED_3_BYTE             VALUES[2][2]   BYTE ADDRESS
# CPU_FAN_SPEED_4_BYTE             VALUES[2][3]   BYTE ADDRESS
# CPU_FAN_SPEED_5_BYTE             VALUES[2][4]   BYTE ADDRESS
# CPU_FAN_SPEED_6_BYTE             VALUES[2][5]   BYTE ADDRESS
# CPU_FAN_SPEED_7_BYTE             VALUES[2][6]   BYTE ADDRESS

# GPU_FAN_SPEED_1_BYTE             VALUES[3][0]   BYTE ADDRESS              GPU FAN SPEEDS ADDRESS
# GPU_FAN_SPEED_2_BYTE             VALUES[3][1]   BYTE ADDRESS
# GPU_FAN_SPEED_3_BYTE             VALUES[3][2]   BYTE ADDRESS
# GPU_FAN_SPEED_4_BYTE             VALUES[3][3]   BYTE ADDRESS
# GPU_FAN_SPEED_5_BYTE             VALUES[3][4]   BYTE ADDRESS
# GPU_FAN_SPEED_6_BYTE             VALUES[3][5]   BYTE ADDRESS
# GPU_FAN_SPEED_7_BYTE             VALUES[3][6]   BYTE ADDRESS

# AUTO_FAN_SPEEDS_VENDOR_VALUES    VALUES[4][]    BYTE ADDRESS              AUTO FAN SPEEDS

# CPU_CURRENT_TEMPERATURE_BYTE     VALUES[5][0]   BYTE ADDRESS              CPU CURRENT TEMPERATURE ADDRESS

VALUES = []

# Select the FAN CURVE profiles

def cpu_gen():
    CPU_GEN = input("is your CPU Intel 10th gen and above [y/n] :-> ")
    if CPU_GEN == 'y' or CPU_GEN == 'Y':
        CPU_GEN = "NEW"
    elif CPU_GEN == 'n' or CPU_GEN == 'N':
        CPU_GEN = "OLD"
    else:
        cpu_gen()
    
    if CPU_GEN == "NEW":
        VALUES = [[0xd4, 13, 141],
                  [0x98, 2, 130],
                  [0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78],
                  [0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f, 0x90],
                  AUTO_SPEED]
    else:
        VALUES = [[0xf4, 12, 140],
                  [0x98, 0, 128],
                  [0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78],
                  [0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f, 0x90],
                  AUTO_SPEED]
    return VALUES

def set_fan_mode():
    VALUES = cpu_gen()
    MODE = int(input("Set Fan Mode\n1 - Auto\n2 - Basic\n3 - Advanced\n4 - Cooler Booster [1 or 2 or 3 or 4] :-> "))

    if MODE == 1:
        ECT.fan_profile("auto", VALUES)

    elif MODE == 2:
        OFFSET = int(input("Select one option for fan speed\n1 - Slower\n2 - Slow\n3 - Normal\n4 - Fast\n5 - Faster [1 or 2 or 3 or 4 or 5] :-> "))
        while OFFSET > 0 and OFFSET < 6:
            for i in range(len(AUTO_SPEED)):
                AUTO_SPEED[i] += (OFFSET * 10) - 30
                if AUTO_SPEED[i] < 0:
                    AUTO_SPEED[i] = 0
                if AUTO_SPEED[i] > 150:
                    AUTO_SPEED[i] = 150
            ECT.fan_profile("advanced", VALUES)
            break
        else:
            OFFSET = int(input("Select one option for fan speed\n1 - Slower\n2 - Slow\n3 - Normal\n4 - Fast\n5 - Faster [1 or 2 or 3 or 4 or 5] :-> "))

    elif MODE == 3:
        ADV_SPEED_CPU = [0, 50, 75, 100, 125, 150, 150] # CPU FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST CPU TEMP
        ADV_SPEED_GPU = [0, 50, 75, 100, 125, 150, 150] # GPU FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST GPU TEMP
        VALUES[4] = ADV_SPEED_CPU + ADV_SPEED_GPU
        ECT.fan_profile("advanced", VALUES)

    elif MODE == 4:

        ECT.fan_profile("cooler booster", VALUES)
        print("Cooler Booster - ", "ON" if ECT.read(VALUES[1][0], 1) == VALUES[1][2] else "OFF")

    else:
        set_fan_mode()

# Function called to set the AUTO fan curve used by the vendor.

if 'AUTO_SPEED' not in globals():
    AUTO_SPEED_CPU = [ECT.read(VALUES[2][0], 1), ECT.read(VALUES[2][1], 1), ECT.read(VALUES[2][2], 1), ECT.read(VALUES[2][3], 1), ECT.read(VALUES[2][4], 1), ECT.read(VALUES[2][5], 1), ECT.read(VALUES[2][6], 1)] # CPU FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST CPU TEMP
    AUTO_SPEED_GPU = [ECT.read(VALUES[3][0], 1), ECT.read(VALUES[3][1], 1), ECT.read(VALUES[3][2], 1), ECT.read(VALUES[3][3], 1), ECT.read(VALUES[3][4], 1), ECT.read(VALUES[3][5], 1), ECT.read(VALUES[3][0], 1)] # GPU FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST GPU TEMP
    AUTO_SPEED = AUTO_SPEED_CPU + AUTO_SPEED_GPU

    with open(__file__, 'r') as file:
        SCRIPT = file.read().split('\n')

    with open(__file__,'w') as file:
        NEW_SCRIPT = []
        for LINE in SCRIPT:
            if LINE == "# AUTO SPEEDS HERE":
                LINE = "AUTO_SPEED = ["+str(AUTO_SPEED[0])+","+str(AUTO_SPEED[1])+","+str(AUTO_SPEED[2])+","+str(AUTO_SPEED[3])+","+str(AUTO_SPEED[4])+","+str(AUTO_SPEED[5])+","+str(AUTO_SPEED[6])+","+str(AUTO_SPEED[7])+","+str(AUTO_SPEED[8])+","+str(AUTO_SPEED[9])+","+str(AUTO_SPEED[10])+","+str(AUTO_SPEED[11])+","+str(AUTO_SPEED[12])+","+str(AUTO_SPEED[13])+"]"
                NEW_SCRIPT.append(LINE)
            else:
                NEW_SCRIPT.append(LINE)
        file.write('\n'.join(NEW_SCRIPT))

CHECK = ECT.check()
if CHECK != 1:
    set_fan_mode()
else:
    os.system("shutdown -r +1")
    print("Rebooting system within 1 min!\nPlease save all work before it happens!")
