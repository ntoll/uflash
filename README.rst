uFlash
======

**THIS MODULE ONLY WORKS WITH PYTHON 3.**

A utility for flashing the BBC micro:bit with Python scripts and the
MicroPython runtime. You pronounce the name of this utility "micro-flash". ;-)

It provides two services:

1. A library of functions to programatically create a hex file and flash it onto a BBC micro:bit.
2. A command line utility called `uflash` that will flash Python scripts onto a BBC micro:bit.

Several essential operations are implemented:

* Encode Python into the hex format.
* Embed the resulting hexified Python into the MicroPython runtime hex.
* Discover the connected micro:bit.
* Copy the resulting hex onto the micro:bit, thus flashing the device.

Installation
------------

To install simply type::

    $ pip install uflash

...and the package will download from PyPI. If you wish to upgrade to the
latest version, use the following command::

    $ pip install --no-cache --upgrade uflash

Command Usage
-------------

To read help simply type::

    $ uflash help

If you type the command on its own then uflash will attempt to find a connected
BBC micro:bit and flash an unmodified version of the MicroPython runtime onto
it::

    $ uflash
    Flashing Python to: /media/ntoll/MICROBIT/micropython.hex

To flash a version of the MicroPython runtime with a specified script embedded
within it (so that script is run when the BBC micro:bit boots up) then pass
the path to the Python script in as the first argument to the command::

    $ uflash my_script.py
    Flashing Python to: /media/ntoll/MICROBIT/micropython.hex

At this point uflash will try to automatically detect the path to the device.
However, if you have several devices plugged in and/or know what the path on
the filesystem to the BBC micro:bit already is, you can specify this as a
second argument to the command::

    $ uflash myscript.py /media/ntoll/MICROBIT
    Flashing Python to: /media/ntoll/MICROBIT/micropython.hex

Development
-----------

The source code is hosted in GitHub. Please feel free to fork the repository.
Assuming you have Git installed you can download the code from the canonical
repository with the following command::

    $ git clone https://github.com/ntoll/uflash.git

Ensure you have the correct dependencies for development installed by creating
a virtualenv and running::

    $ pip install -r requirements.txt

To locally install your development version of the module into a virtualenv,
run the following command::

    $ python setup.py develop
