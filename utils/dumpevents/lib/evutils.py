
class EventUtils():

    def __init__(self):
        self.debug = False
        self.samplenum = 1
        self.modulenum = 8

    def SetDebug(self, value):
        self.debug = value

    def SetModuleNum(self, value):
        self.modulenum = value

    def GetModuleNum(self):
        return self.modulenum

    def SetSampleNum(self, value):
        self.samplenum = value

    def GetSampleNum(self):
        return self.samplenum

    def PrintTab(self, ev):
        col = 0
        num = 0
        print('%04d-> ' % num, end='')
        for item in ev:
            num = num + 1
            print('0x%04X' % item, end='')
            col = col + 1
            if(col == 16):
                col = 0
                print('\n')
                print('%04d-> ' % num, end='')
            else:
                print(' ', end='')
        print('\n')

    def PrintCol(self, ev):
        for item in ev:
            print('%X' % item)
        print('\n')

    def UnmaskEC(self, word):
        return (word & 0x0FFF)

    def GetEC(self, ev):
        return (self.UnmaskEC(ev[1]))

    def UnmaskLEN(self, word):
        return (word & 0x0FFF)

    def GetLEN(self, ev):
        return (self.UnmaskLEN(ev[-2]))

    def UnmaskCRC(self, word):
        return (word & 0x00FF)

    def GetCRC(self, ev):
        return (self.UnmaskCRC(ev[-1]))

    def CheckEC(self, ev):
        ec = 0
        i = 1
        readec = self.UnmaskEC(ev[i])
        step = 2 + 32 + (32 * self.samplenum)
        while (i < len(ev)):
            if (self.UnmaskEC(ev[i]) != readec):
                if self.debug:
                    print("Event EC: %X != %X not consistent" % (self.UnmaskEC(ev[i]), readec))
                return False
            i += step
        return True

    def CheckCRC(self, ev):
        evcrc = self.GetCRC(ev)
        crc = 0
        for item in ev[:-1]:
            msb = (item & 0xFF00) >> 8
            lsb = (item & 0x00FF)
            crc = (crc ^ (msb ^ lsb))
        crc8 = crc & 0x00FF
        if self.debug:
            print("Event CRC: %X - Calculated CRC: %X" % (evcrc, crc8))
        return (evcrc == crc8)

    def CheckLength(self, ev):
        evlen = self.GetLEN(ev)
        length = len(ev) + 1
        if self.debug:
            print("Event LEN: %d - Calculated LEN: %d" % (evlen, length))
        return (evlen == length)

    def GetChannelSamples(self, ev, m, ch):
        offset = 4
        start = m*(32+2+(self.samplenum*32)) + ch*(self.samplenum+1) + offset
        end = start + self.samplenum
        return(ev[start:end])

    def GetTime(self, ev):
        msb = ev[-4]
        lsb = ev[-3]
        msb = msb << 16
        lsb = lsb << 1
        time = (msb + lsb) >> 1
        return time
