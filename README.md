SN3218
======

A fork of Pimoroni's set of drivers for the SN3218 18-channel PWM LED driver
(original here: https://github.com/pimoroni/sn3218)

The purpose of this fork is to add an object oriented (class based) inteface with a more
Pythonic idiom. This may be preferable for users who are more accustomed to idiomatic Python
programming than they are to bitmasks.

Features:

- Class based interface.
- Full docstrings for all public methods and properties.
- PEP8 compliant code.
- Inputs and outputs mostly dictionaries of ints or bools.
- Backwards compatible (original interface still present).

To install first uninstall any other versions of the `sn3218` library hen use:

```
pip install git+https://github.com/AnthonyHorton/sn3218.git
```

You may need to add the `--user` or `--root` options to change the install location. See `pip`
documentation for details.

To install using git:

```
git clone https://github.com/AnthonyHorton/sn3218.git
cd sn3218
python setup.py install
```

To use the original interace `import sn3218` and proceed as before. To use the object orientated
inteface:

```
from sn3218.sn3218 import SN3218

leds = SN3218(led_names)
```

Here `led_names` is an optional dictionary of user defined names for the LED channels together
with the corresponding integer channel numbers. If names are set then intuitive commands such as
`leds.turn_on_leds(['POWER', 'READY'])` can be used, and the return values of status methods like
`leds.get_leds_brightness()` are more readable. All methods and properties are documented with
full docstrings in the file `sn3218/sn3218class.py`.

A demo/self test routine (a reproduction of the original) can be run with `leds.demo()`.
