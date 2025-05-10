import unittest
import utils


class TestutilsConvert2Bool(unittest.TestCase):
    
    def test_convert2bool(self):
        self.assertEqual(utils.convert2bool("TRUE"), True)
        self.assertEqual(utils.convert2bool("TRuE"), True)
        self.assertEqual(utils.convert2bool("true"), True)
        self.assertEqual(utils.convert2bool("True"), True)
        self.assertEqual(utils.convert2bool("YES"),  True)
        self.assertEqual(utils.convert2bool("Yes"),  True)
        self.assertEqual(utils.convert2bool("yes"),  True)
        self.assertEqual(utils.convert2bool("Y"),    True)
        self.assertEqual(utils.convert2bool("y"),    True)
        self.assertEqual(utils.convert2bool("1"),    True)
        self.assertEqual(utils.convert2bool(1),      True)
        self.assertEqual(utils.convert2bool(2),      True)
        self.assertEqual(utils.convert2bool(123456), True)
        self.assertEqual(utils.convert2bool(-1),     True)
        self.assertEqual(utils.convert2bool(True),   True)
        
        self.assertEqual(utils.convert2bool("FALSE"), False)
        self.assertEqual(utils.convert2bool("FAlsE"), False)
        self.assertEqual(utils.convert2bool("false"), False)
        self.assertEqual(utils.convert2bool("False"), False)
        self.assertEqual(utils.convert2bool("NO"),    False)
        self.assertEqual(utils.convert2bool("No"),    False)
        self.assertEqual(utils.convert2bool("no"),    False)
        self.assertEqual(utils.convert2bool("N"),     False)
        self.assertEqual(utils.convert2bool("n"),     False)
        self.assertEqual(utils.convert2bool("0"),     False)
        self.assertEqual(utils.convert2bool(0),       False)
        self.assertEqual(utils.convert2bool(False),   False)
    
        self.assertEqual(utils.convert2bool(""),      None)
        self.assertEqual(utils.convert2bool("a"),     None)
        self.assertEqual(utils.convert2bool("2"),     None) # should this be considered True?
        self.assertEqual(utils.convert2bool("123"),   None) # should this be considered True?
        self.assertEqual(utils.convert2bool("?"),     None)
        self.assertEqual(utils.convert2bool("hello"), None)
        self.assertEqual(utils.convert2bool("ABC"),   None)
        self.assertEqual(utils.convert2bool("!&/("),  None)


class TestutilsFormatMultiLine(unittest.TestCase):

    def test_format_multi_line_string_shorter_than_limit(self):
        data = "abc"
        result = utils.format_multi_line("", data, 4)
        self.assertEqual(result, "abc")

    def test_format_multi_line_string_length_equal_to_limit(self):
        data = "123"
        result = utils.format_multi_line("", data, 3)
        self.assertEqual(result, "123")

    def test_format_multi_line_string_length_longer_to_limit(self):
        data = "---"
        result = utils.format_multi_line("", data, 2)
        self.assertEqual(result, "--\n-")

    def test_format_multi_line_string_add_prefix(self):
        data = "123"
        result = utils.format_multi_line("###", data, 12)
        self.assertEqual(result, "###123")


class TestCrypt(unittest.TestCase):
    
    # Datastreams with length smaller than 9 bytes are not encrypted
    def test_decrypt_data_smaller_than_9byte(self):
        data_bin = b'\x00'
        expected = "00"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)
        
        data_bin = b'\xff'
        expected = "ff"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)
        
        data_bin = b'\x1e\x7a'
        expected = "1e7a"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)
        
        data_bin = b'\x00\x00\x00\x00'
        expected = "00000000"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)

        data_bin = b'\x01\x02\x03\x04\x05\x06\x07'
        expected = "01020304050607"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)
        
        data_bin = b'\x01\x02\x03\x04\x05\x06\x07\x08'
        expected = "0102030405060708"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)


    # The first 8 bytes of a datastreams are not encrypted. 
    # Messages longer than 8 bytes are decrypted starting at byte 9
    def test_decrypt_data_9bytes_long_and_longer(self):
        data_bin = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09'
        expected = "01020304050607084e"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)
        
        data_bin = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
        expected = "00010203040506074f7b657c6d797a48"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)
        
        data_bin = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        expected = "000000000000000047726f7761747447"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)

        data_bin = b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x04\x08\x10\x20\x30\x40'
        expected = "000000000000000046706b7f71544407"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)
        
        data_bin = b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x04\x08\x10\x20\x30\x40\x08\x01\x02\x03\x04\10\x20\x40'
        expected = "000000000000000046706b7f715444077a6e7562707c6732"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)

        data_bin = b'\x00\x01\x02\x03\x04\x05Growatt'
        expected = "000102030405477228050e0315"
        result   = utils.decrypt(data_bin)
        self.assertEqual(result, expected)
        
        
    def test_crypt_has_to_be_symmetric(self):
        data_bin = b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x04\x08\x10\x20\x30\x40\x08\x01\x02\x03\x04\10\x20\x40' 
        expected = "000000000000000001020408102030400801020304082040"
        
        result1 = utils.encrypt(data_bin)
        result2 = utils.decrypt(data_bin)
        self.assertEqual(result1, result2)
        
        result1   = utils.decrypt(utils.crypt(data_bin))
        result2   = utils.encrypt(utils.crypt(data_bin))
        self.assertEqual(result1, expected)
        self.assertEqual(result2, expected)
        self.assertEqual(result1, result2)
        

if __name__ == '__main__':
    unittest.main()