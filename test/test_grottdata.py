

import unittest
import grottconf
from grottdata import msg_has_crc, msg_is_encrypted, extract_record_from_datastream, AutoCreateLayout

class TestGrottdataHelpers(unittest.TestCase):
    

    def test_msg_has_crc(self):

        result = msg_has_crc(0)
        self.assertEqual(result, True)
        
        result = msg_has_crc(2)
        self.assertEqual(result, False)
        
        result = msg_has_crc(5)
        self.assertEqual(result, True) 
        
        result = msg_has_crc(6)
        self.assertEqual(result, True) 
        
        
    def test_msg_is_encrypted(self):

        result = msg_is_encrypted(0)
        self.assertEqual(result, False)
        
        result = msg_is_encrypted(2)
        self.assertEqual(result, False)
        
        result = msg_is_encrypted(5)
        self.assertEqual(result, True) 
        
        result = msg_is_encrypted(6)
        self.assertEqual(result, True) 


class TestGrottdataExtract_record_from_datastream(unittest.TestCase):

    def test_validate_correct_record_without_crc(self):
        data = b'\x00=\x00\x02\x00 \x00\x16\x1f5+A"2@u%YwattGrowattGrowattGr'
        (processed_bytes, msg) = extract_record_from_datastream(data)
        self.assertEqual(msg["valid"], True) 
        self.assertEqual(processed_bytes, 38)


    def test_validate_correct_record_without_crc_but_crc_added_anyway(self):
        data = b'\x00=\x00\x02\x00 \x00\x16\x1f5+A"2@u%YwattGrowattGrowattGr\xe3\xfd'
        (processed_bytes, msg) = extract_record_from_datastream(data)
        self.assertEqual(msg["valid"], True)
        self.assertEqual(processed_bytes, 38)  


    def test_validate_correct_record_with_crc_type_05(self):
        data = b'\x00=\x00\x05\x00 \x00\x16\x1f5+A"2@u%YwattGrowattGrowattGr\x4f\x8b'
        (processed_bytes, msg) = extract_record_from_datastream(data)
        self.assertEqual(msg["valid"], True) 
        self.assertEqual(processed_bytes, 40) 


    def test_validate_correct_record_with_crc_type_06(self):
        data = b'\x00=\x00\x06\x00 \x01\x16\x1f5+A"2@u%YwattGrowattGrowattGr\xe3\xfd'
        (processed_bytes, msg) = extract_record_from_datastream(data)
        self.assertEqual(msg["valid"], True) 
        self.assertEqual(processed_bytes, 40) 


    def test_validate_real_record_with_correct_data(self):
        data = b'\x00=\x00\x06\x00 \x01\x16\x1f5+A"2@u%YwattHrowattGrowattGr\xe3\xfd'
        (processed_bytes, msg) = extract_record_from_datastream(data)
        self.assertEqual(msg["valid"], False) 
        self.assertEqual(processed_bytes, 40) 


    def test_validate_real_record_with_corrupt_crc(self):
        data = b'\x00=\x00\x06\x00 \x01\x16\x1f5+A"2@u%YwattGrowattGrowattGr\xe3\xff'
        (processed_bytes, msg) = extract_record_from_datastream(data)
        self.assertEqual(msg["valid"], False) 
        self.assertEqual(processed_bytes, 40) 
        
        
    def test_validate_record_announced_length_too_big(self):
        data = bytes(b'abcdefgahcdefgh')
        (processed_bytes, msg) = extract_record_from_datastream(data)
        self.assertEqual(msg["valid"], False)
        self.assertEqual(processed_bytes, 0) 


class TestGrottdataAutoCreateLayout(unittest.TestCase):
            
    def test_AutoCreateLayout_short_data_protocol_0(self):
        conf       = grottconf.Conf("3.0.0_20241208")
        conf.mindatarec = 10
        data       = bytes(b'\00\00\00\00\00\06\01\03\00\00\00\00\D3\47')
        (num, msg) = extract_record_from_datastream(data)
        result     = AutoCreateLayout(conf, msg)
        self.assertEqual(result, msg["layout"])


    def test_AutoCreateLayout_too_short_data(self):
        conf       = grottconf.Conf("3.0.0_20241208")
        conf.mindatarec = 10
        data       = bytes(b'xyz')
        (num, msg) = extract_record_from_datastream(data)
        result     = AutoCreateLayout(conf, msg)
        self.assertEqual(result, "none")

    
    def test_AutoCreateLayout_short_data_protocol_05(self):
        conf       = grottconf.Conf("3.0.0_20241208")
        data       = bytes(b'xyz')
        (num, msg) = extract_record_from_datastream(data)
        result     = AutoCreateLayout(conf, msg)
        self.assertEqual(result, "none")
    
    
    def test_AutoCreateLayout_short_data_protocol_06(self):
        conf       = grottconf.Conf("3.0.0_20241208")
        data       = bytes(b'a')
        (num, msg) = extract_record_from_datastream(data)
        result     = AutoCreateLayout(conf, msg)
        self.assertEqual(result, "none")
        

class TestGrottdata_procdata(unittest.TestCase):
    def test_procdata(self):
        result   = 1
        expected = 1
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()