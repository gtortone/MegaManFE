import midas
import midas.frontend
import midas.event
import lib.evutils as evutils
import zmq
import struct
from array import array

class MegampManagerEquipmentData(midas.frontend.EquipmentBase):

    eu = evutils.EventUtils()

    def __init__(self, client, equip_name, feindex, proxy):

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
        ep_data = "tcp://%s:5000" % proxy['hostname']
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
        time = self.eu.GetTime(self.event_raw)
        for i in range(self.eu.GetModuleNum()):
            chdata = []
            chdata.append(self.eu.GetEC(self.event_raw))
            chdata.append((time & 0xFFFF0000) >> 16)
            chdata.append((time & 0x0000FFFF))
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


