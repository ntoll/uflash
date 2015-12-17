# -*- coding: utf-8 -*-
"""
Code for turning a Python script into a .hex file and flashing it onto a
BBC micro:bit.
"""
import sys


def hexlify(script):
    """
    Takes the content of a Python script and returns an appropriately encoded
    hex version of it.
    """
    pass


def embed_hex(python_hex, firmware_hex):
    """
    Takes a hex encoded Python fragment and appropriately embeds it into the
    referenced MicroPython firmware hex.

    Returns a string representation of the resulting combination.
    """
    pass


def find_microbit():
    """
    Returns a path on the filesystem that represents the plugged in BBC
    micro:bit to be flashed.

    Returns None is none is found.
    """
    pass


def flash(hex_file, path):
    """
    Given a string representation of a hex file, copies to the specified path
    thus causing the device mounted at that point to be flashed.
    """
    pass


def main(argv=sys.argv[1:]):
    """
    Entry point for the command line tool 'uflash'.
    """
    pass


if __name__ == '__main__':
    sys.exit(main())
