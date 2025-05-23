"""grottdata.py processing data functions"""

#import pytz
#import sys
#import struct
#import time
#import textwrap
import logging
import json
import codecs
#from os import times_result
#from typing    import Dict
from datetime  import datetime
from PV_output import processPVOutput, create_PV_date_time_str
from influxDB  import influx_processing
from mqtt      import mqtt_processing
from utils     import write_Dict2file, convertBin2Str, decrypt_as_bin, convert_Dict2str, hex_dump, to_hexstring
from extension import extension_processing
from crc       import modbus_crc


logger = logging.getLogger(__name__)


def is_ping_msg(cmd):
    return (cmd == get_command_value("ping"))


def is_get_sm_values_msg(cmd):
    return (cmd == get_command_value("get_sm_values"))


def is_Datalogger_msg(cmd):
    return (cmd == get_command_value("Datalogger"))


def decode_ping_message(msg):
    # The format of a ping message is 
    # Modbus Header    6 bytes consisting of
    # - Sequence number  2 bytes, increasing with every ping message
    # - Protocol version 2 bytes, typical values are 2, 5 or 6
    # - data length      2 bytes, typical value 34
    # Data consisting of 
    # - Device number    1 byte
    # - command = 16     1 byte
    # - Serial number   10 bytes of the data logger device
    # - Zeropadding     20 bytes
    # - CRC              2 bytes depending on protocol version
    #
    # The datalogger (client) sends a ping to the server (Growatt site) regularly.
    # In my case it was every 35 seconds. The sequence number gets incremented
    # for every ping message.
    # The receiver of the ping message responds with a ping message
    # that holds the exact same data content and sequence number as the 
    # received ping message.
    
    if not is_ping_msg(msg["cmd"]): return 
    
    #logger.debug(convert_Dict2str(msg, "\n", exclude = {"dat_str", "protocol", "layout", "cmd", "record_num", "crc_len", "crc", "valid"}))
    
    sn_len   = 10
    sn_start = 0
    sn_end   = sn_start + sn_len
    sn_str   = str(msg["payload_bin"][sn_start:sn_end]) # codecs.decode(sn_hex, "hex").decode('utf-8')
    # logger.debug("Message: {}, seq: {:3}, SN: {}, from: {}".\
    #     format(msg["cmd_name"], msg["seq_num"], sn_str, msg["from"][0]))
    return

def decode_get_sm_value_message(msg) :
    # sm means smart meter
    #
    # The format of a get_sm_values message is 
    # Modbus Header    6 bytes consisting of
    # - Sequence number  2 bytes, increasing with every get_sm_values message
    # - Protocol version 2 bytes, typical values are 2, 5 or 6
    # - data length      2 bytes, typical value 270
    # Data consisting of 
    # - Device number    1 byte
    # - command = 32     1 byte
    # - Serial number   10 bytes of Datalogger device
    # - Zeropadding     20 bytes
    # - Serial number   10 bytes of Inverter device
    # - Zeropadding     20 bytes
    # - binary data      X bytes that presumably hold smart meter measurements \todo decode them
    # - Serial number   10 bytes of Datalogger device
    # - Zeropadding     20 bytes 
    # - CRC              2 bytes depending on protocol version
    #
    # In Response to a get_sm_values message the receiver responds
    # with a get_sm_values message with the same sequence number and
    # a 1 byte response code
    # I only saw the response code 0 which probably means ok
    # I guess there are other repsonse codes which indicate errors (that I never saw).
    
    # There is already a decode layout T060120 for smart meter messages
    #
    # datalogserial                  : XGD6CF42W6
    # pvserial                       : KNN0D7403B
    # voltage_l1                     : 229.7
    # Current_l1                     : 0.0
    # act_power_l1                   : 0.0
    # app_power_l1                   : 221.2
    # react_power_l1                 : -60.5
    # powerfactor_l1                 : -1.0
    # pos_rev_act_power              : 0.0
    # app_power                      : 637.1
    # react_power                    : -378.7
    # powerfactor                    : -0.2
    # frequency                      : 50.0
    # L1-2_voltage                   : 397.1
    # L2-3_voltage                   : 397.5
    # L3-1_voltage                   : 398.4
    # pos_act_energy                 : 197.5
    # rev_act_energy                 : 1723.0
    
    if not is_get_sm_values_msg(msg["cmd"]): return
    
    # logger.debug("Message: {}, seq: {:3}, len: {}, from: {}".\
    #     format(msg["cmd_name"], msg["seq_num"], msg["len"], msg["from"][0]))
    
    #logger.debug(convert_Dict2str(msg, "\n", exclude = {"dat_str", "dat_bin", "payload_str", "payload_bin", "protocol", "layout", "cmd", "record_num", "crc_len", "crc", "valid"}))
    #logger.debug(hex_dump(msg["payload_bin"], 16))
    
    FILENAME_HEX = "get_sm_values.txt"
    with open(FILENAME_HEX, "a") as f:
        print("{}, seq: {}, len: {} ,from: {}\n{}\n".\
              format(msg["rec_time"], msg["seq_num"], msg["len"], msg["from"][0], to_hexstring(msg["dat_bin"])), file=f)
    f.close()
    
    FILENAME_HEX = "get_sm_values.hex"
    with open(FILENAME_HEX, "a") as f:
        print("{}\n".format(to_hexstring(msg["dat_bin"])), file=f)
    f.close()
    return 


