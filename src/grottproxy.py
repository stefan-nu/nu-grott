"""nu-grott Growatt monitor : Proxy mode """

from datetime  import datetime
import logging
import socket   # BSD socket interface: https://docs.python.org/3/library/socket.html
import select
import time
import sys
from utils     import decrypt_as_bin, hex_dump, to_hexstring, format_multi_line
from grottdata import interprete_msg, validate_record


vrmproxy = "3.0.0"

# to resolve errno 32: broken pipe issue (only linux)
if sys.platform != 'win32' :
    from signal import signal, SIGPIPE, SIG_DFL

logger = logging.getLogger(__name__)


""""DEFINE FORWARD CONNECTION"""
# forward refers to that received messages are forwarded to another server
# typically this is the growatt server the inverter would send its messages
# to if it were not interfered by nu-grott 
class Forward:

    def __init__(self): 
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        """start forward connection"""
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception as e:
            logger.critical("Failed connecting to forward server %s:%s\n Error: %s", host, port, e)
            return False


"""Proxy main class"""
class Proxy:
    
    input_list = []
    channel    = {}

    def __init__(self, conf):

        logger.setLevel(conf.loglevel.upper())
        conf.vrmproxy = vrmproxy
        logger.info("nu-grott proxy mode started, version: %s", conf.vrmproxy)

        # to resolve errno 32: broken pipe issue (Linux only)
        if sys.platform != 'win32':
            signal(SIGPIPE, SIG_DFL)
        
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # set default grottip address
        if conf.grottip == "default" :
            conf.grottip = '0.0.0.0'
            
        try:
            self.server.bind((conf.grottip, conf.grottport)) # SN: prevent crash if [Errno 48] Address already in use
            #socket.gethostbyname(socket.gethostname())
        except Exception as e:
            logger.error("Cannot bind to socket: %s", e)
            logger.info("Maybe another instance of nu-grott is already running")
            logger.info("exiting now")
            sys.exit(1)
            
        try:
            hostname = socket.gethostname()
            testip   = socket.gethostbyname(hostname)
            logger.info("running on: %s", hostname)
            logger.info("listening on IP: {0}, port: {1}".format(testip, conf.grottport))
        except Exception as e:
            logger.warning("IP and port information not available: %s", e)

        self.server.listen(200)
        self.forward_to = (conf.growattip, conf.growattport)


    """accept new connection"""
    def on_accept(self):

        # open a TCP connection to the Growatt server
        # typically server.growatt.com:5279
        # forward_to[0] = IP or hostname
        # forward_to[1] = Port
        forward = Forward().start(self.forward_to[0], self.forward_to[1])
        clientsock, clientaddr = self.server.accept()
        if forward:
            logger.info("client connected from: %s", clientaddr)
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward]    = clientsock
        else:
            logger.warning("can't establish connection with remote server")
            logger.warning("closing connection with client: %s", clientaddr)
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


    """proxy main routine"""
    def main(self, conf):

        # Currently data is polled from the socket. 
        # By changing the BUF_SIZE and DELAY_SEC, one can adjust the speed and bandwidth.
        # When the buffer size gets too big or the DELAY_SEC too small, the system gets starved
        # \todo change to interrupt based socket reading to keep the system load low
        BUF_SIZE  = 4096   # max number of bytes to read from socket in one read attempt
        DELAY_SEC = 0.1    # between two socket poll attempts

        self.input_list.append(self.server)
        
        while 1:
            time.sleep(DELAY_SEC) # \todo avoid polling, better run code triggered or use callback
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            
            # for every socket which has input data ready 
            # store the socket in self.s 
            # and start the data processing
            for self.s in inputready:
                
                # if our own server socket is ready, it means a client connection
                # was requested, thus accept the connection from the client, 
                # this will create a new socket which will be used for data 
                # reception later on
                if self.s == self.server: 
                    self.on_accept()
                    break
                
                try:
                    msg_buffer = b''
                    while True: # read buffer until empty
                        part = self.s.recv(BUF_SIZE)
                        msg_buffer += part
                        # part_len = len(part)
                        # if part_len == 0 : # no more data pending in input buffer
                        break          # continue with processing of the data
                        
                    #self.data, self.addr = self.s.recvfrom(BUF_SIZE)
                    
                except Exception as e:
                    logger.warning("Connection error: %s", e)
                    logger.debug  ("Socket info: %s", self.s)
                    
                    # if a connection error occured close the connection
                    # the client will open a new connection and the data
                    # reception will continue without the need to restart 
                    # the program 
                    self.close_connection()
                    break
                
                while len(msg_buffer) > 0 :
                                
                    # check the received data stream whether it contains a 
                    # valid message, if so extract the basic information that
                    # describe the message and store them in a dictionary to
                    # ease later processing of the message 
                    (processed_bytes, msg) = validate_record(msg_buffer)
                    
                    # filter out corrupt messages
                    # if the length is wrong this happens most likely if a
                    # socket read operation was performed in the middle of 
                    # a transmission. In this case the message can be fixed, by
                    # appending data that was received in the following socket
                    # read operation, this happens often if debugging is active
                    if msg['valid'] == False :
                        return
                    
                    if processed_bytes > 0 :
                    
                        msg.update({"from" : self.channel[self.s].getpeername()})
                    
                        # keep the unprocessed message to forward it later
                        self.data = msg_buffer[0 : processed_bytes] 
                        
                        # remove the processed message from the msg_buffer but keep 
                        # the remaining part of the buffer it might hold another 
                        # message or part of it 
                        msg_buffer = msg_buffer[processed_bytes:]
                        
                        #logger.info("\nReceived {} (={}) message, dat_len: {}, with sequence {} from: {} "\
                        #            .format(msg["cmd_name"],  msg["cmd"], msg["dat_len"], msg["seq_num"], self.channel[self.s].getpeername()))
                        #logger.debug("Socket: %s", self.channel[self.s]) 
                        
                        with open("messages_encrypted.txt", "a") as f:
                            print(msg["rec_time"]+": "+to_hexstring(msg_buffer[0:processed_bytes]), file=f)
                            print(file=f)
                        f.close()
                        
                        # with open("messages_decrypted.txt", "a") as f:
                        #     print(msg["rec_time"]+": "+to_hexstring(msg["dat_bin"]), file=f)
                        #     print(file=f)
                        # f.close()
                
                        block_message = self.is_blocked_msg(conf, msg)
                        
                        if block_message == False :
                            self.channel[self.s].send(self.data) # forward original (encrypted) message to inverter
                            interprete_msg(conf, msg) # and decode the message for local processing


    """check if the message needs to be blocked"""
    def is_blocked_msg(self, conf, msg) -> bool:

        if not conf.blockcmd : # if blocking is disabled all messages may pass
            return False
        
        else :  # if blocking is enabled, check if the current message 
                # shall be filtered out 
                
            if msg["cmd"] == 24 : # its a get configuration command
                pos = 76 if (msg["protocol"] == 6) else 36 # the location of the "get conf" command depends on the record type
                conf_cmd = msg["dat_str"][pos : pos+4]
                
                # configuration commands received from Growatt server 
                # are block except for 
                # - configure time commands 
                # - configure IP command if noipf flag is set
                logger.debug("configuration command {0} detected for device {1}".format(conf_cmd, msg["device_no"]))
                
                block_cmd = True
                if (conf_cmd == "001f") :
                    logger.info("its a \"Set Time\" command which is always forwarded")
                    block_cmd = False
                    
                elif (conf_cmd == "0011" and conf.noipf == False) :
                    logger.info("its a \"Change IP\" which is forwarded as noipf == False")
                    block_cmd = False
                
                return block_cmd

            # check if message is whitelisted
            if msg["record_num"] in conf.recwl :
                logger.info("command {0:2} to device {1} whitelisted: forward it".format(msg["cmd"], msg["device_no"]))
                return False

            # a message that is not whitelisted is considered blacklisted
            else :
                logger.info("command {0:2} to device {1} blacklisted: blocked it".format(msg["cmd"], msg["device_no"]))
                return True