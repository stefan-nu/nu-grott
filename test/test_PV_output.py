import unittest
import PV_output
import grottconf


class Test_PV_Output(unittest.TestCase):

    def test_ok_send_run_once_should_be_ok(self):
        defined_key = {}
        defined_key["pvserial"] = "1234"
        conf   = grottconf.Conf("3.0.0_20241208")
        pvout_limit = PV_output.GrottPvOutLimit()
        result = pvout_limit.ok_send(defined_key["pvserial"], conf)
        self.assertEqual(result, True)
        
        
    def test_ok_send_run_twice_should_not_be_ok(self):
        defined_key = {}
        defined_key["pvserial"] = "1234"
        conf   = grottconf.Conf("3.0.0_20241208")
        pvout_limit = PV_output.GrottPvOutLimit()
        result1 = pvout_limit.ok_send(defined_key["pvserial"], conf)
        result2 = pvout_limit.ok_send(defined_key["pvserial"], conf)
        self.assertEqual(result1, True)
        self.assertEqual(result2, False)


if __name__ == '__main__':
    unittest.main()