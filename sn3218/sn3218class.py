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

DEFAULT_NAMES = {'ONE': 1,
                 'TWO': 2,
                 'THREE': 3,
                 'FOUR': 4,
                 'FIVE': 5,
                 'SIX': 6,
                 'SEVEN': 7,
                 'EIGHT': 8,
                 'NINE': 9,
                 'TEN': 10,
                 'ELEVEN': 11,
                 'TWELVE': 12,
                 'THIRTEEN': 13,
                 'FOURTEEN': 14,
                 'FIFTEEN': 15,
                 'SIXTEEN': 16,
                 'SEVENTEEN': 17,
                 'EIGHTEEN': 18}


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

        Raises:
            ValueError: if led_names is not a dictionary or if one of the numbers in
                led_names is not in the range 1-18.

        """
        led_bits = {'NONE': 0, 'ALL': 0b111111111111111111}
        # Default/backup numerical LED names,
        for i, name in enumerate(DEFAULT_NAMES):
            led_bits[name] = self._led_number_to_int(i + 1)
        # Add user defined LED names.
        if led_names:
            try:
                for name, number in led_names.items():
                    if number not in range(0, 18):
                        msg = "LED numbers in led_names must be 1-18, found {}.".format(number)
                        raise ValueError(msg)
                    led_bits[name] = self._led_number_to_int(number)
            except (AttributeError, TypeError):
                msg = "led_names should be a dictionary, got {}.".format(type(led_names))
                raise ValueError(msg)
            self._led_names = led_names
        else:
            self._led_names = DEFAULT_NAMES

        # enum.Flag to associate names with bitmasks
        self._led_bitmask = Flag('LEDBitmask', led_bits)

        # Open I2C connection
        self._i2c = SMBus(self._get_i2c_bus_id())

        # Generate a good default gamma table.
        self._default_gamma_table = [int(255**((i - 1) / 255)) for i in range(256)]
        # Reset all LED gamma tables to default.
        self.reset_led_gamma()
        # Turn off all LEDS.
        self.turn_off_leds()
        # Set brightness to max.
        self.set_leds_brightness(255)
        # Enable output (LEDs will remain off)
        self.enable()

    def __del__(self):
        """Shutdown."""
        self.turn_off_leds()
        self.disable()
        try:
            del(self._i2c)
        except AttributeError:
            pass

# Properties

    @property
    def leds_enabled(self):
        """Return current status of named LEDS."""
        return self.get_leds_enabled()

    @leds_enabled.setter
    def leds_enabled(self, leds_enabled):
        """Turn on or off specified LEDs.

        See set_leds_enabled() method for details.
        """
        self.set_leds_enabled(leds_enabled)

    @property
    def leds_brightness(self):
        """Return current brightness of named LEDS."""
        return self.get_leds_brightness()

    @leds_brightness.setter
    def leds_brightness(self, leds_brightness):
        """Set brightness of LEDS.

        See set_leds_brightness for details.
        """
        self.set_leds_brightness(self, leds_brightness)

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
        """Turn off specified LEDs.

        Args:
            leds (list, optional): list of LED specifiers, each one will be turned off.
                LED specifiers can be either strings corresponding to a user defined
                name, or one of the default names (e.g. 'EIGHT'), or an integer between
                1 and 18. If not given all LEDs will be turned off.

        Raises:
            ValueError: if an element of leds is not a valid LED specifier.

        """
        if not leds:
            # Turn them all off.
            self._leds_enabled = self._led_bitmask.NONE
        else:
            for led in leds:
                led_bitmask = self._get_led_bitmask(led)
                # Disable bit corresponding to specified LED by ANDing with NOT the bitmask.
                self._leds_enabled & ~led_bitmask

        self._enable_leds(self._LEDS_enabled.value)

    def turn_on_leds(self, leds=None):
        """Turn on specified LEDs.

        Args:
            leds (list, optional): list of LED specifiers, each one will be turned on.
                LED specifiers can be either strings corresponding to a user defined
                name, or one of the default names (e.g. 'EIGHT'), or an integer between
                1 and 18. If not given all LEDs will be turned off.

        Raises:
            ValueError: if an element of leds is not a valid LED specifier.

        """
        if not leds:
            # Turn them all on.
            self._leds_enabled = self._led_bitmask.ALL
        else:
            for led in leds:
                led_bitmask = self._get_led_bitmask(led)
                # Enable bit corresponding to specified LED by ORing with the bitmask.
                self._leds_enabled | led_bitmask

        self._enable_leds(self._leds_enabled.value)

    def get_leds_enabled(self, named_only=True):
        """Return current status of LEDs.

        Args:
            named_only (bool, optional): If True will only return the status of LEDS with
                user set names, otherwise will return the status of all the LEDs using
                their numerical names. Default True.

        Returns:
            dict: Dictionary of {name: status} pairs where status if True if the named LED is
                currently enabled and False if not.

        """
        if named_only:
            names = self._led_names
        else:
            names = DEFAULT_NAMES

        return {name: bool(self._leds_enabled & self._led_bitmask[name]) for name in names}

    def set_leds_enabled(self, leds_enabled):
        """Turn on or off specified LEDs.

        Args:
            leds_enabled (dict): dictionary of LED specifiers and boolean values. If the value
                is True the corresponding LED will be turned on, if the value is False the
                corresponding LED will be turned off. Any LEDS not in the dictionary will
                remain in their current state. LED specifiers can be either strings
                corresponding to a user defined name, or one of the default names (e.g. 'EIGHT'),
                or an integer between 1 and 18.

        Raises:
            ValueError: if leds_enabled is not a dictionary or if it contains an invalid LED
                specifier.

        """
        try:
            for led, enable in leds_enabled.items():
                led_bitmask = self.get_led_bitmask(led)
                if enable:
                    self._leds_enabled | led_bitmask
                else:
                    self._leds_enabled & ~led_bitmask
        except (AttributeError, TypeError):
            msg = "led_enabled must be a dictionary, got {}".format(type(leds_enabled))
            raise ValueError(msg)

        self._enable_leds(self._leds_enabled.value)

    def get_leds_brightness(self, named_only=True):
        """Return current brightness of LEDs.

        Args:
            named_only (bool, optional): If True will only return the brightness of LEDS with
                user set names, otherwise will return the brightness of all the LEDs using
                their numerical names. Default True.

        Returns:
            dict: Dictionary of {name: brightness} pairs where brightness is an integer value
                between 0 and 255.

        """
        if named_only:
            names = self._led_names
        else:
            names = DEFAULT_NAMES

        return {name: self._led_brightness[self._get_led_number(name) - 1] for name in names}

    def set_leds_brightness(self, leds_brightness):
        """Set brightness of specified LEDs.

        Args: leds_brightness (dict or int): dictionary of LED specifiers and integer brightness
            values in the range 0 to 256. LED specifiers can be either strings corresponding to a
            user defined name, or one of the default names (e.g. 'EIGHT'), or an integer between
            1 and 18. Alternatively leds_brightness can be a single integer value, in which case
            the brightness of all LEDS will be set to this value.

        Raises:
            ValueError: if leds_brightness is not a dictionary or a valid int, or if
                leds_brightness contains invalid LED specifiers or brightness values.
        """
        try:
            # Try to access leds_brightness as a dictionary.
            for led, brightness in leds_brightness.items():
                led_number = self._get_led_number(led) - 1
                brightness = self._check_integer(brightness, 0, 255)
                self._leds_brightness[led_number] = brightness
        except (AttributeError, TypeError):
            # Not a dictionary, try to use it as an int.
            brightness = self._check_integer(leds_brightness, 0, 255)
            self._leds_brightness = [brightness] * 18

        self._set_led_brightness(self._leds_brightness)

    def set_led_gamma(self, led, gamma_table):
        """Override the gamma table for a single LED.

        Args:
            led (str or int): LED specifier, can be a string corresponding to a user
                defined name, one of the default names (e.g. 'EIGHT'), or an integer
                between 1 and 18.
            gamma_table (list): list of 256 gamma correction values

        Raises:
            ValueError: if led is not a valid LED specifier
            TypeError: if gamma_table is not a list.
            ValueError: if gamma_table does not have 256 elements.

        """
        led_number = self._get_led_number(led)

        if not isinstance(gamma_table, list):
            try:
                gamma_table = list(gamma_table)
            except Exception:
                msg = "gamma_table must be a list, got {}.".format(type(gamma_table))
                raise TypeError(msg)

        if len(gamma_table) != 256:
            raise ValueError("gamma_table must have 256 elements, got {}.".format(len(gamma_table)))

        gamma_table = [self._check_integer(gamma, 0, 255) for gamma in gamma_table]
        self._led_gamma_tables[led_number] = gamma_table

    def reset_led_gamma(self, led=None):
        """Reset the gamma table for all LEDS, or a single LED.

        Args:
            led (str or int, optional): LED specifier, can be a string corresponding to a user
                defined name, one of the default names (e.g. 'EIGHT'), or an integer between 1
                and 18. If not given the gamme table for all LEDs will be reset to defaults.

        Raises:
            ValueError: if led is not a valid LED specifier

        """
        if not led:
            # Reset all the gamme tables.
            self._led_gamma_tables = [self._default_gamma_table] * 18
        else:
            led_number = self._get_led_number(led)
            self._led_gamma_tables[led_number - 1] = self._default_gamma_table

# Private methods

    def _get_i2c_bus_id(self):
        revision = ([l[12:-1] for l in open('/proc/cpuinfo', 'r').readlines()
                     if l[:8] == "Revision"]+['0000'])[0]
        return 1 if int(revision, 16) >= 4 else 0

    def _led_number_to_int(self, number):
        return 2**int(number - 1)

    def _get_led_number(self, specifier):
        try:
            # Try to use led as user defined name.
            led_number = self._led_names[specifier]
        except KeyError:
            # Try using led as a default name.
            try:
                led_number = DEFAULT_NAMES[specifier]
            except KeyError:
                try:
                    # Try to use led as a led number
                    led_number = self._check_integer(specifier, 1, 18)
                except Exception:
                    msg = "'{}' is not a valid LED name or LED number.".format(specifier)
                    raise ValueError(msg)

        return led_number

    def _get_led_bitmask(self, specifier):
        try:
            # Try retrieving bitmask by name.
            led_bitmask = self._led_bitmask['specifier']
        except KeyError:
            # Retrieving by name didn't work, try retrieving by number.
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

    def _set_led_brightness(self, leds_brightness):
        pwm_values = [self._led_gamma_tables[i][leds_brightness[i]] for i in range(18)]
        self._i2c.write_i2c_block_data(I2C_ADDRESS, CMD_SET_PWM_VALUES, pwm_values)
        self._i2c.write_i2c_block_data(I2C_ADDRESS, CMD_UPDATE, [0xFF])

    def _check_integer(self, value, lower_limit, upper_limit):
        try:
            value = int(value)
        except (ValueError, TypeError):
            msg = "Could not convert '{}' to int".format(value)
            raise ValueError(msg)

        if value < lower_limit or value > upper_limit:
            msg = "Value must be between {} & {}, got {}.".format(lower_limit, upper_limit, value)
            raise ValueError(msg)

        return value