def decode_Datalogger_message(msg) :
    # sm means smart meter
    #
    # The format of a DataloggerID message is 
    # Modbus Header    6 bytes consisting of
    # - Sequence number  2 bytes, always 1
    # - Protocol version 2 bytes, typical values are 2, 5 or 6
    # - data length      2 bytes, typical value ...
    # Data consisting of 
    # - Device number    1 byte
    # - command=25(x18)  1 byte
    # - Serial number   10 bytes of Datalogger device
    # - Padding \x00    20 bytes
    # - A register or parameter number
    # - The value of the registers
    # - CRC              2 bytes depending on protocol version
    #
    # The server sends a DataloggerID Request command with a start and as
    # stop number. 
    # it has sequence number 1 data
    # - Device number    1 byte
    # - command = 25     1 byte
    # - Serial number   10 bytes
    # - first parameter  2 bytes
    # - last  parameter  2 bytes 
    #
    #
    # The client responds to it with a series of consecutive DataloggerID responses.
    # All have the same sequence number as the request
    # Every message sends the value of one parameter in the requested range 
    # start..stop 
    # 
    #
    # Example request x00 x04 x00 x15 = start 4(=x4), stop 21(=x15)
    #
    # Example response
    # same of the response values a prepended by binary values which have noknown meaning
    #
    #  x04 = Update intervall = x00 x01 5
    #  x05 = ?                = x00 x01 1
    #  x06 = ?                = x00 x02 32
    #  x07 = ?                = x00 x01 "X"
    #  x08 = Data Logger SN   = x00 x0a XGD6CF42W6
    #  x09 = ?                = x00 x04 4x"X"
    #  x0A = ?                = x00 x01 0
    #  x0B = URL              = ##192.168.3.35/app/xml/#8081#
    #  x0C = ?                = x00 x0f 15x"X"
    #  x0D = ?                = x00 x02 16
    #  x0E = IP               = 192.168.5.1
    #  x0F = Port             = 80
    #  x10 = MAC              = 58:BF:25:XX:XX:XX
    #  x11 = IP               = 192.168.178.19
    #  x12 = Port             = 5379
    #  x13 = set server addr  = all zeros
    #  x14 = ?                = x00 x14 + 20 times "X"
    #  x15 = FW               = 3.1.1.0
    #  x1f = Data/time        = x00 x13 2017-07-01 23:59:59 (why is it an outdated timestamp?, looks like a time format rather than a timestamp)
    #  x20 = Reboot request   = x00 x01 x31
    #  x4c = RSSI             = x00 x03 -54
    #
    # Error codes 0x00 = OK , 0x03 = NACK
    
    if not is_Datalogger_msg(msg["cmd"]): return
    
    logger.debug("Message: {}, len: {}, from: {}".\
        format(msg["cmd_name"], msg["len"], msg["from"][0]))
    
    #logger.debug(convert_Dict2str(msg, "\n", exclude = {"dat_str", "device_no", "rec_time", "dat_bin", "payload_str", "payload_bin", "protocol", "layout", "cmd", "record_num", "crc_len", "crc", "valid"}))
    #print(hex_dump(msg["payload_bin"], 16))
    
    FILENAME_HEX = "datalogger.txt"
    with open(FILENAME_HEX, "a") as f:
        print("{}, seq: {}, len: {} ,from: {}\n{}\n".\
              format(msg["rec_time"], msg["seq_num"], msg["len"], msg["from"][0], to_hexstring(msg["dat_bin"])), file=f)
    f.close()
    
    FILENAME_HEX = "datalogger.hex"
    with open(FILENAME_HEX, "a") as f:
        print("{}\n".format(to_hexstring(msg["dat_bin"])), file=f)
    f.close()
    return 


