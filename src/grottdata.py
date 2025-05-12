"""grottdata.py processing data functions"""

#import pytz
#import sys
#import struct
#import time
#import textwrap
import logging
import json
import codecs
#from itertools import cycle # to support "cycling" the iterator
#from os import times_result
#from typing    import Dict
from datetime  import datetime
from PV_output import processPVOutput
from influxDB  import influx_processing
from mqtt      import mqtt_processing
from utils     import hex_dump, decrypt

logger = logging.getLogger(__name__)


def AutoCreateLayout(conf, data, protocol, deviceno, recordtype) :
    """ Auto generate layout definitions from data record """
    # At this moment 3 types of layout description are known:
    # -"Clasic" inverters (eg. 1500-S) for Grott
    # -"New type" Inverters  (TL-X, TL3, MAD, MIX, MAX, MIX, SPA, SPH )
    # -"SPF" Inverters, not yet covered in the AutoCreateLayout, while detection interferes with Classic type detection.
    #
    # logger.debug("automatic determine data layout started")
    datalen = len(data)

    # decrypt data if needed      
    result_string = decrypt(data) if protocol in ("05", "06") else data.hex()
    result_len    = len(result_string)
    
    # check if data is valid
    # do not process ack records.
    if datalen < conf.mindatarec :
        layout = "none"
        return(layout, result_string)

    # create standard layout
    layout = "T" + protocol + deviceno + recordtype
    #v270 add X for extended except for smart monitor records
    if ((datalen > 375) and recordtype not in conf.smartmeterrec) : layout = layout + "X"

    if recordtype in conf.datarec:
        # for data records create or select layout definition

        inverter_type = conf.invtype.upper()
        if inverter_type == "DEFAULT" :
            logger.debug("determine invertype")
            #is invtypemap defined (map typeing multiple inverters) ?
            if any(conf.invtypemap) :
                logger.debug("invtypemap defined: %s", conf.invtypemap)
                #process invetermap defined:
                serialloc = 36
                if protocol == "06" :
                    serialloc = 76
                try:
                    inverter_serial = codecs.decode(result_string[serialloc:serialloc+20], "hex").decode('ASCII')
                    try:
                        inverter_type = conf.invtypemap[inverter_serial].upper()
                        logger.debug("Inverter serial: {0} found in invtypemap - using inverter type {1}".format(inverter_serial,inverter_type))
                    except:
                        logger.debug("Inverter serial: {0} not found invtypemap - using inverter type {1}".format(inverter_serial,inverter_type))
                except:
                    logger.critical("error in inverter_serial retrieval, try without invertypemap")

        if inverter_type == "AUTO" :
            registergrp = {}
            # layout = "AUTOGEN"
            initlayout = "ALO02" if protocol in ("00","02") else "ALO" + protocol
            
            logger.debug("Base Layout selected %s: ",initlayout)
            
            # Decode Serial number
            start  = conf.alodict[initlayout]["pvserial"]["value"]
            end    = start + 20
            sn_hex = result_string[start : end]
            layout = codecs.decode(sn_hex, "hex").decode('utf-8')

            # test if layout already exist
            try:
                # print(layout)
                # print( conf.recorddict[layout]["pvserial"]["value"])
                test = conf.recorddict[layout]["pvserial"]["value"]
                logger.debug("layout already exists and will be reused: %s", layout)
                return(layout, result_string)

            # if layout does not exist it will be created here
            except Exception as e:
                # print(e)
                logger.debug("layout does not exist yet, create it now: %s", layout)
                conf.recorddict[layout] = {}

            logger.debug("layout record used:")
            for keyword in conf.alodict[initlayout] :
                conf.recorddict[layout][keyword] = conf.alodict[initlayout][keyword]
                # format debug  
                addtab = "" # use tabs to align the output in a human readable way
                if len(keyword) <  5 : addtab = "\t"
                if len(keyword) < 13 : addtab = addtab + "\t"
                
                logger.debug("\t {0}: \t\t".format(keyword)+addtab+"{0}".format(conf.recorddict[layout][keyword]))

            # Determine register groups used in datarecord (for now max 5 groups possible)
            registergrp = {}
            # getgroup start from baselayout
            grouploc = conf.recorddict[layout]["datastart"]["value"]
            for group in range(5) :
                groupstart = result_string[grouploc     : grouploc + 4]
                groupend   = result_string[grouploc + 4 : grouploc + 8]
                registergrp[group] = { "start" : int(groupstart, 16), "end" : int(groupend, 16), "grouploc" : grouploc}
                # calculate next group start location (if any)
                grouploc = grouploc + 8 + (int(groupend,16) - int (groupstart,16) +1)*4
                logger.debug("Detected registergroup {0}, values: {1}".format(group,registergrp[group]))
                # is this the end of the record?
                if grouploc >= len(data)*2-4:
                    break

            # create layout record from register groups:
            # #set basic dataloc:
            # dataloc = conf.recorddict[layout]["datastart"]["value"]
            # #set basic lcoation where first reg starts
            # grouploc = dataloc +8
            # print ("datastart: ", dataloc)
            # print("grouploc: ", grouploc)
            # Check for prot type 1 select different layout, be aware at this time we can detect difference between type = S and type SPF inverters, SPF need to be specified seperate in invtype!!!!!
            layoutversion = ""
            if registergrp[0]["end"] < 45 : layoutversion = "V1"

            for group in registergrp :

                grplayout = "ALO_"+str(registergrp[group]["start"])+"_"+str(registergrp[group]["end"]) + layoutversion
                grouploc = registergrp[group]["grouploc"]

                logger.debug("proces layout file: %s",  grplayout)
                logger.debug("groupstart location: %s", registergrp[group]["grouploc"])

                try:
                    test = conf.alodict[grplayout]
                except:
                    logger.warning("layout file does not exist, and will not be processed: %s",grplayout)
                    break

                for keyword in conf.alodict[grplayout] :

                    conf.recorddict[layout][keyword] = conf.alodict[grplayout][keyword]
                    # calculate offset value and add/override in layout file.
                    keyloc = grouploc + 8 + ((conf.alodict[grplayout][keyword]["register"])-registergrp[group]["start"])*4
                    conf.recorddict[layout][keyword]["value"] = keyloc

                    # format debug
                    addtab = ""
                    if len(keyword) <  5 : addtab =          "\t"
                    if len(keyword) < 13 : addtab = addtab + "\t"
                    logger.debug("\t {0}: \t".format(keyword)+addtab+"{0}".format(conf.recorddict[layout][keyword]))


        if inverter_type.upper() not in ("DEFAULT", "AUTO") and recordtype not in conf.smartmeterrec :
                        layout = layout + inverter_type.upper()

        logger.debug("Auto Layout determined : %s", layout)
    try:
        # does record layout record exists?
        test = conf.recorddict[layout]
    except:
        # try generic if generic record exist
        logger.debug("no specific layout matches record, try generic layout")
        if recordtype in conf.datarec:
            layout = layout.replace(deviceno+recordtype, "NNNN")
            try:
                # does generic record layout exists?
                test = conf.recorddict[layout]
            except:
                # no valid record fall back on old processing?
                logger.debug("no matching generic inverter record layout found")
                layout = "none"

        # test smartmeter layout
        if recordtype in conf.smartmeterrec:
            print(layout)
            layout = layout.replace(deviceno, "NN")
            print(layout)

            try:
                # does generic record layout exists?
                test = conf.recorddict[layout]
            except:
                # no valid record
                logger.debug("no matching generic smart meter record layout found")
                layout = "none"

    return(layout, result_string)


