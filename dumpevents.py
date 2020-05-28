#!/usr/bin/env python3

import sys
import struct
import zmq
from array import array

debug = True

def PrintTab(ev):
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

def PrintCol(ev):
    for item in ev:
        print('%X' % item)
    print('\n')

def EC(ev):
	return (ev[1] & 0x0FFF)

def CheckEC(ev):
	ec = 0
	for item in ev:
		if( (item & 0xF000) == 0xC000 ):
			readec = item & 0x0FFF
			if(ec == 0):
				ec = readec
			else:
				if(ec != readec):
					if debug:
						print("Event EC: %X != %X not consistent" % (ec, readec))
					return False
	return True

def CheckCRC(ev):
	evcrc = (ev[-1] & 0x00FF)
	crc = 0
	for item in ev[:-1]:
		msb = (item & 0xFF00) >> 8
		lsb = (item & 0x00FF)
		crc = crc ^ msb ^ lsb
	crc8 = crc & 0x00FF
	if debug:
		print("Event CRC: %X - Calculated CRC: %X" % (evcrc, crc8))
	return (evcrc == crc8)

def CheckLength(ev):
	evlen = (ev[-2] & 0x0FFF)
	length = len(ev) + 1
	if debug:
		print("Event LEN: %d - Calculated LEN: %d" % (evlen, length))
	return (evlen == length)

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.subscribe("")
socket.connect ("tcp://lxconga01.na.infn.it:5000")

chunk8 = array('B')
event_raw = array('H')

while True:
	string = socket.recv()
	count = len(string) // 2
	data16 = struct.unpack('H'*count, string)

	for word in data16:
		if(len(event_raw) > 60000):
			print("E: skip event - length > 60000 words")	
			del event_raw[:]
			continue
		event_raw.append(word)
		if( (word & 0xF000) == 0xF000):      # end of event
			if(len(event_raw) < 3):
				print("E: skip event - length < 3 words")
				del event_raw[:]
				continue
			print("---")
			print("Event Counter: %X" % EC(event_raw))
			PrintTab(event_raw)
			if (not CheckEC(event_raw)):
				print("E: skip event - EC error")
			if (not CheckCRC(event_raw)):
				print("E: skip event - CRC error")
			if (not CheckLength(event_raw)):
				print("E: skip event - LEN error")
			del event_raw[:]
			print("---")
