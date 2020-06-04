
BOR  = 0x0001  # begin of run
SOF  = 0b0010  # start of frontend
SCLR = 0b0100  # register self clear
SCAN = 0b1000  # register to read periodically

BOARD_TREE = "Board/"

regs = [{'label': BOARD_TREE + "DAC offset",
         'address': 0x01,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "ADC frame phase shift delay",
         'address': 0x02,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "ADC data phase shift delay",
         'address': 0x03,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "Time conversion",
         'address': 0x05,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "LMK control register high",
         'address': 0x10,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "LMK control register low",
         'address': 0x11,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "ADC control register high",
         'address': 0x13,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "ADC control register low",
         'address': 0x14,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "Megamp hold delay",
         'address': 0x17,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "Megamp hold start",
         'address': 0x18,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "Megamp mux frequency",
         'address': 0x19,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "Megamp data latency",
         'address': 0x1A,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "Number of samples per channel",
         'address': 0x1B,
         'flags': BOR | SOF },
        {'label': BOARD_TREE + "Frequency meter scale",
         'address': 0x1C,
         'flags': BOR | SOF | SCAN },
        {'label': BOARD_TREE + "Software trigger",
         'address': 0x20,
         'flags': SCLR },
        {'label': BOARD_TREE + "Reset FIFO",
         'address': 0x21,
         'flags': SCLR },
       ]

cmdregs = [{'label': "ADC delay commit",
         'address': 0x04 },
		{'label': "LMK control register commit",
         'address': 0x12 },
        {'label': "ADC register commit",
         'address': 0x15 },
		]

def GetRegAddress(label):
    for item in regs:
        if (item['label'] == label):
            return item['address']
    return None

def GetRegs(flag=None):
    llist = []
    for item in regs:
        if (flag is None or (item['flags'] & flag) > 0):
            llist.append(item)
    return llist

def GetCommitRegs():
	llist = []
	for item in cmdregs:
		llist.append(item)
	return llist

