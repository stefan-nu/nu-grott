import unittest
import grottdata
import grottconf


class TestGrottPVOutputLimit(unittest.TestCase):
            
    def test_AutoCreateLayout_short_data_protocol_0(self):
        conf       = grottconf.Conf("3.0.0_20241208")
        data       = bytes(b'abcdef')
        protocol   = 0
        deviceno   = 1
        recordtype = 3
        result     = grottdata.AutoCreateLayout(conf, data, protocol, deviceno, recordtype)
        expected_result = ("none", '616263646566')
        self.assertEqual(result, expected_result)


    def test_AutoCreateLayout_short_data_protocol_02(self):
        conf       = grottconf.Conf("3.0.0_20241208")
        data       = bytes(b'xyz')
        protocol   = '02'
        deviceno   = 1
        recordtype = 3
        result     = grottdata.AutoCreateLayout(conf, data, protocol, deviceno, recordtype)
        expected_result = ("none", '78797a')
        self.assertEqual(result, expected_result)

    
    def test_AutoCreateLayout_short_data_protocol_05(self):
        conf       = grottconf.Conf("3.0.0_20241208")
        data       = bytes(b'xyz')
        protocol   = '05'
        deviceno   = '01'
        recordtype = '03'
        result     = grottdata.AutoCreateLayout(conf, data, protocol, deviceno, recordtype)
        expected_result = ("none", '78797a')
        self.assertEqual(result, expected_result)
    
    
    def test_AutoCreateLayout_short_data_protocol_06(self):
        conf       = grottconf.Conf("3.0.0_20241208")
        data       = bytes(b'a')
        protocol   = '06'
        deviceno   = '01'
        recordtype = '03'
        result     = grottdata.AutoCreateLayout(conf, data, protocol, deviceno, recordtype)
        expected_result = ("none", '61')
        self.assertEqual(result, expected_result)
        
    
    def test_AutoCreateLayout_correct_data_unknown_layout_T060103(self):
        conf       = grottconf.Conf("3.0.0_20241208")
        data       = bytes(b'abcdefgahcdefgh')
        protocol   = '06'
        deviceno   = '01'
        recordtype = '03'
        result     = grottdata.AutoCreateLayout(conf, data, protocol, deviceno, recordtype)
        expected_result = ("T060103", '61626364656667612f110b1207131c')
        self.assertEqual(result, expected_result)
        

    def test_procdata(self):
        result   = 1
        expected = 1
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()