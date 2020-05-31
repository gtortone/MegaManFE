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

Event publisher send USB data on ZeroMQ publisher socket on TCP port 5000.

USB endpoint involved for Event publisher is:

- ep 8 (read)

USB data are sent on socket "as is" without any control due to provide reasonable performance on Congatec board.

## Frontend Megamp Manager (femegaman.py)

Frontend Megamp Manager is a MIDAS FrontEnd written in Python with MIDAS Python libraries. It runs on a server/workstation
equipped with MIDAS libraries.

### Usage of feproxy.py

To run Frontend Megamp Manager launch:
```
./femegaman.py -i <index>
```
where `<index>` is the number of this MIDAS FrontEnd.

