
import logging
import textwrap
from itertools import cycle

from crc import modbus_crc

logger = logging.getLogger(__name__)


def to_hexstring(data):
    return "".join("\\x{:02x}".format(n) for n in data)


def decrypt(encrypted_binary_data):
    decrypted_binary_data = crypt(encrypted_binary_data)
    decrypted_string = "".join("{:02x}".format(n) for n in decrypted_binary_data)
    return decrypted_string


def encrypt(decrypted_binary_data):
    encrypted_binary_data = crypt(decrypted_binary_data)
    encrypted_string = "".join("{:02x}".format(n) for n in encrypted_binary_data)
    return encrypted_string


#def crypt(encrypted_binary_data):
def crypt(encrypted_binary_data: bytes):
    len_data = len(encrypted_binary_data)

    # the leading 8 bytes are unencrypted
    # those bytes are used as header
    NUM_UNENCRYTED_BYTES = 8 
    num_encrypted_bytes  = len_data - NUM_UNENCRYTED_BYTES

    key2    = b"Growatt"
    key2_len = len(key2)
    
    KEY     = "Growatt"
    KEY_HEX = ['{:02x}'.format(ord(x)) for x in KEY]
    KEY_LEN = len(KEY_HEX)

    #decrypted = bytearray(decdata)

    decrypted_binary_data = list(encrypted_binary_data[0 : NUM_UNENCRYTED_BYTES])
        
    for i in range(0, num_encrypted_bytes) :
        j = i % KEY_LEN
        decrypted_byte = [encrypted_binary_data[i+8] ^ int(KEY_HEX[j], 16)]
        decrypted_binary_data += decrypted_byte

    return decrypted_binary_data


# encrypt / decrypt data.
def byte_decrypt(decdata: bytes):
    """
    Decrypt the encrypted growatt data,
    made at byte level for more efficient and simple code
    """
    # The xor key is always Growatt
    mask = b"Growatt"
    mask_len = len(mask)

    length_data = len(decdata)
    # The first 8 bytes are always not encrypted
    header_skip = 8

    # Create a bytearray to allow to modify the bytes without copy
    decrypted = bytearray(decdata)

    # Apply the xor until the end of the buffer, skipping the unecrypted header
    for idx in range(header_skip, length_data):
        # modulo allow to cycle in the XOR mask
        decrypted[idx] ^= mask[(idx - header_skip) % mask_len]

    # cast it to bytes
    decrypted = bytes(decrypted)

    return decrypted


def validate_record(data: bytes) -> bool:
    # validata data record on length and CRC (for "05" and "06" records)
    # The CRC is a modbus CRC
    #
    # the packet start with \x00\x0d\x00
    # Protocol byte is the fourth, ex: \x05 \x06 \x02
    # Length is the next to 2 bytes in big endian format
    # Next is data
    # The last 2 bytes if the protocol is not 2 is the CRC

    # Length of the data in bytes
    ldata = len(data)

    protocol = data[3]
    len_orgpayload = int.from_bytes(data[4:6], "big")
    print("header: {} - Data size: {}".format(to_hexstring(data[0:6]), ldata))
    print("\t\t- Protocol is: {}".format(protocol))
    print("\t\t- Length is: {} bytes".format(len_orgpayload))

    has_crc = False
    if protocol in (0x05, 0x06):
        has_crc = True
        # CRC is the last 2 bytes
        lcrc = 2
        crc = int.from_bytes(data[-lcrc:], "big")
    else:
        lcrc = 0

    # ldata - 6 bytes of header - crc length
    len_realpayload = ldata - 6 - lcrc

    if protocol != 0x02:
        crc_calc = modbus_crc(data[: ldata - 2])
        print("Calculated CRC: {}".format(crc_calc))

    if len_realpayload == len_orgpayload:
        returncc = True
        print("Data CRC: {} - Calculated: {}".format(crc, crc_calc))
        if protocol != 0x02 and crc != crc_calc:
            return False
    else:
        returncc = False

    return returncc


## convert a provided value to a boolean value
# 
#  If the provided value can be assigned to a boolean value the return
#  value is either True/False otherwise None
#
#  This is mainly used to convert external parameters to a boolean. 
#  This function may pose a security risk, as external parameters
#  could try to trigger an unwanted behaviour. 
#  
def convert2bool(defstr):
    """Convert provided input value to bool """
    
    # if the provided parameter is an integer, convert it while 
    # integer value == 0 is considered false 
    # all other integer values are considered true
    # if the provided parameter is a boolean, it remains a boolean
    if isinstance(defstr, (int)) : return defstr.__bool__()
    
    # if the provided parameter is a string, try to assign a suitable boolean
    string_to_test = defstr.lower()
    if string_to_test in ("true",  "yes", "y", "1") : return True 
    if string_to_test in ("false", "no",  "n", "0") : return False
    
    # if we get here no boolean value could be assigned
    # this applies for types other than integers/strings
    # strings with numbers other than 0 and 1 are assigned to None too
    return None


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def format_bytes(bytes_data):
    width = 16 * 3 + 3  # 3 char for HEX + space
    data = " ".join(r"{:02x}".format(byte) for byte in bytes_data)
    data = data.ljust(width)
    data += "".join([chr(x) if 32 <= x < 127 else "." for x in bytes_data])
    return data


def hex_dump(data, bytes_per_line=16):
    """Display a hex dump of binary data with both hex and ASCII representation."""
    result = []
    nl = '\n'

    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i+bytes_per_line]
        ## Create the hex representation
        hex_repr = ' '.join(r'{:02x}'.format(b) for b in chunk)

        ## Create the ASCII representation (printable chars only)
        ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        
        ## Format the line with address, hex values, and ASCII representation
        line = f"{i:04x}: {hex_repr:<{bytes_per_line*3}} {ascii_repr}"
        result.append(line)

    return '\n'.join(result)


# Formats multi-line data
def format_multi_line(prefix, string, size=80):
    size -= len(prefix)
    if isinstance(string, bytes):
        bytes_chuncks = chunks(string, 16)
        return "\n".join(
            [prefix + format_bytes(byte_chunk) for byte_chunk in bytes_chuncks]
        )
    return "\n".join([prefix + line for line in textwrap.wrap(string, size)])