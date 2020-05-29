#!/usr/bin/env python3

import sys
import struct
import zmq
from array import array
import lib.evutils

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.subscribe("")
socket.connect ("tcp://lxconga01.na.infn.it:5000")

eu = lib.evutils.EventUtils()
eu.SetDebug(True)

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
			print("Event Counter: %X" % eu.EC(event_raw))
			eu.PrintTab(event_raw)
			if (not eu.CheckEC(event_raw)):
				print("E: skip event - EC error")
			if (not eu.CheckCRC(event_raw)):
				print("E: skip event - CRC error")
			if (not eu.CheckLength(event_raw)):
				print("E: skip event - LEN error")
			del event_raw[:]
			print("---")
