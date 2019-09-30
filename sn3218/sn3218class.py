"""Object orientated interface for SN3218 18 channel PWM LED driver."""
import sys
from enum import Flag

try:
    from smbus import SMBus
except ImportError:
    if sys.version_info[0] < 3:
        msg = "This library requires python-smbus\nInstall with: sudo apt install python-smbus"
        raise ImportError(msg)
    elif sys.version_info[0] == 3:
        msg = "This library requires python3-smbus\nInstall with: sudo apt install python3-smbus"
        raise ImportError(msg)


I2C_ADDRESS = 0x54
CMD_ENABLE_OUTPUT = 0x00
CMD_SET_PWM_VALUES = 0x01
CMD_ENABLE_LEDS = 0x13
CMD_UPDATE = 0x16
CMD_RESET = 0x17


class SN3218():
    """Class representing an SN3218 18 channel PWD LED driver."""

    def __init__(self, led_names=None):
        """Class representing an SN3218 18 channel PWN LED driver.

        Args:
            led_names (dict, optional): dictionary mapping names to LED numbers, i.e.
                {"NAME1": 4, "NAME2": 3, "NAME3": 12}. LED numbers must be integer in
                the range 1 - 18. Names must be unique, i.e. each name can only be used
                for one LED, but multiple names can be used to refer to the same LED.
                LEDs that are not named can still be controlled by number.
        """
        led_bits = {'NONE': 0, 'ALL': 0b111111111111111111}
        # Default/backup numerical LED names,
        for i, name in enumerate(['ONE',
                                  'TWO',
                                  'THREE',
                                  'FOUR',
                                  'FIVE',
                                  'SIX',
                                  'SEVEN',
                                  'EIGHT',
                                  'NINE',
                                  'TEN',
                                  'ELEVEN',
                                  'TWELVE',
                                  'THIRTEEN',
                                  'FOURTEEN',
                                  'FIFTEEN',
                                  'SIXTEEN',
                                  'SEVENTEEN',
                                  'EIGHTEEN']):
            led_bits[name] = self._led_number_to_int(i + 1)
        # Add user defined LED names.
        if led_names:
            try:
                for name, number in led_names.items():
                    if number not in range(0, 18):
                        msg = "LED numbers in led_names must be 0-17, found {}.".format(number)
                        raise ValueError(msg)
                    led_bits[name] = self._led_number_to_int(number)
            except (AttributeError, TypeError):
                msg = "led_names should be a dictionary, got {}.".format(type(led_names))
                raise ValueError(msg)
            self._led_names = list(led_names.keys())
        else:
            self._led_names = list(led_bits.keys())

        # enum.Flag to associate names with bitmasks
        self._LEDBitMask = Flag('LEDBitMask', led_bits)

        # Open I2C connection
        self._i2c = SMBus(self._get_i2c_bus_id())

        # generate a good default gamma table
        self._default_gamma_table = [int(pow(255, float(i - 1) / 255)) for i in range(256)]
        self._channel_gamma_table = [self._default_gamma_table] * 181

        # Turn off all LEDS but enable output.
        self.turn_off_leds()
        self.enable()

    def __del__(self):
        """Shutdown."""
        self.turn_off_leds()
        self.disable()
        try:
            del(self._i2c)
        except AttributeError:
            pass

# Public methods

    def enable(self):
        """Enable outputs."""
        self._i2c.write_i2c_block_data(I2C_ADDRESS, CMD_ENABLE_OUTPUT, [0x01])

    def disable(self):
        """Disable outputs."""
        self._i2c.write_i2c_block_data(I2C_ADDRESS, CMD_ENABLE_OUTPUT, [0x00])

    def reset(self):
        """Reset all internal registers."""
        self._i2c.write_i2c_block_data(I2C_ADDRESS, CMD_RESET, [0xFF])

    def turn_off_leds(self, leds=None):
        """Turn off specified LEDs."""
        if not leds:
            # Turn them all off.
            self._LEDs_enabled = self._LEDBitMask.NONE
        else:
            for led in leds:
                led_bitmask = self._get_bitmask(led)
                # Disable bit corresponding to specified LED by ANDing with NOT the bitmask.
                self._LEDs_enabled & ~led_bitmask

        self._enable_leds(self._LEDS_enabled.value)

    def turn_on_leds(self, leds=None):
        """Turn on specified LEDs."""
        if not leds:
            # Turn them all on.
            self._LEDs_enabled = self._LEDBitMask.ALL
        else:
            for led in leds:
                led_bitmask = self._get_bitmask(led)
                # Enable bit corresponding to specified LED by ORing with the bitmask.
                self._LEDs_enabled | led_bitmask

        self._enable_leds(self._LEDS_enabled.value)

# Private methods

    def _get_i2c_bus_id(self):
        revision = ([l[12:-1] for l in open('/proc/cpuinfo', 'r').readlines()
                     if l[:8] == "Revision"]+['0000'])[0]
        return 1 if int(revision, 16) >= 4 else 0

    def _led_number_to_int(self, number):
        return 2**int(number - 1)

    def _get_bitmask(self, specifier):
        try:
            # Try retrieving bitmask by name.
            led_bitmask = self._LEDBitMask['specifier']
        except KeyError:
            # Retrieving by name didn't work, try retreiving by number.
            try:
                led_bitmask = self._LEDBitMask(self._led_number_to_int(specifier))
            except ValueError:
                raise ValueError("'{}' is not a valid LED specifier.".format(specifier))

        return led_bitmask

    def _enable_leds(self, enable_mask):
        self._i2c.write_i2c_block_data(I2C_ADDRESS, CMD_ENABLE_LEDS,
                                       [enable_mask & 0x3F,
                                        (enable_mask >> 6) & 0x3F,
                                        (enable_mask >> 12) & 0X3F])
        self._i2c.write_i2c_block_data(I2C_ADDRESS, CMD_UPDATE, [0xFF])