# create JSON message (first create obj dict and then convert to a JSON message)
def convert_defined_keys_to_JSON_msg(defined_key, buffered, jsondate, deviceid):

    jsonobj = {
        "device"   : deviceid,
        "time"     : jsondate,
        "buffered" : buffered,
        "values"   : {}
    }

    for key in defined_key :
        jsonobj["values"][key] = defined_key[key]

    jsonmsg = json.dumps(jsonobj)
    return jsonmsg


def convert_defined_keys_to_str(defined_key, record_dict):
    
    all_keys_str = "\n"
    for key in defined_key :
        key_str = key.ljust(30) 
        
        try: # if a divide factor was defined, use it
            keydivide = record_dict[key]["divide"]
        except: # otherwise use 1
            keydivide = 1

        if type(defined_key[key]) != type(str()) and keydivide != 1 :
            value_str = "{:.1f}".format(defined_key[key] / keydivide)
        else :
            value_str = str(defined_key[key])
        
        all_keys_str += key_str + " : " + value_str + "\n"

    return all_keys_str


def is_smart_meter(conf, recordtype: bytes) -> bool:
    
    return True if recordtype in conf.smartmeterrec else False


def is_inverter(conf, recordtype: bytes) -> bool:
    
    return True if recordtype in conf.datarec else False


def is_inverter_or_smart_meter(conf, recordtype: bytes) -> bool:
    
    return True if is_smart_meter(conf, recordtype) or \
                   is_inverter   (conf, recordtype) else False

def is_not_inverter_or_smart_meter(conf, recordtype: bytes) -> bool:
    
    return not is_inverter_or_smart_meter(conf, recordtype)


# this dictionary defines all known commands, aka record or functions
known_commands = {
#    cmd name                    :  int # hex: description
    "read_holding_registers"     :  3,  # x03: read holding registers
    "read_input_registers"       :  4,  # x04: read input registers 
    "preset_single_register"     :  6,  # x06: preset single register
    "preset_multiple_registers"  : 16,  # x10: preset multiple registers
    "ping"                       : 22,  # x16: shows if communication is workinmg
    "ServerCmd"                  : 24,  # x18: command originating from a Growatt server
    "Datalogger"                 : 25,  # x19: get and set datalogger parameters
    "smart_meter1"               : 27,  # x1b: for smart meter
    "smart_meter2"               : 30,  # x1e: for smart meter 
    "get_sm_values"              : 32,  # x20: request to receive smart meter measurements
    "MID_series"                 : 55,  # x37: occurs for MID 25KTL3-XH inverter 
    "unknown"                    : 56,  # x38: occurs for MID 25KTL3-XH inverter
    "acknowledge"                : 80,  # x50: historical buffered record type
}


def get_command_value(string):
    
    for (cmd_name, cmd_value) in known_commands.items() :
        if(cmd_name == string) :
            return cmd_value

    return "unknown"


def get_command_name(command):
    
    for (cmd_name, cmd_value) in known_commands.items() :
        if(cmd_value == command) :
            return cmd_name

    return "unknown"


# this function returns a dictionary with all known growatt communication protocols
def get_known_protocols():
    
    protocols = {
    #    protocol    : int # hex: description
        "protocol_0" :  0, #  00: ALO02 
        "protocol_2" :  2, #  02: ALO02, payload unencrypted no checksum
        "protocol_5" :  5, #  05: ALO05, payload encrypted and Checksum 
        "protocol_6" :  6, #  06: ALO06, payload encrypted and Checksum 
    }
    return protocols


