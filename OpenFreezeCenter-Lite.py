#! /usr/bin/python3

import os
import time
import ECTweaker as ECT

#   PROFILE                      = 1 or 2 or 3 or 4
#	AUTO_SPEED                   = [[CPU1, CPU2, CPU3, CPU4, CPU5, CPU6, CPU7], [GPU1, GPU2, GPU3, GPU4, GPU5, GPU6, GPU7]]
#	ADV_SPEED                    = [[CPU1, CPU2, CPU3, CPU4, CPU5, CPU6, CPU7], [GPU1, GPU2, GPU3, GPU4, GPU5, GPU6, GPU7]]
#   BASIC_OFFSET                 = Value between -30 to +30
#	CPU                          = 1 if CPU is 11th gen and above || 0 if CPU is 10th gen or below
#	AUTO_ADV_VALUES              = [FAN PROFILE ADDRESS, AUTO VALUE, ADVANCED VALUE]
#	COOLER_BOOSTER_OFF_ON_VALUES = [COOLER BOOSTER ADDRESS, COOLER BOOSTER OFF VALUE, COOLER BOOSTER ON VALUE]
#	CPU_GPU_FAN_SPEED_ADDRESS    = [[CPU1, CPU2, CPU3, CPU4, CPU5, CPU6, CPU7], [GPU1, GPU2, GPU3, GPU4, GPU5, GPU6, GPU7]]
#	CPU_GPU_TEMP_ADDRESS         = [CPU CURRENT TEMP ADDRESS, GPU CURRENT TEMP ADDRESS]
#	CPU_GPU_RPM_ADDRESS          = [CPU FAN RPM ADDRESS, GPU FAN RPM ADDRESS]
#   BATTERY_THRESHOLD_VALUE      = 50 to 100

PATH_TO_CONFIG = str(os.path.realpath(os.path.dirname(__file__))) + "/config.py"
LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'
BASIC_SPEED = [[0, 0, 0, 0, 0, 0, 0],[0, 0, 0, 0, 0, 0, 0]]

##########################
# Writing config.py file #
##########################

def config_writer():
    CONFIG = ""
    CONFIG_FILE = open(PATH_TO_CONFIG, "r")
    CONFIG = CONFIG_FILE.read()
    CONFIG_FILE.close()

    CONFIG = ("PROFILE = " + str(config.PROFILE))
    CONFIG = CONFIG + ("\nAUTO_SPEED = " + str(config.AUTO_SPEED))
    CONFIG = CONFIG + ("\nADV_SPEED = " + str(config.ADV_SPEED))
    CONFIG = CONFIG + ("\nBASIC_OFFSET = " + str(config.BASIC_OFFSET))
    CONFIG = CONFIG + ("\nCPU = " + str(config.CPU))
    CONFIG = CONFIG + ("\nAUTO_ADV_VALUES = " + str(config.AUTO_ADV_VALUES))
    CONFIG = CONFIG + ("\nCOOLER_BOOSTER_OFF_ON_VALUES = " + str(config.COOLER_BOOSTER_OFF_ON_VALUES))
    CONFIG = CONFIG + ("\nCPU_GPU_FAN_SPEED_ADDRESS = " + str(config.CPU_GPU_FAN_SPEED_ADDRESS))
    CONFIG = CONFIG + ("\nCPU_GPU_TEMP_ADDRESS = " + str(config.CPU_GPU_TEMP_ADDRESS))
    CONFIG = CONFIG + ("\nCPU_GPU_RPM_ADDRESS = " + str(config.CPU_GPU_RPM_ADDRESS))
    CONFIG = CONFIG + ("\nBATTERY_THRESHOLD_VALUE = " + str(config.BATTERY_THRESHOLD_VALUE))

    CONFIG_FILE = open(PATH_TO_CONFIG, "w")
    CONFIG_FILE.writelines(CONFIG)
    CONFIG_FILE.close()

#########################################
# chekcing fan speeds are within limits #
#########################################

def speed_checker(SPEEDS, OFFSET):
	for ROW in range(0, 2):
		for COLUMN in range(0, 7):
			SPEEDS[ROW][COLUMN] = 0 if (SPEEDS[ROW][COLUMN] + OFFSET < 0) else 150 if (SPEEDS[ROW][COLUMN] + OFFSET > 150) else SPEEDS[ROW][COLUMN] + OFFSET
	return SPEEDS

#################################
# Select the FAN CURVE profiles #
#################################

