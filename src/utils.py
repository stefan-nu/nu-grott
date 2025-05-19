
import textwrap


def write_structure_to_file(file_name, msg):
    
    with open(file_name, "a") as f:
        for key, value in msg.items():
            print('{0:>12}: {1:6}'.format(key, value), file=f)
        print(file=f) # terminate structure with a newline
    f.close()


def write_nested_structure_to_file(file_name, msg):
    
    with open(file_name, "a") as f:
        for key, nested in msg.items() :
            print(key, nested, file=f)
            for subkey, value in sorted(nested.items()):
                print('\t{}: {}'.format(subkey, value), file=f)
            print(file=f)
    f.close()


def to_hexstring(data):
    return "".join("\\x{:02x}".format(n) for n in data)


def convertBin2Str(data: bytes) :
    string = "".join("{:02x}".format(n) for n in data)
    return string


def decrypt_as_bin(encrypted_binary_data, start):
    return crypt(encrypted_binary_data, start)


def decrypt_as_str(encrypted_binary_data, start):
    decrypted_binary_data = decrypt_as_bin(encrypted_binary_data, start)
    return convertBin2Str(decrypted_binary_data)


def encrypt(decrypted_binary_data, start):
    encrypted_binary_data = crypt(decrypted_binary_data, start)
    return convertBin2Str(encrypted_binary_data)


def crypt(binary_data: bytes, start):

    KEY     = b"Growatt"
    KEY_LEN = len(KEY)

    len_data            = len(binary_data)
    num_uncrypted_bytes = len_data - start
    crypted_binary_data = list(binary_data[0 : start])
        
    for i in range(0, num_uncrypted_bytes) :
        j = i % KEY_LEN
        crypted_byte = [binary_data[i+start] ^ KEY[j]]
        crypted_binary_data += crypted_byte

    return crypted_binary_data


# encrypt / decrypt data.
def byte_decrypt(decdata: bytes):
    """
    Decrypt the encrypted growatt data,
    made at byte level for more efficient and simple code
    """
    # The xor key is always Growatt
    mask     = b"Growatt"
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


def hex_dump(data, bytes_per_line=16):
    """Display a hex dump of binary data with both hex and ASCII representation."""
    result = []

    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i+bytes_per_line]
        # Create the hex representation
        hex_repr = ' '.join(r'{:02x}'.format(b) for b in chunk)

        # Create the ASCII representation (printable chars only)
        ascii_repr = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        
        # Format the line with address, hex values, and ASCII representation
        line = f"{i:04x}: {hex_repr:<{bytes_per_line*3}} {ascii_repr}"
        result.append(line)

    return '\n'.join(result)


def format_bytes(bytes_data):
    width = 16 * 3 + 3  # 3 char for HEX + space
    data = " ".join(r"{:02x}".format(byte) for byte in bytes_data)
    data = data.ljust(width)
    data += "".join([chr(x) if 32 <= x < 127 else "." for x in bytes_data])
    return data


# Formats multi-line data
def format_multi_line(prefix, data, size = 80):
    size -= len(prefix)
    # formatting for byte stream
    if isinstance(data, bytes):
        bytes_chuncks = chunks(data, 16)
        return "\n".join([prefix + format_bytes(byte_chunk) for byte_chunk in bytes_chuncks])
    # formatting for text stream
    return     "\n".join([prefix + line                     for line       in textwrap.wrap(data, size)])