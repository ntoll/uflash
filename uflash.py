# -*- coding: utf-8 -*-
"""
Code for turning a Python script into a .hex file and flashing it onto a
BBC micro:bit.
"""
import sys
import os
import struct
import binascii


SCRIPT_ADDR = 0x3e000  # magic start address in flash of script


def hexlify(script):
    """
    Takes the byte content of a Python script and returns an appropriately
    encoded hex version of it.

    Based on the hexlify script in the microbit-micropython repository.
    """
    if not script:
        return ''
    # add header, pad to multiple of 16 bytes
    data = b'MP' + struct.pack('<H', len(script)) + script
    data = data + bytes(16 - len(data) % 16)
    assert len(data) <= 0x2000
    # convert to .hex format
    output = []
    addr = SCRIPT_ADDR
    assert(SCRIPT_ADDR >> 16 == 3)  # 0x0003 is hard coded in line below
    output.append(':020000040003F7')  # extended linear address, 0x0003
    for i in range(0, len(data), 16):
        chunk = data[i:min(i + 16, len(data))]
        chunk = struct.pack('>BHB', len(chunk), addr & 0xffff, 0) + chunk
        checksum = (-(sum(chunk))) & 0xff
        hexline = ':%s%02X' % (str(binascii.hexlify(chunk), 'utf8').upper(),
                               checksum)
        output.append(hexline)
        addr += 16
    return '\n'.join(output)


def embed_hex(python_hex, firmware_hex):
    """
    Takes a hex encoded Python fragment and appropriately embeds it into the
    referenced MicroPython firmware hex.

    Returns a string representation of the resulting combination.

    If the python_hex is empty, will return the unmodified firmware_hex.
    """
    if not firmware_hex:
        return ''
    if not python_hex:
        return firmware_hex
    py_list = python_hex.split()
    firm_list = firmware_hex.split()
    embedded_list = []
    # The embedded list should be the original firmware with the Python based
    # hex embedded two lines from the end.
    embedded_list.extend(firm_list[:-2])
    embedded_list.extend(py_list)
    embedded_list.extend(firm_list[-2:])
    return '\n'.join(embedded_list)


def find_microbit():
    """
    Returns a path on the filesystem that represents the plugged in BBC
    micro:bit to be flashed.

    Returns None if no micro:bit is found.
    """
    pass


def save_hex(hex_file, path):
    """
    Given a string representation of a hex file, copies to the specified path
    thus causing the device mounted at that point to be flashed.

    If the path is not to a .hex file, will raise a ValueError.
    """
    if not hex_file:
        raise ValueError('Cannot flash an empty .hex file.')
    if not path.endswith('.hex'):
        raise ValueError('The path to flash must be for a .hex file.')
    with open(path, 'wb') as output:
        output.write(hex_file.encode('ascii'))


def flash(path_to_python=None, path_to_microbit=None):
    """
    Given a path to a Python file will attempt to create a hex file and then
    flash it onto the microbit (identified by path_to_microbit).

    If the path to the Python file is unspecified it will simply flash the
    unmodified MicroPython firmware onto the device.

    If the microbit is unspecified it will attempt to find the device's path
    automatically. If the automatic discovery fails, then it will raise an
    IOError.
    """
    # Grab the MicroPython runtime firmware.hex.
    firmware_hex = None
    firmware_dir = os.path.dirname(os.path.abspath(__file__))
    path_to_firmware = os.path.join(firmware_dir, 'firmware.hex')
    with open(path_to_firmware, 'r') as firmware_file:
        firmware_hex = firmware_file.read()
    # Grab the Python script (if needed).
    python_hex = ''
    if path_to_python:
        with open(path_to_python, 'rb') as python_script:
            python_hex = hexlify(python_script.read())
    # Generate and check the resulting hex file.
    micropython_hex = embed_hex(python_hex, firmware_hex)
    if not micropython_hex:
        raise IOError('Unable to create hex file.')
    # Find the micro:bit.
    if not path_to_microbit:
        path_to_microbit = find_microbit()
    # Attempt to write the hex file to the micro:bit.
    if path_to_microbit:
        hex_file = os.path.join(path_to_microbit, 'micropython.hex')
        print('Flashing Python to: {}'.format(hex_file))
        save_hex(micropython_hex, hex_file)
    else:
        raise IOError('Unable to find micro:bit. Is it plugged in?')


def main(argv=sys.argv[1:]):
    """
    Entry point for the command line tool 'uflash'.
    """
    pass


if __name__ == '__main__':
    sys.exit(main())
