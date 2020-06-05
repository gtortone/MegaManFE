#!/usr/bin/env python3

import midas
import midas.frontend
import midas.event
import sys
import lib.mmctrl as mmctrl
import lib.mmdata as mmdata
from xmlrpc.client import ServerProxy

### params
proxy_host = "lxconga01.na.infn.it"
proxy_user = "midas"
proxy_pass = "m1d4s"

proxy = {'hostname': proxy_host,
         'username': proxy_user,
         'password': proxy_pass
        }
###

class Frontend(midas.frontend.FrontendBase):
    def __init__(self):

        midas.frontend.FrontendBase.__init__(self, "MegaManFE")
        feindex = midas.frontend.frontend_index
        if(feindex == -1):
            print("Error: please specify frontend index (-i argument)")
            sys.exit(-1)

        # check if megaman-usb-proxy is running
        server = ServerProxy("http://%s:%s@%s:9001/RPC2" % (proxy['username'],
                                                            proxy['password'],
                                                            proxy['hostname']))

        info = None
        try:
            info = server.supervisor.getProcessInfo('megaman-usb-proxy')
        except:
            pass

        if(info is None):
            self.client.msg("E: supervisor on proxy host is not running",
                           is_error=True)
            self.client.msg("check configuration of %s" % proxy_host)
            sys.exit(-1)

        if(info['statename'] != 'RUNNING'):
            # try to restart megaman-usb-proxy
            self.client.msg("I: megaman-usb-proxy is not running ")
            self.client.msg("I: megaman-usb-proxy restarting")
            server.supervisor.startProcess('megaman-usb-proxy')
            info = server.supervisor.getProcessInfo('megaman-usb-proxy')
            if(info['statename'] != 'RUNNING'):
                self.client.msg("E: megaman-usb-proxy failed restart",
                               is_error=True)
                sys.exit(-1)
            else:
                self.client.msg("I: megaman-usb-proxy restarted successfully")

        equip_name = "MegampManager%s" % \
                str(midas.frontend.frontend_index).zfill(2)
        self.eqctrl = mmctrl.MegampManagerEquipmentCtrl(self.client, equip_name,
                                                 feindex, proxy)
        self.eqdata = mmdata.MegampManagerEquipmentData(self.client, equip_name,
                                                 feindex, proxy)
        self.add_equipment(self.eqctrl)
        self.add_equipment(self.eqdata)

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
        self.set_all_equipment_status("Finished", "yellowLight")
        self.client.msg("Frontend has seen end of run number %d" % \
                        run_number)
        self.eqctrl.end_of_run(run_number)
        self.eqdata.end_of_run(run_number)
        return midas.status_codes["SUCCESS"]

if __name__ == "__main__":
    fe = Frontend()
    fe.run()
