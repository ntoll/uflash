Gordon
======

A utility for flashing the BBC micro:bit with MicroPython.

This module provides two services:

1. A library of functions to programatically create a hex file and flash it onto a BBC micro:bit.
2. A command line utility called `gordon` that takes a path to a Python file, and an optional target location then turns it into a hex file and copies it to either the target or the discovered MICROBIT device.

There are several operations required:

* Encode the Python into hex format.
* Embed the resulting hexified Python into the MicroPython runtime hex.
* Discover the connected micro:bit.
* Copy the resulting hex onto the micro:bit, thus flashing the device.
