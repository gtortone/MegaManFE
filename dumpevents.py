#!/usr/bin/env python3

import sys
import struct
import time
import zmq
import zerorpc
from array import array
import lib.evutils

### params
proxy_host = "lxconga01.na.infn.it"
###

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.subscribe("")
socket.connect("tcp://%s:5000" % proxy_host)

rpcclient = zerorpc.Client()
ep_ctrl = "tcp://%s:4242" % proxy_host
rpcclient.connect(ep_ctrl)

eu = lib.evutils.EventUtils()
eu.SetDebug(True)

# number of samples per channel
snum = rpcclient.readreg(0x1B)
eu.SetSampleNum(snum)

chunk8 = array('B')
event_raw = array('H')

nevents = 0
totevents = 0
ts_prev = time.time()
fevents = 0
printrate = False
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
            totevents += 1
            nevents += 1
            ts_now = time.time()
            ts_diff = ts_now - ts_prev
            if(ts_diff > 5):
                fevents = nevents/ts_diff
                nevents = 0
                ts_prev = ts_now
                printrate = True
            if(len(event_raw) < 3):
                print("E: skip event - length < 3 words")
                del event_raw[:]
                continue
            print("---")
            print("Event Counter: %X" % eu.GetEC(event_raw))
            eu.PrintTab(event_raw)
            if (not eu.CheckEC(event_raw)):
                print("E: skip event - EC error")
            if (not eu.CheckCRC(event_raw)):
                print("E: skip event - CRC error")
            if (not eu.CheckLength(event_raw)):
                print("E: skip event - LEN error")
            print("Timestamp: %d" % eu.GetTime(event_raw))
            print("Number of events: %d" % totevents)
            if(printrate):
                print("Rate of events: %d ev/s" % round(fevents))
                printrate = False
            del event_raw[:]
            print("---")