def set_fan_mode():
    MODE = int(input("Set Fan Mode\n1 - Auto\n2 - Basic\n3 - Advanced\n4 - Cooler Booster [1 or 2 or 3 or 4] :-> "))
    if MODE == 1:
        config_writer(PROFILE = 1)
        ECT.fan_profile(0, [[config.AUTO_ADV_VALUES[0], config.AUTO_ADV_VALUES[1]], [config.COOLER_BOOSTER_OFF_ON_VALUES[0], config.COOLER_BOOSTER_OFF_ON_VALUES[1]]], config.CPU_GPU_FAN_SPEED_ADDRESS, speed_checker(config.AUTO_SPEED, 0))
    elif MODE == 2:
        config_writer(PROFILE = 2)
        ECT.fan_profile(0, [[config.AUTO_ADV_VALUES[0], config.AUTO_ADV_VALUES[2]], [config.COOLER_BOOSTER_OFF_ON_VALUES[0], config.COOLER_BOOSTER_OFF_ON_VALUES[1]]], config.CPU_GPU_FAN_SPEED_ADDRESS, speed_checker(BASIC_SPEED, 30 if (config.BASIC_OFFSET > 30) else -30 if (config.BASIC_OFFSET < -30) else config.BASIC_OFFSET))
    elif MODE == 3:
        config_writer(PROFILE = 3)
        ECT.fan_profile(0, [[config.AUTO_ADV_VALUES[0], config.AUTO_ADV_VALUES[2]], [config.COOLER_BOOSTER_OFF_ON_VALUES[0], config.COOLER_BOOSTER_OFF_ON_VALUES[1]]], config.CPU_GPU_FAN_SPEED_ADDRESS, speed_checker(config.ADV_SPEED, 0))
    elif MODE == 4:
        config_writer(PROFILE = 4)
        ECT.fan_profile(1, [config.COOLER_BOOSTER_OFF_ON_VALUES[0], config.COOLER_BOOSTER_OFF_ON_VALUES[2]])
    else: set_fan_mode(4)

#########################################
# Select the battery charging threshold #
#########################################

def bct():
    config.BATTERY_THRESHOLD_VALUE = int(input("YOU WILL NEED TO RESTART LAPTOP FOR THIS TO TAKE EFFECT\nInput the upper charge limit for battery charging (50 to 80 is ideal for battery life)(100 for max battery):-> "))
    if config.BATTERY_THRESHOLD_VALUE >= 50 or config.BATTERY_THRESHOLD_VALUE <= 100:
        ECT.write(0xe4, (128 + config.BATTERY_THRESHOLD_VALUE))
    else:
        bct()
        
######################################################
# Monitor the CPU and GPU fan RPM's and Temperatures #
######################################################

def monitoring():
    try:
        while True:
            CPU_TEMP = ECT.read(config.CPU_GPU_TEMP_ADDRESS[0], 1)
            CPU_FAN_RPM = ECT.read(config.CPU_GPU_RPM_ADDRESS[0], 2)
            GPU_TEMP = ECT.read(config.CPU_GPU_TEMP_ADDRESS[1], 1)
            GPU_FAN_RPM = ECT.read(config.CPU_GPU_RPM_ADDRESS[1], 2)
            if CPU_FAN_RPM != 0: CPU_FAN_RPM = 478000//CPU_FAN_RPM
            if GPU_FAN_RPM != 0: GPU_FAN_RPM = 478000//GPU_FAN_RPM
            print(LINE_CLEAR, LINE_UP, LINE_CLEAR, LINE_UP, LINE_CLEAR, LINE_UP, LINE_CLEAR, LINE_UP, LINE_CLEAR, LINE_UP)
            print("CPU Temperature -> ", CPU_TEMP, "C\nCPU Fan RPM -> ", CPU_FAN_RPM, "\nGPU Temperature -> ", GPU_TEMP, "C\nGPU Fan RPM -> ", GPU_FAN_RPM)
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
        
#####################################################
# Function called to chose what this script will do #
#####################################################

def function():
    FUNC = int(input("1 -> Set Fan Profile\n2 -> Battery charge threshold\n3 -> Monitorting\nChoise -> "))
    if FUNC == 1:
        set_fan_mode()
    elif FUNC == 2:
        bct()
    elif FUNC == 3:
        monitoring()
    else:
        function()

##########################################
# Function called to set the CONFIG FILE #
##########################################

