#!/usr/bin/env python3 

import midas
import midas.frontend
import midas.event
import sys
import struct
import zmq
import lib.evutils
from array import array

equip_stats_settings = {"Events with EC non consistent": 0, "Events with CRC error": 0, "Events with LEN error": 0, "Events too short": 0}

class MegampManagerEquipment(midas.frontend.EquipmentBase):
    def __init__(self, client, equip_name):

        default_common = midas.frontend.InitialEquipmentCommon()
        default_common.equip_type = midas.EQ_POLLED
        default_common.buffer_name = "SYSTEM"
        default_common.trigger_mask = 0
        default_common.event_id = 1
        default_common.period_ms = 100
        default_common.read_when = midas.RO_RUNNING
        default_common.log_history = 1

        self.client = midas.client.MidasClient
        self.odb_stats_base = "/Equipment/%s/Settings/" % equip_name

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.subscribe("")
        self.socket.connect ("tcp://lxconga01.na.infn.it:5000")
        
        self.eu = lib.evutils.EventUtils()
        self.eu.SetDebug(False)
        #
        self.eu.SetModuleNum(8)
        self.eu.SetSampleNum(5)
        #
        self.event_raw = array('H')
        self.buf = array('H')
        self.buflen = 0

        midas.frontend.EquipmentBase.__init__(self, client, equip_name, default_common, (equip_stats_settings))
        self.set_status("Initialized", "yellowLight")

    def begin_of_run(self, run_number):
        # reset event error statistics
        self.settings["Events with EC non consistent"] = 0
        self.settings["Events with CRC error"] = 0
        self.settings["Events with LEN error"] = 0
        self.settings["Events too short"] = 0
        self.client.odb_set(self.odb_stats_base, self.settings)

    def end_of_run(self, run_number):
        None

    def poll_func(self):
        string = self.socket.recv()
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
                    self.settings["Events with LEN error"] += 1
                    event_error = True
                #self.eu.PrintTab(self.event_raw)
                if (not self.eu.CheckEC(self.event_raw)):
                    self.settings["Events with EC non consistent"] += 1
                    event_error = True
                if (not self.eu.CheckCRC(self.event_raw)):
                    self.settings["Events with CRC error"] += 1
                    event_error = True
                if (not self.eu.CheckLength(self.event_raw)):
                    self.settings["Events with LEN error"] += 1
                    event_error = True

                if event_error is True:
                    self.client.odb_set(self.odb_stats_base, self.settings)
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

        self.equip_name = "MegampManager%s" % str(midas.frontend.frontend_index).zfill(2)
        self.mmeq = MegampManagerEquipment(self.client, self.equip_name)
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
