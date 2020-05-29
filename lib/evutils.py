
class EventUtils():

	def __init__(self):
		self.debug = False

	def SetDebug(self, value):
		self.debug = value

	def PrintTab(self, ev):
		col = 0
		for item in ev:
			print('%X' % item, end='')
			col = col + 1
			if(col == 16):
				col = 0
				print('\n')
			else:
				print(' . ', end='')
		print('\n')

	def PrintCol(self, ev):
		for item in ev:
			print('%X' % item)
		print('\n')

	def EC(self, ev):
		return (ev[1] & 0x0FFF)

	def CheckEC(self, ev):
		ec = 0
		for item in ev:
			if( (item & 0xF000) == 0xC000 ):
				readec = item & 0x0FFF
				if(ec == 0):
					ec = readec
				else:
					if(ec != readec):
						if self.debug:
							print("Event EC: %X != %X not consistent" % (ec, readec))
						return False
		return True

	def CheckCRC(self, ev):
		evcrc = (ev[-1] & 0x00FF)
		crc = 0
		for item in ev[:-1]:
			msb = (item & 0xFF00) >> 8
			lsb = (item & 0x00FF)
			crc = crc ^ msb ^ lsb
		crc8 = crc & 0x00FF
		if self.debug:
			print("Event CRC: %X - Calculated CRC: %X" % (evcrc, crc8))
		return (evcrc == crc8)

	def CheckLength(self, ev):
		evlen = (ev[-2] & 0x0FFF)
		length = len(ev) + 1
		if self.debug:
			print("Event LEN: %d - Calculated LEN: %d" % (evlen, length))
		return (evlen == length)
