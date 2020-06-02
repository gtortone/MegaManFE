#!/usr/bin/env python3

import midas
import midas.frontend
import midas.event
import sys
import struct
import zmq
import zerorpc
import lib.evutils as evutils
from lib.register import GetRegAddress, GetRegs,\
        GetCommitRegs, BOR, SOF, SCLR, SCAN
from array import array

### params
proxy_host = "lxconga01.na.infn.it"
###

class MegampManagerEquipmentCtrl(midas.frontend.EquipmentBase):
    def __init__(self, client, equip_name, feindex):

        default_common = midas.frontend.InitialEquipmentCommon()
        default_common.equip_type = midas.EQ_PERIODIC
        default_common.buffer_name = "SYSTEM"
        default_common.trigger_mask = 0
        default_common.event_id = 100
        default_common.period_ms = 2000
        default_common.read_when = midas.RO_ALWAYS
        default_common.log_history = 1

        self.client = client
        self.feindex = feindex
        equip_name_ctrl = equip_name + "-ctrl"
        self.odb_ctrl_base = "/Equipment/%s/Settings" % equip_name_ctrl

        self.rpcclient = zerorpc.Client()
        ep_ctrl = "tcp://%s:4242" % proxy_host
        self.rpcclient.connect(ep_ctrl)

        # initialize default settings
        self.default_settings = {}
        for item in GetRegs():
            self.default_settings[item['label']] = 0

        # read FPGA registers with SOF flag - write to ODB
        for item in GetRegs(SOF):
            value = self.rpcclient.readreg(item['address'])
            self.default_settings[item['label']] = value

        midas.frontend.EquipmentBase.__init__(self, client, equip_name_ctrl,
                                              default_common,
                                              self.default_settings)

        self.set_status("Initialized", "yellowLight")

    def begin_of_run(self, run_number):
        # read from ODB - write to FPGA registers with BOR
        for item in GetRegs(BOR):
            addr = item['address']
            value = self.client.odb_get(self.odb_ctrl_base + "/%s" %
                                        item['label'])
            self.rpcclient.writereg(addr, value)
        # commit register
        for item in GetCommitRegs():
            addr = item['address']
            self.rpcclient.writereg(addr, 1)

    def end_of_run(self, run_number):
        None

    def readout_func(self):
        # read FPGA registers with SCAN flag - write to ODB
        for item in GetRegs(SCAN):
            value = self.rpcclient.readreg(item['address'])
            self.default_settings[item['label']] = value
            self.client.odb_set(self.odb_ctrl_base + "/%s" \
                                % item['label'], value)

        # check SCLR registers: if value is 1 set again to 0
        # and set FPGA register
        state = self.client.odb_get("/Runinfo/State")
        for item in GetRegs(SCLR):
                value = self.client.odb_get(self.odb_ctrl_base + "/%s" % \
                                item['label'])
                if (value != 0):
                    if (state != midas.STATE_RUNNING):
                        addr = GetRegAddress(item['label'])
                        self.rpcclient.writereg(addr, 1)
                        self.rpcclient.writereg(addr, 0)
                    else:
                        self.client.msg("Register not available in running mode",
                                        is_error=True)
                    self.client.odb_set(self.odb_ctrl_base + "/%s" % \
                                        item['label'], 0)

        self.client.communicate(10)

