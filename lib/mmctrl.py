import midas
import midas.frontend
import zerorpc
from lib.register import GetRegAddress, GetRegs,\
        GetCommitRegs, BOR, SOF, SCLR, SCAN

class MegampManagerEquipmentCtrl(midas.frontend.EquipmentBase):
    def __init__(self, client, equip_name, feindex, proxy):

        default_common = midas.frontend.InitialEquipmentCommon()
        default_common.equip_type = midas.EQ_PERIODIC
        default_common.buffer_name = "SYSTEM"
        default_common.trigger_mask = 0
        default_common.event_id = 100
        default_common.period_ms = 2000
        default_common.read_when = midas.RO_ALWAYS
        default_common.log_history = 1

        self.feindex = feindex
        equip_name_ctrl = equip_name + "-ctrl"
        self.odb_ctrl_base = "/Equipment/%s/Settings" % equip_name_ctrl

        self.rpcclient = zerorpc.Client()
        ep_ctrl = "tcp://%s:4242" % proxy['hostname']
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


