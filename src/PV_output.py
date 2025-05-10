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