def global_var_check(CHOICE, LINE_YES, LINE_NO):
    INPUT = input(CHOICE)
    if INPUT == 'y' or INPUT == 'Y': LINE = LINE_YES
    elif INPUT == 'n' or INPUT == 'N': LINE = LINE_NO
    else: global_var_check(CHOICE, LINE_YES, LINE_NO)
    return LINE

CHECK = ECT.check()
if CHECK != 1:
    try:
        CONFIG_FILE = open(PATH_TO_CONFIG, "r")
    except FileNotFoundError:
        CONFIG = []
        CHOICE = "\nIf you want universal auto fan profile whihc is as below then [SELECT YES]\n\tAUTO SPEEDS = [[0, 40, 48, 56, 64, 72, 80], [0, 48, 56, 64, 72, 79, 86]]\n\nIf you want to fetch vendor specified auto fan profile which will require you to \n\t1 :- Close this(Before closing read all the steps)\n\t2 :- boot into windows\n\t3 :- set the fan profile to auto\n\t4 :- boot back to linux and then [SELECT NO]"
        LINE_YES = "PROFILE = 1\nAUTO_SPEED = [[0, 40, 48, 56, 64, 72, 80], [0, 48, 56, 64, 72, 79, 86]]"
        LINE_NO = "PROFILE = 1\nAUTO_SPEED = [["+str(ECT.read(0x72, 1))+", "+str(ECT.read(0x73, 1))+", "+str(ECT.read(0x74, 1))+", "+str(ECT.read(0x75, 1))+", "+str(ECT.read(0x76, 1))+", "+str(ECT.read(0x77, 1))+", "+str(ECT.read(0x78, 1))+"], ["+str(ECT.read(0x8a, 1))+", "+str(ECT.read(0x8b, 1))+", "+str(ECT.read(0x8c, 1))+", "+str(ECT.read(0x8d, 1))+", "+str(ECT.read(0x8e, 1))+", "+str(ECT.read(0x8f, 1))+", "+str(ECT.read(0x90, 1))+"]]"
        CONFIG.append(global_var_check(CHOICE, LINE_YES, LINE_NO))
        
        CHOICE = "\nIs your CPU intel 10th Gen and above\n"
        LINE_YES = "\nADV_SPEED =  [[0, 40, 48, 56, 64, 72, 80], [0, 48, 56, 64, 72, 79, 86]] # Edit this list for ADVANCED FAN SPEEDS first the CPU speeds teh GPU speeds\nBASIC_OFFSET = 0 # Edit this for a offset of fan speeds from AUTO SPEEDS from -30 to 30\nCPU = 1\nAUTO_ADV_VALUES = [0xd4, 13, 141]\nCOOLER_BOOSTER_OFF_ON_VALUES = [0x98, 2, 130]\nCPU_GPU_FAN_SPEED_ADDRESS = [[0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78], [0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f, 0x90]]\nCPU_GPU_TEMP_ADDRESS = [0x68, 0x80]\nCPU_GPU_RPM_ADDRESS = [0xc8, 0xca]\nBATTERY_THRESHOLD_VALUE = 100 # Edit this value from between 50 to 100 for the percentage your battery will charge upto"
        LINE_NO =  "\nADV_SPEED =  [[0, 40, 48, 56, 64, 72, 80], [0, 48, 56, 64, 72, 79, 86]] # Edit this list for ADVANCED FAN SPEEDS first the CPU speeds teh GPU speeds\nBASIC_OFFSET = 0 # Edit this for a offset of fan speeds from AUTO SPEEDS from -30 to 30\nCPU = 0\nAUTO_ADV_VALUES = [0xf4, 12, 140]\nCOOLER_BOOSTER_OFF_ON_VALUES = [0x98, 0, 128]\nCPU_GPU_FAN_SPEED_ADDRESS = [[0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78], [0x8a, 0x8b, 0x8c, 0x8d, 0x8e, 0x8f, 0x90]]\nCPU_GPU_TEMP_ADDRESS = [0x68, 0x80]\nCPU_GPU_RPM_ADDRESS = [0xc8, 0xca]\nBATTERY_THRESHOLD_VALUE = 100 # Edit this value from between 50 to 100 for the percentage your battery will charge upto"
        CONFIG.append(global_var_check(CHOICE, LINE_YES, LINE_NO))
        
        CONFIG_FILE = open(PATH_TO_CONFIG, "w")
        CONFIG_FILE.writelines(CONFIG)
        CONFIG_FILE.close()
    finally:
        import config
        function()
else:
    os.system("shutdown -r +1")
    print("Rebooting system within 1 min!\nPlease save all work before it happens!")