# checks if a message has a CRC or not
# all protocols except protocol 2 use a CRC
def msg_has_crc(protocol) -> bool :
    if protocol != 2 : return True
    else             : return False


# checks if a message is encrypted
# protocols 5 and 6 are encrypted and also use CRC
def msg_is_encrypted(protocol) -> bool :
    if protocol in (5, 6) : return True
    else                  : return False


# function checks if a given record number corresponds to a buffered record
def is_buffered_record(cmd: bytes) -> bool:
    if(cmd == 80) : return True
    else          : return False


# \todo this function should better be called from extract_record_from_datastream
def detect_layout(msg, conf, inverter_type = "default") -> str:
    "Detect the layout to find the mapping"

    layout = msg["layout"]
    
    # if this is a shine X box append X to the layout
    LENGTH_LIMIT = 375 # SN: describe what this limit is about, I assume it is an empirical limit to differentiate data messages from control messages
    if msg["len"] > LENGTH_LIMIT and (msg["cmd"] not in conf.smartmeterrec):
        layout += "X"

    # no invtype added to layout for smart meter records
    if (inverter_type != "default") and not is_smart_meter(conf, msg["cmd"]) :
        layout += inverter_type.upper()

    msg["layout"] = layout
    return layout


""" validata data record on length and CRC"""
# This function takes the byte stream received from a socket and tries to
# interpret it as a Modbus RTU message
# If a valid message is found it will be separated into its parts and
# returned as as dictionary.
#
# returns 
# 1. the number of bytes that have been processed from the provided input data stream
# 2. a dictionary with the decoded message
def extract_record_from_datastream(in_data: bytes):
    # 
    # A message for a Growatt inverter is structured as follows
    # this structure is derived from Modbus RTU communication
    # specifically MODBUS TCP/IP ADU/Modbus TCP frame format is used
    # https://en.wikipedia.org/wiki/Modbus
    # 
    # 1.  Header   8 bytes (
    # 2. Payload  variable size
    # 3. Optional Checksum 2 bytes at end of data
    # 
    # The header consists of
    # transaction ID 2 bytes usually 0
    # protocol       2 byte big endian format
    # data length 2 bytes big endian format, length of data including optional checksum
    # Device Adress  1 byte, 0 = broadcast address, 1..254 = individual devices starting with 1
    # Command        1 byte  aka as function
    #
    # In modbus Device Id and Command are counted as part of the data. 
    # Thus modus defines a 6 bytes long header
    #
    # The format of the data depends on the command 
    # its length an content need to be determined for every command individually
    # 
    # All protocols except protocol 2 use a CRC
    # The CRC is a 16bit modbus CRC
    # It is calculated over the header and the data and then 
    # added at the end of the message
    
    in_data_len = len(in_data)
    
    # A data stream shorter than 8 bytes is no valid Modbus message.
    # This should not happen during normal operation, but might happen
    # if an error occured during data reception. It will also happen
    # during debugging or when intentionally testing the code with
    # invalid data e.g. during unit test.
    INVALID_MSG = { "valid" : False, "len" : 0, "dat_len" : 0 }
    MIN_PROCESSABLE_MESSAGE_LEN = 8
    if(in_data_len < MIN_PROCESSABLE_MESSAGE_LEN) : 
        return (0, INVALID_MSG)

    # extract some information from message header
    # Modbus defines a 6 bytes long header
    HEADER_LEN   = 6
    transaction  = int.from_bytes(in_data[0:2], "big") # currently this is never used, but it might be helpful for some analysis
    protocol     = int.from_bytes(in_data[2:4], "big") # protocol version used for the message
    anounced_len = int.from_bytes(in_data[4:6], "big") # number of bytes the payload data (without header and CRC) is long according to the header
    
    # Modbus defines data from byte 7 to the end as payload
    device_no  = in_data[6] # this is the first byte of the payload
    cmd        = in_data[7] # this is the second byte of the payload
    record_num = "{:02x}{:02x}".format(device_no, cmd)

    # if no CRC is present set default values for it
    # a message without CRC is considered having a valid CRC
    crc_len   = 0
    crc       = 0
    crc_valid = True

    # check CRC if it is present
    if msg_has_crc(protocol) :
        crc_len   = 2
        crc_start = HEADER_LEN + anounced_len # CRC starts after the message payload
        crc_end   = crc_start  + crc_len
        crc       = int.from_bytes(in_data[crc_start : crc_end  ], "big")
        crc_calc  = modbus_crc(    in_data[0         : crc_start])
        crc_valid = True if (crc == crc_calc) else False
        
    msg_length = HEADER_LEN + anounced_len + crc_len
    if(msg_length > in_data_len) :
        # the available data from the input stream is less than the message length,
        # return now and check the data stream again when more data was received. 
        # This also implies that the CRC is wrong. 
        return (0, INVALID_MSG)
    
    # If the CRC is wrong but the message is completely present in the input data
    # stream, this means the message was corrupted. In this case we cannot 
    # handle the corrupt message. Therefore it is marked as invalide, but the
    # processed bytes are returned for the corrupt message so it gets removed
    # from the input message buffer 

    decrypted_bin = ""
    if crc_valid :
        if msg_is_encrypted(protocol) : 
            decrypted_bin = decrypt_as_bin(in_data[0 : in_data_len - crc_len], 8)
        else :
            decrypted_bin =               (in_data[0 : in_data_len - crc_len])
    decrypted_str = convertBin2Str(decrypted_bin)

    # \todo better store message as binary instead of dat_str
    # \todo might be better to store only payload data in dat_str without header
    # currently this is not possible as position values are calculated including
    # the header and changing all positions and offsets would be a lot of work
    message = {
        "seq_num"       : transaction,   # counter for consecutive transaction like pings
        "protocol"      : protocol,      # protocol identifier
        "cmd_name"      : get_command_name(cmd),
        "len"           : msg_length,    # length of the message including header and CRC
        "dat_len"       : anounced_len,  # length of data only, thus message len - 6byte header - 2byte CRC
        "device_no"     : device_no,     # the modbus device the message is related to
        "cmd"           : cmd,           # record type aka command
        "record_num"    : record_num,    # to ease later code
        "crc_len"       : crc_len,       # for Modbus this is always 2bytes
        "crc"           : crc,           # checksum the modbus message had at its end
        "valid"         : crc_valid,     # indicates that the dictionary holds a valid Modbus message
        "dat_bin"       : decrypted_bin, # decrypted message including header but without CRC as binary stream
        "dat_str"       : decrypted_str, # decrypted message including header but without CRC as hex string
        "payload_bin"   : decrypted_bin[1*(HEADER_LEN+2) : ], # decrypted payload as binary stream
        "payload_str"   : decrypted_str[2*(HEADER_LEN+2) : ], # decrypted payload as hex string
        "layout"        : "T{:02x}{}".format(protocol, record_num),
        "rec_time"      : datetime.now().replace(microsecond=0).isoformat(), # time when the message was received 
        #"header"       : convertBin2Str(in_data[0:8]) # \todo remove later
    }
    
    dat_str_len     = len(decrypted_str)
    payload_str_len = len(message["payload_str"]) 
    
    return (msg_length, message)


