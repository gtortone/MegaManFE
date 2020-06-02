
BOR  = 0x0001  # begin of run
SOF  = 0b0010  # start of frontend
SCLR = 0b0100  # register self clear
SCAN = 0b1000  # register to read periodically

regs = [ {'label': "Number of samples per channel",
          'address': 0x1B,
          'flags': BOR | SOF },
         {'label': "Software trigger",
          'address': 0x20,
          'flags': SCLR },
       ]

def GetRegs(flag=None):
    llist = []
    for item in regs:
        if (flag is None or (item['flags'] & flag) > 0):
            llist.append(item)
    return llist

"""
@ start of FE:
    1) read from FPGA all registers with flag SOF
    2) write to ODB

    GetRegs(regs, SOF)
      return a list of {'label': "....", 'address': 0xYZ }

@ begin of run:
    1) read from ODB all registers with flag BOR
    2) write to FPGA

    GetRegs(regs, BOR)
      return a list of {'label': "....", 'address': 0xYZ }
      for item in list: value = odb_get(item['label']) SetRegValue(item['address'], value)

@ time period (e.g. 10 seconds)
    1) read from FPGA all registers with flag SCAN
    2) update to ODB

    GetRegs(regs, SCAN)
      return a list of {'label': "....", 'address': 0xYZ }
      for item in list: value = GetRegValue(item['address']) odb_set(item['label'], value)
"""
