#!/usr/bin/env python3

import midas
import midas.frontend
import midas.event
import sys
import struct
import zmq
import zerorpc
import lib.evutils
from array import array

### params
proxy_host = "lxconga01.na.infn.it"
###

class MegampManagerEquipmentData(midas.frontend.EquipmentBase):
    def __init__(self, client, equip_name):

        default_common = midas.frontend.InitialEquipmentCommon()
        default_common.equip_type = midas.EQ_POLLED
        default_common.buffer_name = "SYSTEM"
        default_common.trigger_mask = 0
        default_common.event_id = 1
        default_common.period_ms = 100
        default_common.read_when = midas.RO_RUNNING
        default_common.log_history = 1

        self.context = zmq.Context()
        self.data_socket = self.context.socket(zmq.SUB)
        self.data_socket.subscribe("")
        ep_data = "tcp://%s:5000" % proxy_host
        self.data_socket.connect(ep_data)

        self.rpcclient = zerorpc.Client()
        ep_ctrl = "tcp://%s:4242" % proxy_host
        self.rpcclient.connect(ep_ctrl)

        self.eu = lib.evutils.EventUtils()
        self.eu.SetDebug(False)
        #
        self.eu.SetModuleNum(8)
        self.eu.SetSampleNum(5)
        #
        self.event_raw = array('H')
        self.buf = array('H')
        self.buflen = 0

        self.default_settings = {"Number of samples per channel": 0}

        self.odb_stats_base = "/Equipment/%s/Counters" % equip_name
        self.stats_settings = {"Events with CRC error": 0, "Events with LEN error": 0, "Events too short": 0, "Events with EC not consistent": 0}
        client.odb_set(self.odb_stats_base, self.stats_settings)

        midas.frontend.EquipmentBase.__init__(self, client, equip_name, default_common, self.default_settings)

        self.set_status("Initialized", "yellowLight")

    def begin_of_run(self, run_number):
        # reset event error statistics
        self.stats_settings["Events with EC not consistent"] = 0
        self.stats_settings["Events with CRC error"] = 0
        self.stats_settings["Events with LEN error"] = 0
        self.stats_settings["Events too short"] = 0
        self.client.odb_set(self.odb_stats_base, self.stats_settings)

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
                    self.client.odb_set(self.odb_stats_base, self.stats_settings)
                    del self.event_raw[:]
                    return False
                else:
                    return True

        return False

    def readout_func(self):
        event = midas.event.Event()
        for i in range(self.eu.GetModuleNum()):          # for each Megamp
            chdata = []
            chdata.append(self.eu.GetEC(self.event_raw))    # event counter
            chdata.append(self.eu.GetModuleNum())              # number of Megamp modules
            chdata.append(self.eu.GetSampleNum())           # number of samples per channel
            bankname = "M" + str(i).zfill(3)
            for j in range(32):     # for each channel
                chdata.append(j)
                chdata.extend(self.eu.GetChannelSamples(self.event_raw,i,j).tolist())
            event.create_bank(bankname, midas.TID_WORD, chdata)

        del self.event_raw[:]

        return event

class Frontend(midas.frontend.FrontendBase):
    def __init__(self):
        midas.frontend.FrontendBase.__init__(self, "MegaManFE")
        if(midas.frontend.frontend_index == -1):
            print("Error: please specify frontend index (-i argument)")
            sys.exit(-1)

        self.equip_name = "MegampManager%s-data" % str(midas.frontend.frontend_index).zfill(2)
        self.mmeq = MegampManagerEquipmentData(self.client, self.equip_name)
        self.add_equipment(self.mmeq)
        if(self.run_state == midas.STATE_RUNNING):
            self.set_all_equipment_status("Running", "greenLight")

    def begin_of_run(self, run_number):
        self.set_all_equipment_status("Running", "greenLight")
        self.client.msg("Frontend has seen start of run number %d" % run_number)
        self.mmeq.begin_of_run(run_number)
        return midas.status_codes["SUCCESS"]

    def end_of_run(self, run_number):
        self.set_all_equipment_status("Finished", "greenLight")
        self.client.msg("Frontend has seen end of run number %d" % run_number)
        self.mmeq.end_of_run(run_number)
        return midas.status_codes["SUCCESS"]

if __name__ == "__main__":
    fe = Frontend()
    fe.run()
