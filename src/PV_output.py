""" code related with PVoutput  """

import logging
from typing import Dict
import time


logger = logging.getLogger(__name__)

class PV_Output_Limit:
    """limit the amount of request sent to pvoutput"""
    def __init__(self):
        self.register: Dict[str, int] = {}

    def ok_send(self, pvserial: str, conf) -> bool:
        """test if it is ok to send to pvoutpt"""
        now = time.perf_counter()
        ok = False
        if self.register.get(pvserial):
            ok = True if self.register.get(pvserial) + conf.pvuplimit * 60 < now else False
            if ok:
                self.register[pvserial] = int(now)
            else:
                logger.debug('\t - PVOut: Update refused for %s due to time limitation', {pvserial})
        else:
            self.register.update({pvserial: int(now)})
            ok = True
        return ok


pvout_limit = PV_Output_Limit()

def processPVOutput(conf, defined_key, jsondate, header) :
    import requests

    pvidfound = False
    if  conf.pvinverters == 1 :
        pvssid = conf.pvsystemid[1]
        pvidfound = True
    else:
        for pvnum, pvid in conf.pvinverterid.items():
            if pvid == defined_key["pvserial"] :
                print(pvid)
                pvssid = conf.pvsystemid[pvnum]
                pvidfound = True

    if not pvidfound:
        if conf.verbose : print("\t - " + "pvsystemid not found for inverter : ", defined_key["pvserial"])
        return
    
    if not pvout_limit.ok_send(defined_key["pvserial"], conf):
        # Will print a line for the refusal in verbose mode (see GrottPvOutLimit at the top)
        return
    
    if conf.verbose : 
        print("\t - " + "send data to PVOutput systemid: ", pvssid, "for inverter: ", defined_key["pvserial"])
        
    pvheader = {
        "X-Pvoutput-Apikey"   : conf.pvapikey,
        "X-Pvoutput-SystemId" : pvssid
    }

    pvodate = jsondate[:4] + jsondate[5:7] + jsondate[8:10]
    pvotime = jsondate[11:16]

    record_type = header[14:16]
    if record_type != "20" : # record is not from a smart meter
        
        # calculate average voltage of the 3 phases
        grid_voltage_L1  = defined_key["pvgridvoltage" ]
        grid_voltage_L2  = defined_key["pvgridvoltage2"]
        grid_voltage_L3  = defined_key["pvgridvoltage3"]
        grid_voltage_sum = (grid_voltage_L1 + grid_voltage_L2 + grid_voltage_L3)
        grid_voltage_avg = round((grid_voltage_sum / 30), 1) 
        
        # \todo PVoutput accepts one voltage value. 
        # It is up to the user if this is the grid voltage the string
        # voltage or any other voltage. 
        # grott should allow to adjust which voltage is sent.
                 
        pvdata = {
            "d"     : pvodate,
            "t"     : pvotime,
            "v2"    : defined_key["pvpowerin"]/10,
            "v6"    : grid_voltage_avg
        }
        if not conf.pvdisv1 :                    
            pvdata["v1"]    = defined_key["pvenergytoday"] * 100 
        else:
            if conf.verbose : 
                print("\t - " + "PVOutput send V1 disabled")

        if conf.pvtemp :
            pv_temp = defined_key["pvtemperature"]
            pvdata["v5"] = pv_temp / 10

        reqret = requests.post(conf.pvurl, data = pvdata, headers = pvheader)
      
        if conf.verbose : 
            print("\t\t - ", pvheader)
            print("\t\t - ", pvdata)
            print("\t - " + "Grott PVOutput response: ")
            print("\t\t - ", reqret.text)
        
    else: # record is from a smart meter
        # values are seprated in several packets because PVoutput does not accept them combined

        pvdata1 = {
            "d"  : pvodate,
            "t"  : pvotime,
            "v3" : defined_key["pos_act_energy"]*100, # lifetime energy consumption (day wil be calculated)
            "c1" : 3,                                 # cumulative flag indicates
            "v6" : defined_key["voltage_l1"    ]/10   # grid voltage L1
            }

        pvdata2 = {
            "d"  : pvodate,
            "t"  : pvotime,
            "v4" : defined_key["pos_rev_act_power"]/10, # power consumption
            "v6" : defined_key["voltage_l1"       ]/10, # grid voltage L1 
            "n"  : 1                                    # indicates if net data (import /export)
            }
        #  "v4"  : defined_key["pos_act_power"]/10,     # power consumption
            
        reqret1 = requests.post(conf.pvurl, data = pvdata1, headers = pvheader)
        reqret2 = requests.post(conf.pvurl, data = pvdata2, headers = pvheader)

        if conf.verbose : 
            print("\t\t - ", pvheader)
            print("\t\t - ", pvdata1)
            print("\t\t - ", pvdata2)
            print("\t - " + "PVOutput response SM1: ")
            print("\t\t - ", reqret1.text)
            print("\t - " + "PVOutput response SM2: ")
            print("\t\t - ", reqret2.text)