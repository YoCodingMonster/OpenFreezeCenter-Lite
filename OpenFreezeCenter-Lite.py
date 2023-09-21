#! /usr/bin/python3

import os
import ECTweaker_test as ECT

# CPU_FAN_PROFILE_BYTE                  VALUES[0][0]   BYTE ADDRESS              FAN PROFILES BYTE AND VALUES
# CPU_FAN_PROFILE_VALUE_AUTO            VALUES[0][1]   VALUE
# CPU_FAN_PROFILE_VALUE_ADVANCED        VALUES[0][2]   VALUE

# CPU_COOLER_BOOSTER_BYTE               VALUES[1][0]   BYTE ADDRESS              COOLER BOOSTER BYTE AND VALUES
# CPU_COOLER_BOOSTER_VALUE              VALUES[1][1]   VALUE [off]
# CPU_COOLER_BOOSTER_VALUE              VALUES[1][2]   VALUE [on]

# CPU_FAN_SPEED_1_BYTE                  VALUES[2][0]   BYTE ADDRESS              CPU FAN SPEEDS ADDRESS
# CPU_FAN_SPEED_2_BYTE                  VALUES[2][1]   BYTE ADDRESS
# CPU_FAN_SPEED_3_BYTE                  VALUES[2][2]   BYTE ADDRESS
# CPU_FAN_SPEED_4_BYTE                  VALUES[2][3]   BYTE ADDRESS
# CPU_FAN_SPEED_5_BYTE                  VALUES[2][4]   BYTE ADDRESS
# CPU_FAN_SPEED_6_BYTE                  VALUES[2][5]   BYTE ADDRESS
# CPU_FAN_SPEED_7_BYTE                  VALUES[2][6]   BYTE ADDRESS

# GPU_FAN_SPEED_1_BYTE                  VALUES[3][0]   BYTE ADDRESS              GPU FAN SPEEDS ADDRESS
# GPU_FAN_SPEED_2_BYTE                  VALUES[3][1]   BYTE ADDRESS
# GPU_FAN_SPEED_3_BYTE                  VALUES[3][2]   BYTE ADDRESS
# GPU_FAN_SPEED_4_BYTE                  VALUES[3][3]   BYTE ADDRESS
# GPU_FAN_SPEED_5_BYTE                  VALUES[3][4]   BYTE ADDRESS
# GPU_FAN_SPEED_6_BYTE                  VALUES[3][5]   BYTE ADDRESS
# GPU_FAN_SPEED_7_BYTE                  VALUES[3][6]   BYTE ADDRESS

# AUTO_FAN_SPEEDS_VENDOR_VALUES         VALUES[4][]    BYTE ADDRESS              AUTO FAN SPEEDS

# ADVANCED_FAN_SPEEDS_VENDOR_VALUES     VALUES[5][]    BYTE ADDRESS              ADVANCED FAN SPEEDS

AUTO_SPEED = []
VALUES = []

# Select the FAN CURVE profiles

def set_fan_mode():
    MODE = int(input("Set Fan Mode\n1 - Auto\n2 - Advanced\n3 - Cooler Booster [1 or 2 or 3] :-> "))

    if MODE == 1: ECT.fan_profile("auto", VALUES)

#    elif MODE == 2 and CPU == 0:
#        OFFSET = int(input("Select one option for fan speed\n1 - Slower\n2 - Slow\n3 - Normal\n4 - Fast\n5 - Faster [1 or 2 or 3 or 4 or 5] :-> "))
#        while OFFSET < 1 and OFFSET > 5:
#            OFFSET = int(input("Select one option for fan speed\n1 - Slower\n2 - Slow\n3 - Normal\n4 - Fast\n5 - Faster [1 or 2 or 3 or 4 or 5] :-> "))
#        BASIC_SPEED = AUTO_SPEED
#        for i in range(len(AUTO_SPEED)):
#            BASIC_SPEED[i] += (OFFSET * 10) - 30
#            if BASIC_SPEED[i] < 0:
#                BASIC_SPEED[i] = 0
#            if BASIC_SPEED[i] > 150:
#                BASIC_SPEED[i] = 150
#        VALUES[4] = BASIC_SPEED
#        ECT.fan_profile("basic", VALUES, CPU)
    
    elif MODE == 2: ECT.fan_profile("advanced", VALUES)

    elif MODE == 3:
        ECT.fan_profile("cooler booster", VALUES)
        print("Cooler Booster - ", "ON" if ECT.read(VALUES[1][0], 1) == VALUES[1][2] else "OFF")
        if ECT.read(VALUES[1][0], 1) == VALUES[1][1]:
            if ECT.read(VALUES[0][0], 1) == VALUES[0][1]:
                print("Back to :-> auto")
                ECT.fan_profile("auto", VALUES)
            if ECT.read(VALUES[0][0], 1) == VALUES[0][2]:
                print("Back to :-> advanced")
                ECT.fan_profile("advanced", VALUES)

    else:
        set_fan_mode()

