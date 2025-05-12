"""Grott Growatt monitor :  Proxy """
# Updated: 2024-10-27
# Version 3.0.0
import logging
import socket
import select
import time
import sys
from utils     import decrypt, format_multi_line, validate_record
from grottdata import process_data

vrmproxy = "3.0.0"

# to resolve errno 32: broken pipe issue (only linux)
if sys.platform != 'win32' :
    from signal import signal, SIGPIPE, SIG_DFL

#set logging definities
logger = logging.getLogger(__name__)

# By changing the buffer_size and delay, you can improve the speed and bandwidth.
# But when the buffer size gets too high or the delay goes too small, you can brake things
buffer_size = 4096
#buffer_size = 65535
delay = 0.0002


def decode_header(header_str):
    header_len = len(header_str)

    unknown1 = header_str[ 0: 2]
    unknown2 = header_str[ 2: 4]
    unknown3 = header_str[ 4: 6]
    protocol = header_str[ 6: 8]
    data_len = header_str[ 8:12]
    device   = header_str[12:14]
    rec_type = header_str[14:16] # aka command
    
    print("header   : ", header_str)
    print("unknown1 : ", unknown1)
    print("unknown2 : ", unknown2)
    print("unknown3 : ", unknown3)
    print("protocol : ", protocol)
    print("data_len : ", data_len)
    print("device   : ", device)
    print("rec_type : ", rec_type)
    return 0


""""DEFINE FORWARD CONNECTION"""
class Forward:

    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        """start forward connection"""
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception as e:
            logger.critical("Proxy forward error : %s", e)
            return False


