# Megamp Manager FrontEnd for MIDAS DAQ

## Index

[Frontend USB proxy](#frontend-usb-proxy)\
[Frontend Megamp Manager](#frontend-megamp-manager)\
[MIDAS Event data format](#midas-event-data-format)\
[Tools to inspect events](#tools-to-inspect-events)\
[Run control](#run-control)\
[ODB structure](#odb-structure)\
[Startup of frontend](#startup-of-frontend)

## Introduction

This MIDAS frontend collects events from Megamp Manager board then through MIDAS flow data are stored in MIDAS event files.

Megamp Manager DAQ software is composed by two parts:

- FrontEnd USB proxy
- Frontend Megamp Manager

## FrontEnd USB proxy

![Screenshot](docs/proxy.bmp)

FrontEnd USB proxy (feproxy) runs on Congatec board and is composed by:

- RunControl RPC
- Event publisher

### Usage of feproxy

To run FrontEnd USB proxy simple launch:
```
./feproxy
```
Note: a unique instance of feproxy is allowed to run on Congatec board due to exclusive access to USB bus.

### RunControl RPC

RunControl RPC provides a mechanism of Run Control (get/set registers) by Remote Procedure Call mechanism.
RPC is implemented with XML-RPC on port 4242.

USB endpoints involved for RunControl RPC are:

- ep 6 (read)
- ep 2 (write)

Read/write a register value is possible to use `xmlrpc` command line:

Example: read register 27
```
xmlrpc http://lxconga01.na.infn.it:4242/RPC2 readreg i/27
```

Example: write register 27 - value 3
```
xmlrpc http://lxconga01.na.infn.it:4242/RPC2 writereg i/27 i/3
```

### Event publisher

Event publisher sends USB data on ZeroMQ (https://zeromq.org/) publisher socket on TCP port 5000.

USB endpoint involved for Event publisher is:

- ep 8 (read)

USB data are sent on socket when end-of-event word (0xFxxx) is detected 

## Frontend Megamp Manager

![Screenshot](docs/frontend.bmp)

Frontend Megamp Manager (femegaman) is a MIDAS FrontEnd written in C++ with MIDAS libraries. It runs on a server/workstation equipped with MIDAS libraries.

### Usage of femegaman

To run FrontEnd Megamp Manager an environment variable MIDAS_FRONTEND_INDEX must be set before launch executable:

```
export MIDAS_FRONTEND_INDEX=<index>
```

where `<index>` is the number of this MIDAS FrontEnd.

then launch executable:

```
./femegaman
```

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
(Evid): event id - type of event\
(Mask): trigger mask\
(Serial): progressive number (provided by MIDAS)\
(Time): UNIX timestamp (provided by MIDAS)

- Each Megamp board is a bank: M000, M001, ..., M007

inside a bank data are organized as follow:

(EC): Event Counter\
(TSH): MSW of 30-bit timestamp\
(TSL): LSW of 30-bit timestamp\
(NM): number of Megamp modules\
(NS): number of samples per channel\
(NC): number of channel\
(Sx): sample
```
Bank:M000
   1-> 0x00cc 0x02c2 0x55e6 0x0008 0x0005 0x0000 0x278f 0x2792 
        (EC)   (TSH)  (TSL)  (NM)   (NS)   (NC)   (S0)   (S1)
   9-> 0x2792 0x37af 0x37af 0x0001 0x3fff 0x3fff 0x3fff 0x3fff
        (S2)   (S3)   (S4)   (NC)   (S0)   (S1)   (S2)   (S3)
  17-> 0x3fff 0x0002 0x077f 0x0705 0x0705 0x097b 0x097b 0x0003
        (S4)
  25-> 0x0d0d 0x0d06 0x0d06 0x0c25 0x0c25 0x0004 0x0705 0x0707 
  33-> 0x0707 0x0a05 0x0a05 0x0005 0x0d17 0x0d0e 0x0d0e 0x0c2b 
  41-> 0x0c2b 0x0006 0x071b 0x0715 0x0715 0x0967 0x0967 0x0007 
  49-> 0x0d27 0x0d2c 0x0d2c 0x0c55 0x0c55 0x0008 0x072d 0x0721 
  57-> 0x0721 0x0a13 0x0a13 0x0009 0x0d41 0x0d38 0x0d38 0x0c4f 
  65-> 0x0c4f 0x000a 0x0735 0x072f 0x072f 0x0a11 0x0a11 0x000b 
  73-> 0x0d3f 0x0d38 0x0d38 0x0c51 0x0c51 0x000c 0x0741 0x0738 
  81-> 0x0738 0x0a19 0x0a19 0x000d 0x0d41 0x0d45 0x0d45 0x0c6c 
  89-> 0x0c6c 0x000e 0x074d 0x0745 0x0745 0x096b 0x096b 0x000f 
  97-> 0x0d59 0x0d53 0x0d53 0x0c4d 0x0c4d 0x0010 0x074f 0x0752 
 105-> 0x0752 0x0a64 0x0a64 0x0011 0x0d65 0x0d67 0x0d67 0x0d10 
 113-> 0x0d10 0x0012 0x0763 0x075c 0x075c 0x0a64 0x0a64 0x0013 
 121-> 0x0d61 0x0d5f 0x0d5f 0x0c78 0x0c78 0x0014 0x0761 0x075e 
 129-> 0x075e 0x0a74 0x0a74 0x0015 0x0e03 0x0d7f 0x0d7f 0x0d10 
 137-> 0x0d10 0x0016 0x0767 0x076e 0x076e 0x0a52 0x0a52 0x0017 
 145-> 0x0e0e 0x0e11 0x0e11 0x0d2c 0x0d2c 0x0018 0x076d 0x076c 
 153-> 0x076c 0x0a6e 0x0a6e 0x0019 0x0e0a 0x0e0f 0x0e0f 0x0d2e 
 161-> 0x0d2e 0x001a 0x0775 0x076e 0x076e 0x0a68 0x0a68 0x001b 
 169-> 0x0d7b 0x0d6f 0x0d6f 0x0d14 0x0d14 0x001c 0x077b 0x0774 
 177-> 0x0774 0x0a72 0x0a72 0x001d 0x0d73 0x0d6f 0x0d6f 0x0d0a 
 185-> 0x0d0a 0x001e 0x0801 0x0776 0x0776 0x0a19 0x0a19 0x001f 
 193-> 0x0d7b 0x0e05 0x0e05 0x0d6a 0x0d6a 
```

## Tools to inspect events

### dumpevents

dumpevents is a simple tool to capture events from ZeroMQ socket. It displays a raw dump of event in text mode and reports
error conditions (EC mismatch, length/crc error).

### mdump

mdump is a MIDAS event dump utility that supports some parameters to filter event data. Event shown by mdump are organized
with MIDAS event format.

Example 1:
```
mdump
```
Dump a single event.

Example 2:
```
mdump -l 10 -b M000
```
Dump 10 events (-l argument) but display only bank M000 (-b argument)

Example 3:
```
mdump -f d
```
Dump a single event with decimal data representation (default: hexadecimal)

## Run Control

Run control is related to FPGA registers of Megamp Manager accessible through Frontend USB proxy and XML-RPC.

Each FPGA register has following attributes:
- label
- address
- flags

Label attribute contains Midas ODB record name related to this register\
(e.g. _/Equipment/MegampManager00-ctrl/Settings/DAC offset_)

Flags are combination of following values:
- **BOR** (Begin Of Run)\
registers with this flag will be read from ODB and written to FPGA at begin of each run 
- **SOF** (Start of Frontend)\
registers with this flag will be read from FPGA and written to ODB at start of frontend code
- **SCLR** (Self-Clear)\
registers with this flag will be read from ODB and written to ODB only when DAQ is STOPPED. User can use it through web interface and they will be automatically reset to 0.
- **SCAN** (Scan)\
registers with this flag are periodically (2 seconds frequency) read from FPGA and written to ODB in every DAQ state (RUNNING/STOPPED/PAUSED)

## ODB structure

- **/Equipment/MegampManager\<index\>-data/Statistics**
   - Events with EC not consistent
   - Events with CRC error
   - Events with LEN error
   - Events too short
   
- **/Equipment/MegampManager\<index\>-ctrl/Settings**
   - FPGA registers for board hardware setup (registers with SOF/BOR/SCLR flag)

- **/Equipment/MegampManager\<index\>-ctrl/Variables**
   - FPGA registers for board monitoring (registers with SCAN flag)
   
## Startup of frontend

Start/stop of DAQ processes can be done with MIDAS web interface with *Programs* panel. DAQ process can also be managed by command line with supervisor utility.

To check/start/stop MIDAS processes (mhttpd, mserver) on DAQ server:
```
supervisorctl status
supervisorctl start midas-mhttpd
supervisorctl start midas-mserver
supervisorctl stop midas-mhttpd
supervisorctl stop midas-mserver
```

To check/start/stop feproxy process on Congatec board:
```
supervisorctl status
supervisorctl start megaman-usb-proxy
supervisorctl stop megaman-usb-proxy
```
