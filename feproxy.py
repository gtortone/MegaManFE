#!/usr/bin/python3 -B

import usb.core
import usb.util
import sys
import signal
import threading
import gevent
from time import sleep
from lib.cypress import Cypress
import zerorpc
import zmq

running = True
cy = Cypress()

def signal_handler(sig, frame):
	global running
	running = False

class RunControlRPC(object):
	def readreg(self, addr):
		return(cy.readmem(addr))

	def writereg(self, addr, val):
		return(cy.writemem(addr, val))

class DaqThread(threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.ctx = zmq.Context()
		self.socket = self.ctx.socket(zmq.PUB)
		self.socket.bind("tcp://0.0.0.0:5000")
	
	def run(self):
		print("Starting ", self.name)
		while(running):
			try:
				chunk = cy.getdata()
			except Exception as e:
				#print(str(e))
				pass
			else: 
				self.socket.send(chunk)
				#print("D " , len(chunk))
				#print(chunk)
				del chunk[:]
		print("Exiting ", self.name)
		self.socket.close()

if __name__ == "__main__":
	print("Megamp frontend - USB proxy")

	cy.open()
	cy.config()
	cy.busclear()

	signal.signal(signal.SIGINT, signal_handler)

	s = zerorpc.Server(RunControlRPC())
	s.bind("tcp://0.0.0.0:4242")
	gevent.spawn(s.run)

	daqt = DaqThread(1, "daqthread")
	daqt.start()

	while(running):
		gevent.sleep(0.5)

	daqt.join()

	print("Bye!")
	sys.exit(0)