"""Proxy main class"""
class Proxy:
    
    input_list = []
    channel    = {}


    def __init__(self, conf):

        logger.setLevel(conf.loglevel.upper())
        conf.vrmproxy = vrmproxy
        logger.info("Grott proxy mode started, version: %s", conf.vrmproxy)

        ## to resolve errno 32: broken pipe issue (Linux only)
        if sys.platform != 'win32':
            signal(SIGPIPE, SIG_DFL)
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # set default grottip address
        if conf.grottip == "default" :
            conf.grottip = '0.0.0.0'
        self.server.bind((conf.grottip, conf.grottport))
        #socket.gethostbyname(socket.gethostname())
        try:
            hostname = socket.gethostname()
            logger.info("\t - Hostname : %s", hostname)
            testip = socket.gethostbyname(hostname)
            logger.info("\t - IP : {0}, port : {1}".format(testip, conf.grottport))
        except Exception as e:
            logger.warning("IP and port information not available: %s",e)

        self.server.listen(200)
        self.forward_to = (conf.growattip, conf.growattport)


    """proxy main routine"""
    def main(self,conf):

        self.input_list.append(self.server)
        while 1:
            time.sleep(delay) # \todo better run code triggered by interrupt
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for self.s in inputready:
                if self.s == self.server:
                    self.open_connection()
                    break
                try:
                    # read buffer until empty
                    msg_buffer = b''
                    while True:
                        part = self.s.recv(buffer_size)
                        msg_buffer += part
                        if len(part) < buffer_size:
                        # either 0 or end of data
                            break
                    #self.data, self.addr = self.s.recvfrom(buffer_size)
                except Exception as e:
                    logger.warning("Connection error: %s", e)
                    logger.debug("Socket info:\n\t %s", self.s)
                    self.close_connection()
                    break
                
                if len(msg_buffer) == 0:
                    self.close_connection()
                    break
                else:
                    # split buffer if contain multiple records
                    self.header      = "".join("{:02x}".format(n) for n in msg_buffer[0:8])
                    self.protocol    = self.header[6:8]
                    self.data_length = int(self.header[8:12], 16)
                    #rec_length      = int.from_bytes(msg_buffer[4:6], "big")
                    buf_length       = len(msg_buffer)
                    #total rec_length is datarec + buffer (+ crc)
                    if self.protocol in ("05", "06"):
                        rec_length = self.data_length + 8
                    else :
                        rec_length = self.data_length + 6
                    while rec_length <= buf_length:
                        logger.debugv("Received buffer:\n{0} \n".format(format_multi_line("\t", msg_buffer, 120)))
                        self.data = msg_buffer[0:rec_length]
                        self.process_received_data(conf)
                        if buf_length > rec_length :
                            logger.debug("handle_readble_socket, Multiple records in buffer, process next message in buffer")
                            msg_buffer       = msg_buffer[rec_length : buf_length]
                            self.header      = "".join("{:02x}".format(n) for n in msg_buffer[0:8])
                            self.protocol    = self.header[6:8]
                            self.data_length = int(self.header[8:12],16)
                            
                            if self.protocol in ("05", "06"):
                                rec_length = self.data_length + 8
                            else :
                                rec_length = self.data_length + 6
                            buf_length = len(msg_buffer)
                        else: break


    """accept new connection"""
    def open_connection(self):

        forward = Forward().start(self.forward_to[0], self.forward_to[1])
        clientsock, clientaddr = self.server.accept()
        if forward:
            logger.info("Client connection from: %s", clientaddr)
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward]    = clientsock
        else:
            logger.warning("can't establish connection with remote server")
            logger.warning("closing connection with client side: %s", clientaddr)
            clientsock.close()


    """close connection"""
    def close_connection(self):

        logger.info("Close connection requested for: %s",self.s)
        # try / except to resolve errno 107: Transport endpoint is not connected
        try:
            logger.info("{0} disconnected".format(self.s.getpeername()))
        except:
            logger.info("Peer already disconnected")

        # remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        
        # close the connection with remote server
        self.channel[self.s].close()
        
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]


    """process received data"""
    def process_received_data(self, conf):
        
        data_bin = self.data # create local copy of received data
        logger.debug(" - %s", self.channel[self.s]) # show socket where data_bin originates from
        
        # test if record is not corrupted
        record_valid  = validate_record(data_bin)
        if record_valid == False :
            logger.warning("invalid data_bin record received")
            logger.debugv("original data_bin:\n{0} \n".format(format_multi_line("\t", self.data, 120)))
            return
        
        # FILTER Detect if configure data_bin is sent
        if conf.blockcmd :
            # by default all received commands are blocked
            logger.debug("checking if received command is to be blocked")
            blockflag = True
            
            # partly block configure Shine commands
            cmd = self.header[14:16]
            if cmd == "18" :
                if conf.blockcmd :
                    if self.protocol == "05" or self.protocol == "06" :
                        confdata = decrypt(data_bin)
                    else :  confdata = data_bin
                    
                    # get conf command (location depends on record type), maybe later more flexibility is needed
                    if self.protocol == "06" :
                        conf_cmd = confdata[76:80]
                    else:
                        conf_cmd = confdata[36:40]
                    #
                    if self.header[14:16] == "18" :
                        # do not block if configure time command of configure IP (if noipf flag set)
                        logger.debug("Datalogger Configure command detected")
                        if conf_cmd == "001f" or (conf_cmd == "0011" and conf.noipf) :
                            blockflag = False
                            if conf_cmd == "001f": conf_cmd = "Time"
                            if conf_cmd == "0011": conf_cmd = "Change IP"
                            logger.info("Datalogger configure command not blocked : %s ", conf_cmd)
                    else :
                        # All configure inverter commands will be blocked
                        logger.debug("Inverter Configure command detected")
                        
            # allow records
            record_num = self.header[12:16] # 12-13 deviveno 14-15 recordtype
            if self.header[12:16] in conf.recwl :
                blockflag = False
                logger.info("record forwarded, as it is whitelisted: %s ", self.header[12:16])

            if blockflag :
                logger.info("record blocked: %s", self.header[12:16])
                if self.protocol == "05" or self.protocol == "06" :
                    blockeddata = decrypt(data_bin)
                else :  
                    blockeddata = data_bin
                logger.debugv("\n{0} \n".format(format_multi_line("\t", blockeddata, 120)))
                return

        # send message to inverter
        self.channel[self.s].send(data_bin) # forward message to inverter and ...
        if len(data_bin) > conf.minrecl :
            process_data(conf, data_bin)    # ... decode the message for local processing
        else:
            logger.debug("Data less than minimum record length, data_bin not processed")