def AutoCreateLayout(conf, msg) :
    """ Auto generate layout definitions from data record """
    # Currently three types of layout descriptions are known:
    # - "Clasic" inverters (eg. 1500-S) for Grott
    # - "New type" Inverters  (TL-X, TL3, MAD, MIX, MAX, MIX, SPA, SPH )
    # - "SPF" Inverters, not yet covered in the AutoCreateLayout, while detection interferes with Classic type detection.
    
    # do not process ack records
    if msg["len"] < conf.mindatarec : # SN what is different between mindatarec=12 and minrecl=8(100)
        return "none"

    # create standard layout
    layout = detect_layout(msg, conf)

    msg_data_str = msg["dat_str"]

    if msg["cmd"] in conf.datarec: # for data records create or select layout definition
        inverter_type = conf.invtype.upper()
        if inverter_type == "DEFAULT" :
            logger.debug("determine invertype")
            # is invtypemap defined (map typeing multiple inverters) ?
            if any(conf.invtypemap) :
                logger.debug("invtypemap defined: %s", conf.invtypemap)
                # process invetermap defined:
                serialloc = 36
                if msg["protocol"] == 6 :
                    serialloc = 76
                try:
                    inverter_serial = codecs.decode(msg_data_str[serialloc:serialloc+20], "hex").decode('ASCII')
                    try:
                        inverter_type = conf.invtypemap[inverter_serial].upper()
                        logger.debug("Inverter serial: {0}     found in inv_type_map - using inverter type {1}".format(inverter_serial, inverter_type))
                    except:
                        logger.debug("Inverter serial: {0} not found in inv_type_map - using inverter type {1}".format(inverter_serial, inverter_type))
                except:
                    logger.critical("error in inverter_serial retrieval, try without invertypemap")

        if inverter_type == "AUTO" :
            register_group = {}
            
            init_layout = "ALO02" if msg["protocol"] in (0, 2) else "ALO{:02x}".format(msg["protocol"])

            # Decode Serial number
            start  =           conf.alodict[init_layout]["pvserial"]["value"]
            end    = start + 2*conf.alodict[init_layout]["pvserial"]["length"] # *2 because data is in hex string form
            sn_hex = msg_data_str[start : end]
            layout = codecs.decode(sn_hex, "hex").decode('utf-8')

            if hasattr(conf.recorddict, layout): # if layout exists, use it ...
                logger.debug("layout %s exists and will be used", layout)
                return layout
            else : # ... otherwise, create the missing layout
                logger.debug("create layout %s named after device's serial number", layout)
                conf.recorddict[layout] = {}

            logger.debug("layout %s is based on scheme: %s", layout, init_layout)
            for keyword in conf.alodict[init_layout] :
                conf.recorddict[layout][keyword] =         conf.alodict[init_layout][keyword]
                logger.debug("{0:20}: {1}".format(keyword, conf.recorddict[layout][keyword]))

            # Determine register groups used in datarecord 
            MAX_NUM_GROUPS = 5 # max 5 groups, as no layout has more than 5 register groups
            register_group = {}
            grouploc = conf.recorddict[layout]["datastart"]["value"] # get group start from base layout
            for group in range(MAX_NUM_GROUPS) : 
                groupstart = msg_data_str[grouploc     : grouploc + 4] # start addr is 2 bytes long
                groupend   = msg_data_str[grouploc + 4 : grouploc + 8] # end   addr is 2 bytes long
                g_start    = int(groupstart, 16)       
                g_end      = int(groupend,   16)
                
                register_group[group] = { 
                    "start"    : g_start, 
                    "end"      : g_end, 
                    "grouploc" : grouploc
                }
                grouploc = grouploc + 8 + (g_end - g_start +1) * 4 # calculate next group start location (if any)
                
                logger.debug("Detected register group {0}, values: {1}".format(group, register_group[group]))
                
                # is this the end of the record
                if grouploc >= msg["len"]*2 - 4: # *2 as we work with string -4 as we ignore CRC at the end
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
            if register_group[0]["end"] < 45 : layoutversion = "V1"

            for group in register_group :

                grplayout = "ALO_"+str(register_group[group]["start"])+"_"+str(register_group[group]["end"]) + layoutversion
                grouploc  =            register_group[group]["grouploc"]

                logger.debug("process layout file: %s, groupstart location: %s", grplayout, register_group[group]["grouploc"])

                try:
                    test = conf.alodict[grplayout]
                except:
                    logger.warning("layout %s does not exist, ignoring record", grplayout)
                    break

                for keyword in conf.alodict[grplayout] :

                    conf.recorddict[layout][keyword] = conf.alodict[grplayout][keyword]
                    # calculate offset value and add/override in layout file.
                    keyloc = grouploc + 8 + ((conf.alodict[grplayout][keyword]["register"])-register_group[group]["start"])*4
                    conf.recorddict[layout][keyword]["value"] = keyloc

                    # format debug
                    #logger.debug("{0:20}: {1}".format(keyword, conf.recorddict[layout][keyword]))


        if inverter_type.upper() not in ("DEFAULT", "AUTO") and msg["cmd"] not in conf.smartmeterrec :
            layout = layout + inverter_type.upper()

        logger.debug("Created automatic layout : %s", layout)
        
    try: # if record dictionary provides a layout that fits to the message
        test = conf.recorddict[layout]
        
    except:
        logger.debug("no specified layout matches record: {0}=x{0:02x}, try generic layout".format(msg["cmd"]))
        
        if is_inverter(conf, msg["cmd"]) :
            device_and_record_str = "{:02x}{:02x}".format(msg["device_no"], msg["cmd"])
            layout                = layout.replace(device_and_record_str, "NNNN")
            
            try: # if a generic record layout exists?
                test = conf.recorddict[layout]
            except:
                # no valid record fall back on old processing?
                logger.debug("no matching generic inverter record layout found")
                layout = "none"

        if is_smart_meter(conf, msg["cmd"]) :
            deviceno_str = "{:02x}".format(msg["device_no"])
            layout       = layout.replace(deviceno_str, "NN")

            try: # if ageneric record layout exists?
                test = conf.recorddict[layout]
            except:
                # no valid record
                logger.debug("no matching generic smart meter record layout found")
                layout = "none"

    return layout