class MegampManagerEquipmentData(midas.frontend.EquipmentBase):

    eu = evutils.EventUtils()

    def __init__(self, client, equip_name, feindex):

        default_common = midas.frontend.InitialEquipmentCommon()
        default_common.equip_type = midas.EQ_POLLED
        default_common.buffer_name = "SYSTEM"
        default_common.trigger_mask = 0
        default_common.event_id = 1
        default_common.period_ms = 100
        default_common.read_when = midas.RO_RUNNING
        default_common.log_history = 1

        self.feindex = feindex
        self.equip_name = equip_name
        equip_name_data = equip_name + "-data"

        self.context = zmq.Context()
        self.data_socket = self.context.socket(zmq.SUB)
        self.data_socket.subscribe("")
        ep_data = "tcp://%s:5000" % proxy_host
        self.data_socket.connect(ep_data)

        self.event_raw = array('H')
        self.buf = array('H')
        self.buflen = 0

        self.odb_stats_base = "/Equipment/%s/Counters" % equip_name_data
        self.stats_settings = {"Events with CRC error": 0, \
                               "Events with LEN error": 0, \
                               "Events too short": 0, \
                               "Events with EC not consistent": 0}
        client.odb_set(self.odb_stats_base, self.stats_settings)

        midas.frontend.EquipmentBase.__init__(self, client,
                                              equip_name_data, default_common)

        self.setup_of_run()

        self.set_status("Initialized", "yellowLight")

    def setup_of_run(self):
        #
        self.eu.SetModuleNum(8)
        #
        snum = self.client.odb_get(
            "/Equipment/%s/Settings/Board/Number of samples per channel" %\
            (self.equip_name + "-ctrl"))
        self.eu.SetSampleNum(snum)
        self.eu.SetDebug(False)

    def begin_of_run(self, run_number):
        # reset event error statistics
        for key in self.stats_settings.keys():
            self.stats_settings[key] = 0
        self.client.odb_set(self.odb_stats_base, self.stats_settings)

        self.setup_of_run()

    def end_of_run(self, run_number):
        None

    def poll_func(self):
        string = self.data_socket.recv()
        self.buflen = len(string) // 2
        self.buf = struct.unpack('H'*self.buflen, string)

        for word in self.buf:
            if(len(self.event_raw) > 60000):
                del self.event_raw[:]
                continue
            self.event_raw.append(word)
            if( (word & 0xF000) == 0xF000):      # end of event
                event_error = False
                if(len(self.event_raw) < 3):
                    self.stats_settings["Events with LEN error"] += 1
                    event_error = True
                #self.eu.PrintTab(self.event_raw)
                if (not self.eu.CheckEC(self.event_raw)):
                    self.stats_settings["Events with EC not consistent"] += 1
                    event_error = True
                if (not self.eu.CheckCRC(self.event_raw)):
                    self.stats_settings["Events with CRC error"] += 1
                    event_error = True
                if (not self.eu.CheckLength(self.event_raw)):
                    self.stats_settings["Events with LEN error"] += 1
                    event_error = True

                if event_error is True:
                    self.client.odb_set(self.odb_stats_base,
                                        self.stats_settings)
                    del self.event_raw[:]
                    return False
                else:
                    return True

        return False

    def readout_func(self):
        event = midas.event.Event()
        for i in range(self.eu.GetModuleNum()):
            chdata = []
            chdata.append(self.eu.GetEC(self.event_raw))
            chdata.append(self.eu.GetModuleNum())
            chdata.append(self.eu.GetSampleNum())
            bankname = "M" + str(i).zfill(3)
            for j in range(32):
                chdata.append(j)
                chdata.extend(self.eu.GetChannelSamples(
                    self.event_raw,i,j).tolist())
            event.create_bank(bankname, midas.TID_WORD, chdata)

        del self.event_raw[:]

        return event

class Frontend(midas.frontend.FrontendBase):
    def __init__(self):
        midas.frontend.FrontendBase.__init__(self, "MegaManFE")
        feindex = midas.frontend.frontend_index
        if(feindex == -1):
            print("Error: please specify frontend index (-i argument)")
            sys.exit(-1)

        equip_name = "MegampManager%s" % \
                str(midas.frontend.frontend_index).zfill(2)
        self.eqdata = MegampManagerEquipmentData(self.client, equip_name,
                                                 feindex)
        self.add_equipment(self.eqdata)
        equip_name = "MegampManager%s" % \
                str(midas.frontend.frontend_index).zfill(2)
        self.eqctrl = MegampManagerEquipmentCtrl(self.client, equip_name,
                                                 feindex)
        self.add_equipment(self.eqctrl)
        if(self.run_state == midas.STATE_RUNNING):
            self.set_all_equipment_status("Running", "greenLight")

    def begin_of_run(self, run_number):
        self.set_all_equipment_status("Running", "greenLight")
        self.client.msg("Frontend has seen start of run number %d" % \
                        run_number)
        self.eqctrl.begin_of_run(run_number)
        self.eqdata.begin_of_run(run_number)
        return midas.status_codes["SUCCESS"]

    def end_of_run(self, run_number):
        self.set_all_equipment_status("Finished", "greenLight")
        self.client.msg("Frontend has seen end of run number %d" % \
                        run_number)
        self.eqctrl.end_of_run(run_number)
        self.eqdata.end_of_run(run_number)
        return midas.status_codes["SUCCESS"]

if __name__ == "__main__":
    fe = Frontend()
    fe.run()
