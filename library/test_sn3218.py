
"""
Tests for sn3218.py
"""

import builtins
import sys
import time
import unittest
from unittest.mock import patch

# fool pylint
sn3218 = None # pylint: disable=invalid-name

# Change this to slow down
DELAY_SEC = 0.1

SKIPSLOW = False

if sys.version_info < (3,):
    sys.exit("tests currently require python3")

def delay(sec=DELAY_SEC):
    """Sleep for sec seconds"""
    if sec:
        time.sleep(sec)

realimport = builtins.__import__

def fail_import(name, globals, locals, fromlist, level):
    """Helper function to selectively fail import"""
    # pylint: disable=redefined-builtin

    if name in {'smbus'}:
        raise ImportError("Mock import error")
    return realimport(name, globals, locals, fromlist, level)

class ImportTest(unittest.TestCase):
    """Test for import failure, and the actual module import"""

    def test_import_fail(self):
        """Module import fails when smbus is unavailable"""

        # pylint: disable=redefined-outer-name
        with patch('builtins.__import__', fail_import):
            with self.assertRaisesRegex(ImportError, "requires"):
                import sn3218
                assert sn3218

    def test_import_ok(self):
        """Module loads correctly"""
        # ugly hack: this test must run early, and must not be skipped

        # pylint: disable=global-statement,redefined-outer-name
        global sn3218
        import sn3218

class SN3218Test(unittest.TestCase):
    """Tests of sm3218 functions"""

    def setUp(self):
        """Reset chip for each test"""
        sn3218.reset()
        sn3218.enable()
        sn3218.enable_leds(0b111111_111111_111111)

    def test_i2c_bus_id(self):
        """Detect i2c bus ID"""
        result = sn3218.i2c_bus_id()
        self.assertIn(result, (0, 1))

    def test_disable_enable(self):
        """Enable / disable operations"""
        sn3218.disable()
        delay()
        sn3218.enable()
        delay()

    def test_reset(self):
        """Reset the SN3218"""
        sn3218.reset()

    def test_enable_leds(self):
        """Enable different combinations of LEDs"""
        sn3218.output([60] * 18)
        for _ in range(3):
            sn3218.enable_leds(0b101010_101010_101010)
            delay()
            sn3218.enable_leds(0b010101_010101_010101)
            delay()
            sn3218.enable_leds(0b000000_000000_000000)
            delay()
            sn3218.enable_leds(0b111111_111111_111111)
            delay()

    def test_enable_leds_non_int(self):
        """Enable fails with wrong type"""
        sn3218.output([60] * 18)
        with self.assertRaisesRegex(TypeError,
                                    'must be an integer'):
            sn3218.enable_leds("banana")

    def test_channel_gamma_ok(self):
        """Set channel gamma"""
        sn3218.channel_gamma(0, [0x88] * 256)
        self.assertEqual(sn3218.channel_gamma_table[0], [0x88] * 256)

    def test_channel_gamma_wrong_channel(self):
        """channel_gamma fails with wrong type"""
        with self.assertRaisesRegex(TypeError,
                                    'channel must be an integer'):
            sn3218.channel_gamma("apple", [0x88] * 256)

    def test_channel_gamma_wrong_channel_val(self):
        """channel_gamma fails with wrong value"""
        with self.assertRaisesRegex(ValueError,
                                    'in the range 0..17'):
            sn3218.channel_gamma(999, [0x88] * 256)

    def test_channel_gamma_wrong_table(self):
        """channel_gamma fails with wrong type"""
        with self.assertRaisesRegex(TypeError,
                                    'must be a list'):
            sn3218.channel_gamma(0, (1, 2, 3))

    def test_channel_gamma_wrong_table_len(self):
        """channel_gamma fails with wrong length"""
        with self.assertRaisesRegex(TypeError,
                                    'list of 256 integers'):
            sn3218.channel_gamma(0, [0x88] * 200)

    def test_output_1(self):
        """Output to LEDs"""
        sn3218.output([0x60] * 18)
        delay(0.5)

    def test_output_wrong_type(self):
        """output fails with wrong type"""
        with self.assertRaisesRegex(TypeError,
                                    'must be a list'):
            sn3218.output("apple")

    def test_output_wrong_len(self):
        """output fails with wrong length"""
        with self.assertRaisesRegex(TypeError,
                                    'list of 18 integers'):
            sn3218.output([0x60] * 99)

    def test_output_raw(self):
        """Output directly to LEDs"""
        sn3218.output_raw([0x60] * 18)
        delay(1)

    def test_output_raw_wrong_type(self):
        """output fails with wrong type"""
        sn3218.output_raw([0x60] * 18)
        with self.assertRaisesRegex(TypeError,
                                    'must be a list'):
            sn3218.output_raw("apple")

    def test_output_raw_wrong_len(self):
        """output fails with wrong length"""
        sn3218.output_raw([0x60] * 18)
        with self.assertRaisesRegex(TypeError,
                                    'list of 18 integers'):
            sn3218.output_raw([0x60] * 99)

    @unittest.skipIf(SKIPSLOW, "skipping slow test")
    def test_module_tests(self):
        """Run the test included in sn3218.py"""
        sn3218.test_cycles()

if __name__ == "__main__":
    delay(0) # for coverage
    unittest.main()
