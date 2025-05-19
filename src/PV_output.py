""" code related with PVoutput  """

import logging
import time
from typing import Dict



logger = logging.getLogger(__name__)

# expects the provided string to store date/time information in the form
# YYMMDDHHMMSS
# with the year in the 21th century
# all values as hexadecimal strings 
def create_PV_date_time_str(time_str, offset):

    year   = int(time_str[offset+ 0 : offset+ 2], 16)
    month  = int(time_str[offset+ 2 : offset+ 4], 16)
    day    = int(time_str[offset+ 4 : offset+ 6], 16)
    hour   = int(time_str[offset+ 6 : offset+ 8], 16)
    minute = int(time_str[offset+ 8 : offset+10], 16)
    second = int(time_str[offset+10 : offset+12], 16)
                    
    # create date/time string suitable for PV output
    # in the format YYYY-MM-DDTHH:MM:SS"
    date_time_str ="20{:02}-{:02}-{:02}T{:02}:{:02}:{:02}".\
                   format(year, month, day, hour, minute, second) 
    
    return date_time_str


class PV_Output_Limit:
    """limit the amount of request sent to pvoutput"""
    def __init__(self):
        self.register: Dict[str, int] = {}

    def ok_send(self, pvserial: str, conf) -> bool:
        """test if it is ok to send to pvoutpt"""
        now = time.perf_counter()
        ok  = False
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


def processPVOutput(conf, msg, defined_key, jsondate) :
    import requests

    pvidfound = False
    if  conf.pvinverters == 1 :
        pvssid    = conf.pvsystemid[1]
        pvidfound = True
    else:
        for (pvnum, pvid) in conf.pvinverterid.items():
            if pvid == defined_key["pvserial"] :
                logger.debug("{}".format(pvid))
                pvssid    = conf.pvsystemid[pvnum]
                pvidfound = True

    if not pvidfound:
        logger.debug("pvsystemid not found for inverter: {} ".format(defined_key["pvserial"]))
        return
    
    if not pvout_limit.ok_send(defined_key["pvserial"], conf):
        return
    
    logger.debug("send data to PV Output systemid: () for inverter: () ".format(pvssid, defined_key["pvserial"]))
        
    pvheader = {
        "X-Pvoutput-Apikey"   : conf.pvapikey,
        "X-Pvoutput-SystemId" : pvssid
    }

    pvodate = jsondate[:4] + jsondate[5:7] + jsondate[8:10]
    pvotime = jsondate[11:16]

    if msg["cmd"] != 32 : # record is not from a smart meter
        
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
            "d"  : pvodate,
            "t"  : pvotime,
            "v2" : defined_key["pvpowerin"] / 10,
            "v6" : grid_voltage_avg
        }
        if not conf.pvdisv1 :                    
            pvdata["v1"] = defined_key["pvenergytoday"] * 100 
        else:
            logger.debug("PVOutput send V1 disabled")

        if conf.pvtemp :
            pv_temp      = defined_key["pvtemperature"]
            pvdata["v5"] = pv_temp / 10

        response = requests.post(conf.pvurl, data = pvdata, headers = pvheader)
      
        logger.debug("{} {}".format(pvheader, pvdata))
        logger.debug("PVOutput response: {}".format(response.text))
        
    else: # record is from a smart meter
        # values are send in two packets because PVoutput does not accept them combined

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
         #  "v4" : defined_key["pos_act_power"    ]/10, # power consumption
            "v6" : defined_key["voltage_l1"       ]/10, # grid voltage L1 
            "n"  : 1                                    # indicates if net data (import /export)
            }
        
        response1 = requests.post(conf.pvurl, data = pvdata1, headers = pvheader)
        response2 = requests.post(conf.pvurl, data = pvdata2, headers = pvheader)

        logger.debug("{} {} {}".format(pvheader, pvdata1, pvdata2))
        logger.debug("PVOutput response1: {}".format(response1.text))
        logger.debug("PVOutput response2: {}".format(response2.text))
