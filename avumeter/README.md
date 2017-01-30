SN3218 ALSA VU METER
====================

`avumeter` is a generic ALSA plugin for the SN3218.

It is primarily intended for the SN3218 breakout, but should work with any product with a SN3218 on an I2C bus addr 0x54.

To install,

```
sudo apt-get install build-essential libasound2-dev wiring-pi
```

then

```
make
sudo make install
```

You will also need an ad hoc ALSA configuration file. You'll find one herein that works with our pHAT DAC.

To use, copy the file to the `/etc` directory:

```
sudo cp ./asound.conf /etc
```