def interprete_msg(conf, msg):
    
    logger.setLevel(conf.loglevel.upper()) # without this no logging occurs in this file
    
    if msg['len'] <= conf.minrecl : 
        logger.debug("Message is shorter than minimum required record length, ignore it")
        return

    decode_ping_message        (msg)
    decode_get_sm_value_message(msg)
    decode_Datalogger_message  (msg)

    # Create layout that fits to the received message
    layout      = AutoCreateLayout(conf, msg)
    conf.layout = layout # save layout in conf to being passed to extension

    # if length < 12 it is a data ack record or no layout record is available
    if is_not_inverter_or_smart_meter(conf, msg["cmd"]) or conf.layout == "none":
        if conf.store_unknown_records == True : # store all found unknown records to analyse them later
            FILENAME_HEX = "unknown_records.hex" 
            write_Dict2file(FILENAME_HEX, msg)
        
        if msg["cmd"] not in (3, 4, 22, 24, 25, 32, 55, 56, 80) : # log only protocols I did not find yet
            logger.debug("Ignore record %s as there is no matching layout (yet)", msg["cmd"])
        return

    logger.debug("processing new layout: %s", layout)
    dat_str = msg["dat_str"]

    try:
        # try if log_start and log fields are defined, if yes prepare log fields
        log_start = conf.recorddict[layout]["log_start"]["value"]
        log_dict  = {}
        log_dict  = bytes.fromhex(dat_str[log_start : len(dat_str)-4]).decode("ASCII").split(",")
    except:
        pass

    defined_key = {} # define dictonary for key values
 
    # log data record processing (SDM630 smart monitor with railog)
    for keyword in conf.recorddict[layout].keys() :

        if keyword not in ("decrypt", "date", "log_start", "device") :
            
            # try if keyword should be included
            include = True
            try: # check if keytype was correctly specified
                if conf.recorddict[layout][keyword]["incl"] == "no" :
                    include = False
            except: # no include statement keyword should be processed, set include to prevent exception
                include = True
                
            # process only keywords needed to be included (default):
            try:
                if ((include) or (conf.includeall)):
                    try:    # if key has a keytype defined, use it ...
                        keytype = conf.recorddict[layout][keyword]["type"]
                    except: # ... otherwise use num as default
                        keytype = "num"
                        
                    if keytype == "text" :
                        defined_key[keyword] = dat_str[conf.recorddict[layout][keyword]["value"]:conf.recorddict[layout][keyword]["value"]+(conf.recorddict[layout][keyword]["length"]*2)]
                        defined_key[keyword] = codecs.decode(defined_key[keyword], "hex").decode('utf-8')
                        
                    elif keytype == "num" :
                        defined_key[keyword] = int(dat_str[conf.recorddict[layout][keyword]["value"]:conf.recorddict[layout][keyword]["value"]+(conf.recorddict[layout][keyword]["length"]*2)],16)
                    
                    elif keytype == "numx" : # process signed integer
                        keybytes = bytes.fromhex(dat_str[conf.recorddict[layout][keyword]["value"]:conf.recorddict[layout][keyword]["value"]+(conf.recorddict[layout][keyword]["length"]*2)])
                        defined_key[keyword] = int.from_bytes(keybytes, byteorder='big', signed=True)
                        
                    elif keytype == "log" : # process log fields
                        defined_key[keyword] = log_dict[conf.recorddict[layout][keyword]["pos"]-1]
                        
                    elif keytype == "logpos" : # Process log fields, only display this field if positive
                        if float(log_dict[conf.recorddict[layout][keyword]["pos"]-1]) > 0 :
                            defined_key[keyword] = log_dict[conf.recorddict[layout][keyword]["pos"]-1]
                        else : 
                            defined_key[keyword] = 0
                        
                    elif keytype == "logneg" : # Process log fields, only display this field if negative
                        if float(log_dict[conf.recorddict[layout][keyword]["pos"]-1]) < 0 :
                            defined_key[keyword] = log_dict[conf.recorddict[layout][keyword]["pos"]-1]
                        else : 
                            defined_key[keyword] = 0
            except:
                logger.debug("error in keyword processing: %s", keyword + ", data processing stopped")
    
    device_defined = False
    try: # if "device" was defined in recorddictionary use it ...
        defined_key["device"] = conf.recorddict[layout]["device"]["value"]
        device_defined = True
    except:
        try: # ... otherwise use serial if it was defined ...
            test = defined_key["pvserial"]
        except:  # ... and if not assign inverterid from config as serial number
            defined_key["pvserial"] = conf.inverterid
            conf.recorddict[layout]["pvserial"] = {"value" : 0, "type" : "text"}
            logger.debug("pvserial not found and device not specified used configuration defined invertid:", defined_key["pvserial"] )

    try: # if dateoffset was specified in layout use it ...
        dateoffset = int(conf.recorddict[layout]["date"]["value"]) # SN: value should be renamed to offset
    except: # ... otherwise set dateoffset to zero, which means no dateoffset value is available
        dateoffset = 0

    # process date value if specifed
    buffered = "yes" if is_buffered_record(msg["cmd"]) else "no" # \todo SN: change to bool
    
    if dateoffset > 0 and (conf.gtime != "server" or buffered == "yes"):
        logger.debug("processing date/time values extracted from received message")
        pvdate = create_PV_date_time_str(dat_str, dateoffset)
        
        try: # test if the extracted date/time fit in the expected format
            testdate = datetime.strptime(pvdate, "%Y-%m-%dT%H:%M:%S")
            jsondate = pvdate
            logger.debug("date-time: %s", jsondate)

            # \todo check if time from inverter is close to server time
            time_from_server = False # Indicate date/time is not from server but from received message

        except Exception as e : # Date could not be parsed - either the format is wrong or its not a valid date
            logger.debug("Error %s: invalid time/date found in message, use server time instead", e)
            jsondate         = datetime.now().replace(microsecond=0).isoformat()
            time_from_server = True
    else :
        logger.debug("server date/time used")
        jsondate         = datetime.now().replace(microsecond=0).isoformat()
        time_from_server = True

    # create a string with all values of a data message
    all_keys_str = convert_defined_keys_to_str(defined_key, conf.recorddict[layout])
    logger.debug(all_keys_str)
    
    # if device is not specified in layout, record datalogserial is used as device (to distinguish record from inverter record)
    if device_defined == True:                    device_str = defined_key["device"]
    else :
        if msg["cmd"] not in conf.smartmeterrec : device_str = defined_key["pvserial"]
        else :                                    device_str = defined_key["datalogserial"]
    
    # only process records of type 0120 if they have a voltage in the range of 0 .. 500V
    if msg["cmd"] == 32 :
        real_voltage = defined_key["voltage_l1"]/10
        if (real_voltage > 500) or (real_voltage < 0) :
            logger.warning("invalid 0120 record processing stopped")
            return
    
    jsonmsg = convert_defined_keys_to_JSON_msg(defined_key, buffered, jsondate, device_str)
    logger.debug(jsonmsg)

    # do not process buffered records with time from server) 
    # or buffered records if sendbuf = False
    if (buffered == "yes") :
        if (conf.sendbuf == False) or (time_from_server == True) :
            logger.debug("Buffered record not sent because sendbuf == False or invalid date/time format")
            return

    if conf.nomqtt != True: mqtt_processing(conf, msg, jsonmsg,     device_str)
    if conf.pvoutput:  processPVOutput     (conf, msg, defined_key, jsondate)
    if conf.influx:    influx_processing   (conf, msg, defined_key, jsondate)
    if conf.extension: extension_processing(conf)