def process_data(conf, data):
    logger.setLevel(conf.loglevel.upper())
    # print() # add a newline to visually indicate a new record starts here
    logger.debug("start data processing")

    header     = "".join("{:02x}".format(n) for n in data[0:8])
    #buffered  = "nodetect"    # set buffer detection to nodetect (for compat mode), will in auto detection be changed to no or yes
    protocol   = header[ 6: 8] # SET PROTOCOL TYPE(00, 02, 05, 06)
    deviceno   = header[12:14] # set devicenumber (for shinewifi, lan always: 01 for shinelink 5x)
    recordtype = header[14:16] # SET RECORD TYPE (04, 50 are inverter data records, 20, 1b smart meter, 03 = ?)
        
    # record type 50 is a historical (buffered) record type
    buffered = "yes" if recordtype == "50" else "no"

    # if not conf.compat :
    # Create layout
    (layout, result_string) = AutoCreateLayout(conf, data, protocol, deviceno, recordtype)

    if layout == "none" :
        logger.warning("ignore record without matching layout")
        no_valid_rec = True

    else : 
        logger.info("Record layout used : %s", layout)
    # save layout in conf to being passed to extension
    conf.layout = layout

    # print data records (original/decrypted)
    #logger.debug("Original  data:\n{0} \n".format(format_multi_line("\t", data,          80)))
    #logger.debug("Decrypted data:\n{0} \n".format(format_multi_line("\t", result_string, 80)))
    #print(hex_dump(bytes.fromhex(result_string)))

    # Test length if < 12 it is a data ack record or no layout record is defined
    if recordtype not in conf.datarec + conf.smartmeterrec or conf.layout == "none":
        logger.debug("Grott data ack or data record not defined, no processing done")
        
        # store all found unknown records in hexadecimal format to analyse them
        FILENAME_HEX = "unknown_records.hex" 
        my_file = open(FILENAME_HEX, mode='a')
        my_file.write("\nEncrypted:\n")
        my_file.write(hex_dump(data))
        my_file.write("\nDecrypted:\n")
        my_file.write(hex_dump(bytes.fromhex(result_string)))
        my_file.write("\n")
        my_file.close()
        
        # store all found unknown records in raw format to use them as test data
        FILENAME_TXT = "unknown_records.txt" 
        my_file = open(FILENAME_TXT, mode='a')
        my_file.write("\n")
        my_file.write(result_string)
        my_file.write("\n")
        my_file.close()
        return

    # Inital flag to detect if real data was processed
    data_processed = False

    # define dictonary for key values
    defined_key = {}

    #if conf.compat is False:
    # dataprocessing with defined record layout

    if conf.verbose:
        print("\t - " + 'Growatt new layout processing')
        #print("\t\t - " + "decrypt       : ", conf.decrypt)
        #print("\t\t - " + "offset        : ", conf.offset)
        print("\t\t - " + "record layout : ", layout)
        print()

    try:
        #v270 try if log_start and log fields are defined, if yes prepare log fields
        log_start = conf.recorddict[layout]["log_start"]["value"]
        log_dict  = {}
        log_dict  = bytes.fromhex( result_string[log_start : len(result_string)-4] ).decode("ASCII").split(",")
    except:
        pass

    #v270 log data record processing (SDM630 smart monitor with railog
    #if rectype == "data" :
    for keyword in conf.recorddict[layout].keys() :

        if keyword not in ("decrypt", "date", "log_start", "device") :
            
            #try if keyword should be included
            include = True
            try: # check if keytype was correctly specified
                if conf.recorddict[layout][keyword]["incl"] == "no" :
                    include = False
            except: # no include statement keyword should be process, set include to prevent exception
                include = True
                
            # process only keyword needs to be included (default):
            try:
                if ((include) or (conf.includeall)):
                    try: # check if keytype was correctly specified
                        keytype = conf.recorddict[layout][keyword]["type"]
                    except: # no keytype was defined, use num as default
                        keytype = "num"
                        
                    if keytype == "text" :
                        defined_key[keyword] = result_string[conf.recorddict[layout][keyword]["value"]:conf.recorddict[layout][keyword]["value"]+(conf.recorddict[layout][keyword]["length"]*2)]
                        defined_key[keyword] = codecs.decode(defined_key[keyword], "hex").decode('utf-8')
                        #print(defined_key[keyword])
                        
                    if keytype == "num" :
                        defined_key[keyword] = int(result_string[conf.recorddict[layout][keyword]["value"]:conf.recorddict[layout][keyword]["value"]+(conf.recorddict[layout][keyword]["length"]*2)],16)
                    
                    if keytype == "numx" : # process signed integer
                        keybytes = bytes.fromhex(result_string[conf.recorddict[layout][keyword]["value"]:conf.recorddict[layout][keyword]["value"]+(conf.recorddict[layout][keyword]["length"]*2)])
                        defined_key[keyword] = int.from_bytes(keybytes, byteorder='big', signed=True)
                        
                    if keytype == "log" : # process log fields
                        defined_key[keyword] = log_dict[conf.recorddict[layout][keyword]["pos"]-1]
                        
                    if keytype == "logpos" :
                        # only display this field if positive
                        # Proces log fields
                        if float(log_dict[conf.recorddict[layout][keyword]["pos"]-1]) > 0 :
                            defined_key[keyword] = log_dict[conf.recorddict[layout][keyword]["pos"]-1]
                        else : 
                            defined_key[keyword] = 0
                        
                    if keytype == "logneg" : # Proces log fields
                        # only display this field if negative
                        
                        if float(log_dict[conf.recorddict[layout][keyword]["pos"]-1]) < 0 :
                            defined_key[keyword] = log_dict[conf.recorddict[layout][keyword]["pos"]-1]
                        else : 
                            defined_key[keyword] = 0
            except:
                if conf.verbose : print("\t - utils - error in keyword processing : ", keyword + " ,data processing stopped")


    # test if pvserial was defined, if not take inverterid from config
    device_defined = False
    try:
        defined_key["device"] = conf.recorddict[layout]["device"]["value"]
        device_defined = True
    except:
        # test if pvserial was defined, if not take inverterid from config
        try:
            test = defined_key["pvserial"]
        except:
            defined_key["pvserial"] = conf.inverterid
            conf.recorddict[layout]["pvserial"] = {"value" : 0, "type" : "text"}
            if conf.verbose : print("\t - pvserial not found and device not specified used configuration defined invertid:", defined_key["pvserial"] )

    # test if dateoffset is defined, if not take set to 0 (no futher date retrieval processing)
    try:
        # test of date is specified in layout
        dateoffset = int(conf.recorddict[layout]["date"]["value"])
    except:
        # no date specified, default no date specified
        dateoffset = 0

    # process date value if specifed
    if dateoffset > 0 and (conf.gtime != "server" or buffered == "yes"):
        if conf.verbose: print("\t - " + 'Grott data record date/time processing started')

        pvyearI   = int(result_string[dateoffset+ 0 : dateoffset+ 2], 16)
        pvmonthI  = int(result_string[dateoffset+ 2 : dateoffset+ 4], 16)
        pvdayI    = int(result_string[dateoffset+ 4 : dateoffset+ 6], 16)
        pvhourI   = int(result_string[dateoffset+ 6 : dateoffset+ 8], 16)
        pvminuteI = int(result_string[dateoffset+ 8 : dateoffset+10], 16)
        pvsecondI = int(result_string[dateoffset+10 : dateoffset+12], 16)
        
        pvyear   = "200" + str(pvyearI)   if pvyearI   < 10 else "20" + str(pvyearI)
        pvmonth  =   "0" + str(pvmonthI)  if pvmonthI  < 10 else        str(pvmonthI)
        pvday    =   "0" + str(pvdayI)    if pvdayI    < 10 else        str(pvdayI)
        pvhour   =   "0" + str(pvhourI)   if pvhourI   < 10 else        str(pvhourI)
        pvminute =   "0" + str(pvminuteI) if pvminuteI < 10 else        str(pvminuteI)
        pvsecond =   "0" + str(pvsecondI) if pvsecondI < 10 else        str(pvsecondI)
     
        # create date/time string suitable for PVoutput
        pvdate = pvyear + "-" + pvmonth + "-" + pvday + "T" + pvhour + ":" + pvminute + ":" + pvsecond
        
        # test if valid date/time in data record
        try:
            testdate = datetime.strptime(pvdate, "%Y-%m-%dT%H:%M:%S")
            jsondate = pvdate
            if conf.verbose : print("\t - date-time: ", jsondate)
            
            # \todo check if time from inverter is close to server time
            
            timefromserver = False   # Indicate of date/time is from server (used for buffered data)
        except ValueError:
            # Date could not be parsed - either the format is different or 
            # it's not a valid date
            if conf.verbose : print("\t - " + "no or no valid time/date found, grott server time will be used (buffer records not sent!)")
            timefromserver = True
            jsondate = datetime.now().replace(microsecond=0).isoformat()
    else:
        if conf.verbose: print("\t - " + "Grott server date/time used")
        jsondate       = datetime.now().replace(microsecond=0).isoformat()
        timefromserver = True

    data_processed = True

    if data_processed: # only send data to MQTT if data was processed

        if conf.verbose:
            # print values for all defined keys as retrieved from data logger
            print("\t - " + "Grott values retrieved:")
            for key in defined_key :
                # test if there is specified a divide factor
                try:
                    keydivide = conf.recorddict[layout][key]["divide"]
                    #print(keyword)
                    #print(keydivide)
                except:
                    #print("error")
                    keydivide = 1

                if type(defined_key[key]) != type(str()) and keydivide != 1 :
                    printkey = "{:.1f}".format(defined_key[key]/keydivide)
                else :
                    printkey = defined_key[key]
                print("\t\t - ",key.ljust(30) + " : ", printkey)

        # create JSON message (first create obj dict and then convert to a JSON message)

        # only process records of type 0120 if they have a voltage in the range of 0 .. 500V
        record_type = header[14:16]
        if record_type == "20" :
            real_voltage = defined_key["voltage_l1"]/10
            if (real_voltage > 500) or (real_voltage < 0) :
                print("\t - " + "invalid 0120 record processing stopped")
                return

        # v270
        # compatibility with prev releases for "20" smart monitor record!
        # if device is not specified in layout record datalogserial is used as device (to distinguish record from inverter record)

        if device_defined == True:
            deviceid = defined_key["device"]

        else :
            if record_type not in conf.smartmeterrec :
                deviceid = defined_key["pvserial"]
            else :
                deviceid = defined_key["datalogserial"]

        jsonobj = {
                    "device"   : deviceid,
                    "time"     : jsondate,
                    "buffered" : buffered,
                    "values"   : {}
        }

        for key in defined_key :
            jsonobj["values"][key] = defined_key[key]

        jsonmsg = json.dumps(jsonobj)

        #if conf.verbose:
            # print("\t - " + "MQTT jsonmsg: ")
            # print(format_multi_line("\t\t\t ", jsonmsg))

        # do not process invalid records 
        # (e.g. buffered records with time from server) 
        # or buffered records if sendbuf = False
        if (buffered == "yes") :
            if (conf.sendbuf == False) or (timefromserver == True) :
                if conf.verbose : print("\t - " + 'Buffered record not sent: sendbuf = False or invalid date/time format')
                return


        if conf.nomqtt != True:
            mqtt_processing(conf, header, jsonmsg, deviceid)
        else:
            if conf.verbose : print("\t - " + 'Sending data via MQTT disabled')


        # process pvoutput if enabled
        if conf.pvoutput :
            processPVOutput(conf, defined_key, jsondate, header)
        else:
            if conf.verbose : print("\t - " + "Sending data to PVOutput disabled ")


    # influxDB processing
    if conf.influx:
        influx_processing(conf, jsondate, header, defined_key)


    if conf.extension :
        if conf.verbose :  
            print("\t - " + "extension processing started : ", conf.extname)
        import importlib
        try:
            module = importlib.import_module(conf.extname, package = None)
        except :
            if conf.verbose : print("\t - " + "import extension failed:", conf.extname)
            return

        try:
            ext_result = module.grottext(conf,result_string,jsonmsg)
            if conf.verbose :
                print("\t - " + "extension processing ended : ", ext_result)
        except Exception as e:
            print("\t - " + "extension processing error:", repr(e))
            if conf.verbose:
                import traceback
                print("\t - " + traceback.format_exc())

    else:
            if conf.verbose : print("\t - " + "Grott extension processing disabled ")
