#! /usr/bin/python3

import EC_Controller as ECC

def set_fan_mode():
    MODE = input("Set Fan Mode\n1 - Auto\n2 - Basic\n3 - Advanced\n4 - Cooler Booster [1 or 2 or 3 or 4] :-> ")
    if MODE == 1:
        ECC.byte_interpreter("auto")
        auto()
    elif MODE == 2:
        ECC.byte_interpreter("basic")
        basic()
    elif MODE == 3:
        ECC.byte_interpreter("advanced")
        advanced()
    elif MODE == 4:
        ECC.byte_interpreter("cooler booster")
    else:
        set_fan_mode()

def setter(SPEED, OFFSET):
    ECC.byte_interpreter("CPU_FAN_1", SPEED[0] + OFFSET)
    ECC.byte_interpreter("CPU_FAN_2", SPEED[1] + OFFSET)
    ECC.byte_interpreter("CPU_FAN_3", SPEED[2] + OFFSET)
    ECC.byte_interpreter("CPU_FAN_4", SPEED[3] + OFFSET)
    ECC.byte_interpreter("CPU_FAN_5", SPEED[4] + OFFSET)
    ECC.byte_interpreter("CPU_FAN_6", SPEED[5] + OFFSET)
    ECC.byte_interpreter("CPU_FAN_7", SPEED[6] + OFFSET)

    ECC.byte_interpreter("GPU_FAN_1", SPEED[7] + OFFSET)
    ECC.byte_interpreter("GPU_FAN_2", SPEED[8] + OFFSET)
    ECC.byte_interpreter("GPU_FAN_3", SPEED[9] + OFFSET)
    ECC.byte_interpreter("GPU_FAN_4", SPEED[10] + OFFSET)
    ECC.byte_interpreter("GPU_FAN_5", SPEED[11] + OFFSET)
    ECC.byte_interpreter("GPU_FAN_6", SPEED[12] + OFFSET)
    ECC.byte_interpreter("GPU_FAN_7", SPEED[13] + OFFSET)

def auto():
    setter(AUTO_SPEED, 0)

def basic():
    OFFSET = input("Select one option for fan speed\n1 - Slower\n2 - Slow\n3 - Normal\n4 - Fast\n5 - Faster [1 or 2 or 3 or 4 or 5] :-> ")
    if OFFSET > 0 and OFFSET < 6:
        OFFSET = (OFFSET * 10) - 30
        setter(AUTO_SPEED, OFFSET)
    else:
        basic()

def advanced():
    ADV_SPEED = []
    ADV_SPEED.append(00) # CPU FAN speed at LOWEST CPU TEMP
    ADV_SPEED.append(40) # CPU FAN speed at LOWER CPU TEMP
    ADV_SPEED.append(48) # CPU FAN speed at LOW CPU TEMP
    ADV_SPEED.append(56) # CPU FAN speed at MEDIUM CPU TEMP
    ADV_SPEED.append(64) # CPU FAN speed at HIGH CPU TEMP
    ADV_SPEED.append(72) # CPU FAN speed at HIGHER CPU TEMP
    ADV_SPEED.append(80) # CPU FAN speed at HIGHEST CPU TEMP

    ADV_SPEED.append(00) # GPU FAN speed at LOWEST GPU TEMP
    ADV_SPEED.append(48) # GPU FAN speed at LOWER GPU TEMP
    ADV_SPEED.append(56) # GPU FAN speed at LOW GPU TEMP
    ADV_SPEED.append(64) # GPU FAN speed at MEDIUM GPU TEMP
    ADV_SPEED.append(72) # GPU FAN speed at HIGH GPU TEMP
    ADV_SPEED.append(79) # GPU FAN speed at HIGHER GPU TEMP
    ADV_SPEED.append(86) # GPU FAN speed at HIGHEST GPU TEMP
    setter(ADV_SPEED, 0)

# AUTO SPEEDS HERE

if 'AUTO_SPEED' not in globals():
    AUTO_SPEED = []
    AUTO_SPEED.append(str(ECC.read(0x72)))
    AUTO_SPEED.append(str(ECC.read(0x73)))
    AUTO_SPEED.append(str(ECC.read(0x74)))
    AUTO_SPEED.append(str(ECC.read(0x75)))
    AUTO_SPEED.append(str(ECC.read(0x76)))
    AUTO_SPEED.append(str(ECC.read(0x77)))
    AUTO_SPEED.append(str(ECC.read(0x78)))

    AUTO_SPEED.append(str(ECC.read(0x8a)))
    AUTO_SPEED.append(str(ECC.read(0x8b)))
    AUTO_SPEED.append(str(ECC.read(0x8c)))
    AUTO_SPEED.append(str(ECC.read(0x8d)))
    AUTO_SPEED.append(str(ECC.read(0x8e)))
    AUTO_SPEED.append(str(ECC.read(0x8f)))
    AUTO_SPEED.append(str(ECC.read(0x90)))

    with open(__file__, 'r') as file:
        SCRIPT = file.read().split('\n')

    with open(__file__,'w') as file:
        NEW_SCRIPT = []
        for LINE in SCRIPT:
            if LINE != "# AUTO SPEEDS HERE":
                NEW_SCRIPT.append(LINE)
            else:
                LINE = "AUTO_SPEED = ["+AUTO_SPEED[0]+","+AUTO_SPEED[1]+","+ AUTO_SPEED[2]+","+AUTO_SPEED[3]+","+AUTO_SPEED[4]+","+AUTO_SPEED[5]+","+AUTO_SPEED[6]+","+AUTO_SPEED[7]+","+AUTO_SPEED[8]+","+AUTO_SPEED[9]+","+AUTO_SPEED[10]+","+AUTO_SPEED[11]+","+AUTO_SPEED[12]+","+AUTO_SPEED[13]+"]"
                NEW_SCRIPT.append(LINE)
        file.write('\n'.join(NEW_SCRIPT))

set_fan_mode()
