import unittest
import grottproxy


# Unit Tests for modul grottproxy.py


class TestGrottProxy(unittest.TestCase):
        
    def test_validate_record_msg_02_wrong_length(self):
        data_in_bytes  =  b'\x00=\x00\x02\x00 \x00\x16\x1f5+A"2@u%YwattGrowattGrowattGr\xe3\xfd'
        data_as_string = "".join("{:02x}".format(n) for n in data_in_bytes)
        self.assertEqual(grottproxy.validate_record(data_as_string), (8, 'data record has invalid length')) 
        
        
    def test_validate_record_correct_msg_02(self):
        data_in_bytes  =  b'\x00=\x00\x02\x00 \x00\x16\x1f5+A"2@u%YwattGrowattGrowattGr'
        data_as_string = "".join("{:02x}".format(n) for n in data_in_bytes)
        self.assertEqual(grottproxy.validate_record(data_as_string), (0, 'ok'))
        
        
    def test_validate_record_correct_msg_05(self):
        data_in_bytes  =  b'\x00=\x00\x05\x00 \x00\x16\x1f5+A"2@u%YwattGrowattGrowattGr\x4f\x8b'
        data_as_string = "".join("{:02x}".format(n) for n in data_in_bytes)
        self.assertEqual(grottproxy.validate_record(data_as_string), (0, 'ok')) 
        
        
    def test_validate_record_correct_msg_06(self):
        data_in_bytes  =  b'\x00=\x00\x06\x00 \x01\x16\x1f5+A"2@u%YwattGrowattGrowattGr\xe3\xfd'
        data_as_string = "".join("{:02x}".format(n) for n in data_in_bytes)
        self.assertEqual(grottproxy.validate_record(data_as_string), (0, "ok")) 
        
        
    def test_validate_record_wrong_crc(self):
        data_in_bytes  =  b'\x00=\x00\x06\x00 \x01\x16\x1f5+A"2@u%YwattGrowattGrowattGr\xe3\xff'
        data_as_string = "".join("{:02x}".format(n) for n in data_in_bytes)
        self.assertEqual(grottproxy.validate_record(data_as_string), (8, 'data record has invalid crc')) 
        
        
    # real message received from Growatt
    #     - <socket.socket fd=7, family=2, type=1, proto=0, laddr=('192.168.178.192', 52700), raddr=('8.209.71.240', 5279)>
    #data_bin = b'\x00\x08\x00\x06\x00 \x01\x16\x1f5+A"2@u%YwattGrowattGrowattGr\xb1\xf3'
    #data_str = "00080006002001161f352b412232407525597761747447726f7761747447726f776174744772b1f3"
    
    # \todo more tests should be added to test all modules of the grottproxy.py file
        
        

if __name__ == '__main__':
    unittest.main()