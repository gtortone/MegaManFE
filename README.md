# Megamp Manager FrontEnd for MIDAS DAQ

This MIDAS frontend collects events from Megamp Manager board then through MIDAS flow data are stored in MIDAS event files.

Megamp Manager frontend is composed by two parts:

- FrontEnd USB proxy
- Frontend Megamp Manager

## FrontEnd USB proxy (feproxy.py)

FrontEnd USB proxy runs on Congatec board and is composed by:

- RunControl RPC
- Event publisher

### RunControl RPC

RunControl RPC provides a mechanism of Run Control (get/set registers) by Remote Procedure Call mechanism.
RPC is implemented with ZeroRPC (http://www.zerorpc.io/) on TCP port 4242

To get/set a register value is possible to use `zerorpc` command line:


Example: write register 0 - value 1
```
zerorpc  --client --connect tcp://lxconga01.na.infn.it:4242 -j writereg 0 1
```

Example: read register 0
```
zerorpc --client --connect tcp://lxconga01.na.infn.it:4242 -j readreg 0
```
