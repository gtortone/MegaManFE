# Megamp Manager FrontEnd for MIDAS DAQ

This MIDAS frontend collects events from Megamp Manager board then through MIDAS flow data are stored in MIDAS event files.

Megamp Manager frontend is composed by two parts:

- FrontEnd USB proxy
- Frontend Megamp Manager

## FrontEnd USB proxy (feproxy.py)

FrontEnd USB proxy runs on Congatec board and is composed by:

- RunControl RPC
- Event publisher

### Usage of feproxy.py

To run FrontEnd USB proxy simple launch:
```
./feproxy.py
```
Note: a unique instance of feproxy.py is allowed to run on Congatec board due to exclusive access to USB bus.

### RunControl RPC

RunControl RPC provides a mechanism of Run Control (get/set registers) by Remote Procedure Call mechanism.
RPC is implemented with ZeroRPC (http://www.zerorpc.io/) on TCP port 4242.

USB endpoints involved for RunControl RPC are:

- ep 6 (read)
- ep 2 (write)

Read/write a register value is possible to use `zerorpc` command line:

Example: read register 0
```
zerorpc --client --connect tcp://lxconga01.na.infn.it:4242 -j readreg 0
```

Example: write register 0 - value 1
```
zerorpc  --client --connect tcp://lxconga01.na.infn.it:4242 -j writereg 0 1
```

### Event publisher

Event publisher send USB data on ZeroMQ (https://zeromq.org/) publisher socket on TCP port 5000.

USB endpoint involved for Event publisher is:

- ep 8 (read)

USB data are sent on socket "as is" without any control due to provide reasonable performance on Congatec board.

## Frontend Megamp Manager (femegaman.py)

Frontend Megamp Manager is a MIDAS FrontEnd written in Python with MIDAS Python libraries. It runs on a server/workstation
equipped with MIDAS libraries.

### Usage of feproxy.py

To run FrontEnd Megamp Manager launch:
```
./femegaman.py -i <index>
```
where `<index>` is the number of this MIDAS FrontEnd.

### MIDAS Event data format

Megamp Manager raw event has this specifications:

- a Megamp Manager handles 8 Megamp boards
- each Megamp board provides 32 channels
- each Megamp channel provides from 1 to 15 samples (value suggested: 5)

User can specify with RunControl registers:
- number of Megamp boards
- number of samples per channel

Raw events collected by FrontEnd Megamp Manager are organized with MIDAS event format, each word is 16 bit:

- Event data start with event header:
```
Evid:0001- Mask:0000- Serial:639- Time:0x5ed38991
```
Evid: event id - type of event\
Mask: trigger mask\
Serial: progressive number (provided by MIDAS)\
Time: UNIX timestamp (provided by MIDAS)

- Each Megamp board is a bank: M000, M001, ..., M008

inside a bank data are organized as follow:

(EC): Event Counter\
(NM): number of Megamp modules\
(NS): number of samples per channel\
(NC): number of channel\
(Sx): sample
```
Bank:M000
   1-> 0x0c32 0x0008 0x0005 0x0000 0x26e3 0x26e3 0x26e3 0x2f8d
        (EC)   (NM)   (NS)   (NC)   (S0)   (S1)   (S2)   (S3)
   9-> 0x2f8d 0x0001 0x3fff 0x3fff 0x3fff 0x3fff 0x3fff 0x0002
        (S4)   (NC)   (S0)   (S1)   (S2)   (S3)   (S4)
  17-> 0x03c9 0x03c6 0x03c6 0x04fd 0x04fd 0x0003 0x06c3 0x06c8 
  25-> 0x06c8 0x0657 0x0657 0x0004 0x03c8 0x03c5 0x03c5 0x0504 
  33-> 0x0504 0x0005 0x06d0 0x06cc 0x06cc 0x0658 0x0658 0x0006 
  41-> 0x03d1 0x03ce 0x03ce 0x04f5 0x04f5 0x0007 0x06d5 0x06d3 
  49-> 0x06d3 0x066c 0x066c 0x0008 0x03d7 0x03d5 0x03d5 0x0506 
  57-> 0x0506 0x0009 0x06dd 0x06dd 0x06dd 0x066a 0x066a 0x000a 
  65-> 0x03db 0x03d8 0x03d8 0x0507 0x0507 0x000b 0x06e1 0x06df 
  73-> 0x06df 0x0668 0x0668 0x000c 0x03e2 0x03e3 0x03e3 0x050e 
  81-> 0x050e 0x000d 0x06e2 0x06e1 0x06e1 0x067b 0x067b 0x000e 
  89-> 0x03e6 0x03e4 0x03e4 0x04f3 0x04f3 0x000f 0x06e7 0x06ec 
  97-> 0x06ec 0x066a 0x066a 0x0010 0x03e6 0x03e9 0x03e9 0x0532 
 105-> 0x0532 0x0011 0x06f5 0x06f3 0x06f3 0x0684 0x0684 0x0012 
 113-> 0x03ed 0x03ee 0x03ee 0x0530 0x0530 0x0013 0x06f1 0x06ef 
 121-> 0x06ef 0x067b 0x067b 0x0014 0x03f4 0x03ef 0x03ef 0x0537 
 129-> 0x0537 0x0015 0x06fe 0x0701 0x0701 0x068d 0x068d 0x0016 
 137-> 0x03f8 0x03f2 0x03f2 0x0527 0x0527 0x0017 0x0708 0x0706 
 145-> 0x0706 0x0694 0x0694 0x0018 0x03f7 0x03f7 0x03f7 0x0537 
 153-> 0x0537 0x0019 0x0704 0x0705 0x0705 0x069a 0x069a 0x001a 
 161-> 0x03fb 0x03f7 0x03f7 0x052c 0x052c 0x001b 0x06fa 0x06fb 
 169-> 0x06fb 0x0688 0x0688 0x001c 0x03fb 0x03f9 0x03f9 0x0538 
 177-> 0x0538 0x001d 0x06f6 0x06f7 0x06f7 0x0683 0x0683 0x001e 
 185-> 0x03fb 0x03fb 0x03fb 0x050c 0x050c 0x001f 0x06fe 0x06ff 
 193-> 0x06ff 0x06b6 0x06b6 
```
### ODB records

- /Equipment/MegampManager<index>/Settings/
   - Events with EC non consistent
   - Events with CRC error
   - Events with LEN error
   - Events too short
   