# Function called to set the CONFIG FILE

def global_var_check(CHOICE, LINE_YES, LINE_NO):
    INPUT = input(CHOICE)
    if INPUT == 'y' or INPUT == 'Y': LINE = LINE_YES
    elif INPUT == 'n' or INPUT == 'N': LINE = LINE_NO
    else: global_var_check(CHOICE, LINE_YES, LINE_NO)
    return LINE

CHECK = ECT.check()
if CHECK != 1:
    try:
        CONFIG_FILE = open("config.py", "r")
    except FileNotFoundError:
        CONFIG = []
        CHOICE = "Select [Y/y] if you want universal auto fan profile without booting into windows\nor\nSelect [N/n] if you want to fetch vendor specified auto fan profile which will require you to \n\tPRIMARY. Close this terminal (Before closing read all the steps)\n\t1. boot into windows\n\t2. set the fan profile to auto\n\t3. boot back to linux and then choose this option here! :-> "
        LINE_YES = "AUTO_SPEED = [0, 40, 48, 56, 64, 72, 80, 0, 48, 56, 64, 72, 79, 86]"
        AUTO_SPEED_CPU = [ECT.read(0x72, 1), ECT.read(0x73, 1), ECT.read(0x74, 1), ECT.read(0x75, 1), ECT.read(0x76, 1), ECT.read(0x77, 1), ECT.read(0x78, 1)] # CPU FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST CPU TEMP
        AUTO_SPEED_GPU = [ECT.read(0x8a, 1), ECT.read(0x8b, 1), ECT.read(0x8c, 1), ECT.read(0x8d, 1), ECT.read(0x8e, 1), ECT.read(0x8f, 1), ECT.read(0x90, 1)] # GPU FAN speed at LOWEST, LOWER, LOW, MEDIUM, HIGH, HIGHER, HIGHEST GPU TEMP
        AUTO_SPEED = AUTO_SPEED_CPU + AUTO_SPEED_GPU
        LINE_NO = "AUTO_SPEED = ["+str(AUTO_SPEED[0])+", "+str(AUTO_SPEED[1])+", "+str(AUTO_SPEED[2])+", "+str(AUTO_SPEED[3])+", "+str(AUTO_SPEED[4])+", "+str(AUTO_SPEED[5])+", "+str(AUTO_SPEED[6])+", "+str(AUTO_SPEED[7])+", "+str(AUTO_SPEED[8])+", "+str(AUTO_SPEED[9])+", "+str(AUTO_SPEED[10])+", "+str(AUTO_SPEED[11])+", "+str(AUTO_SPEED[12])+", "+str(AUTO_SPEED[13])+"]"
        CONFIG.append(global_var_check(CHOICE, LINE_YES, LINE_NO))

        CHOICE = "Is your CPU intel 10th Gen and above [Y/N] :-> "
        LINE_YES = "\nCPU = 1\nVALUES = [[0xd4, 13, 141],\n[0x98, 2, 130],\n[0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78],\n[0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f, 0x90],\nAUTO_SPEED,\n[0, 50, 75, 100, 125, 150, 150, 0, 50, 75, 100, 125, 150, 150]]\t\t# Edit this list for ADVANCED FAN SPEEDS with  refrence [CPU1, CPU2, CPU3, CPU4, CPU5, CPU6, CPU7, GPU1, GPU2, GPU3, GPU4, GPU5, GPU6, GPU7]"
        LINE_NO  = "\nCPU = 0\nVALUES = [[0xf4, 12, 140],\n[0x98, 0, 128],\n[0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78],\n[0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f, 0x90],\nAUTO_SPEED,\n[0, 50, 75, 100, 125, 150, 150, 0, 50, 75, 100, 125, 150, 150]]\t\t# Edit this list for ADVANCED FAN SPEEDS with  refrence [CPU1, CPU2, CPU3, CPU4, CPU5, CPU6, CPU7, GPU1, GPU2, GPU3, GPU4, GPU5, GPU6, GPU7]"
        CONFIG.append(global_var_check(CHOICE, LINE_YES, LINE_NO))

        CONFIG_FILE = open("config.py", "w")
        CONFIG_FILE.writelines(CONFIG)
        CONFIG_FILE.close()
    finally:
        import config
        AUTO_SPEED = config.AUTO_SPEED
        VALUES = config.VALUES
        set_fan_mode()
else:
    os.system("shutdown -r +1")
    print("Rebooting system within 1 min!\nPlease save all work before it happens!")
