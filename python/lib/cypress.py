
import usb.core
import usb.util
from array import array
from random import randint
import struct

class CypressError(Exception):
	 """Base class for other exceptions"""
	 pass 

class CypressWriteRequestError(CypressError):
	 """Raised if an USB write error occours"""
	 pass

class CypressReadResponseError(CypressError):
	 """Raised if an USB read error occours"""
	 pass

class CypressOpcError(CypressError):
	 """Raised for wrong operation code"""
	 pass

class CypressSeqError(CypressError):
	 """Raised for response wrong sequence number"""
	 pass

class Cypress():

	def __init__(self):
		self.opc_rd = 0x20
		self.opc_wr = 0x10
		self.ep_rd = None
		self.ep_wr = None
		self.ep_data = None
		self.dev = None
		self.cfg = None
		self.intf = None

	def open(self):
			try:
				self.dev = usb.core.find(idVendor=0x04b4, idProduct=0x8613)
			except Exception as e:
				print("ERROR: Cypress device not found")
				sys.exit(1)

	def config(self):
		self.cfg = self.dev.get_active_configuration()
		self.intf = self.cfg[(0,1)]
		self.dev.set_interface_altsetting(self.intf)

		if self.dev.is_kernel_driver_active(0) is True:
			self.dev.detach_kernel_driver(0)

		self.ep_rd = usb.util.find_descriptor(self.intf, bEndpointAddress=0x86)
		self.ep_wr = usb.util.find_descriptor(self.intf, bEndpointAddress=0x02)
		self.ep_data = usb.util.find_descriptor(self.intf, bEndpointAddress=0x88)

		assert self.ep_rd is not None
		assert self.ep_wr is not None
		assert self.ep_data is not None


	def busclear(self):
		while True:
			try:
				data = self.ep_rd.read(1)
			except usb.core.USBError as e:
				break

	def getdata(self):
		data = self.dev.read(self.ep_data, 1024, timeout=100)
		return data

	def readmem(self, addr):
		wrbuf = array('B')
		wrbuf.append(self.opc_rd)
		seq = randint(1,15)
		wrbuf.append(seq)
		wrbuf.append((addr & 0xFF00) >> 8)
		wrbuf.append(addr & 0x00FF)

		wrbuf[0], wrbuf[1] = wrbuf[1], wrbuf[0]
		wrbuf[2], wrbuf[3] = wrbuf[3], wrbuf[2]

		# write request
		try:
			self.ep_wr.write(wrbuf.tostring(), 100)
		except usb.core.USBError as e:
			print(e)
			raise CypressWriteRequestError("Cypress error sending READ(addr) request")

		# read response
		try:
			rdbuf = self.ep_rd.read(4)
		except:
			raise CypressReadResponseError("Cypress error receiving READ(addr) response")

		rdbuf[0], rdbuf[1] = rdbuf[1], rdbuf[0]
		rdbuf[2], rdbuf[3] = rdbuf[3], rdbuf[2]

		if(rdbuf[0] != self.opc_rd):
			raise CypressOpcError("Cypress op code error in WRITE(addr,val) response")

		if(rdbuf[1] != seq):
			raise CypressSeqError("Cypress seq number error in WRITE(addr,val) response")

		value = rdbuf[3] + (rdbuf[2] << 8)

		return(value)

	def writemem(self, addr, value):
		wrbuf = array('B')
		wrbuf.append(self.opc_wr)
		seq = randint(1,15)
		wrbuf.append(seq)
		wrbuf.append((addr & 0xFF00) >> 8)
		wrbuf.append(addr & 0x00FF)
		wrbuf.append((value & 0xFF00) >> 8)
		wrbuf.append(value & 0x00FF)

		wrbuf[0], wrbuf[1] = wrbuf[1], wrbuf[0]
		wrbuf[2], wrbuf[3] = wrbuf[3], wrbuf[2]
		wrbuf[4], wrbuf[5] = wrbuf[5], wrbuf[4]

		# write request
		try:
			self.ep_wr.write(wrbuf.tostring())
		except usb.core.USBError as e:
			raise CypressWriteRequestError("Cypress error sending WRITE(addr,val) request")

		# read response 
		try:
			rdbuf = self.ep_rd.read(4)
		except:
			raise CypressReadResponseError("Cypress error receiving WRITE(addr,val) response")

		rdbuf[0], rdbuf[1] = rdbuf[1], rdbuf[0]

		if(rdbuf[0] != self.opc_wr):
			raise CypressOpcError("Cypress op code error in WRITE(addr,val) response")

		if(rdbuf[1] != seq):
			raise CypressSeqError("Cypress seq number error in WRITE(addr,val) response")

