# -*- coding: utf-8 -*-
"""
Code for turning a Python script into a .hex file and flashing it onto a
BBC micro:bit.
"""
import sys
import os
import struct
import binascii
import ctypes
from subprocess import check_output


SCRIPT_ADDR = 0x3e000  # magic start address in flash of script


HELP_TEXT = """
Flash Python onto the BBC micro:bit

Usage: uflash [path_to_script.py] [path_to_microbit]

If no path to the micro:bit is provided uflash will attempt to autodetect the
correct path to the device. If no path to the Python script is provided uflash
will flash the unmodified MicroPython firmware onto the device.
"""


def hexlify(script):
    """
    Takes the byte content of a Python script and returns an appropriately
    encoded hex version of it.

    Based on the hexlify script in the microbit-micropython repository.
    """
    if not script:
        return ''
    # Convert line endings in case the file was created on Windows.
    script = script.replace(b'\r\n', b'\n')
    script = script.replace(b'\r', b'\n')
    # Add header, pad to multiple of 16 bytes.
    data = b'MP' + struct.pack('<H', len(script)) + script
    data = data + bytes(16 - len(data) % 16)
    assert len(data) <= 0x2000
    # Convert to .hex format.
    output = []
    addr = SCRIPT_ADDR
    assert(SCRIPT_ADDR >> 16 == 3)  # 0x0003 is hard coded in line below.
    output.append(':020000040003F7')  # extended linear address, 0x0003.
    for i in range(0, len(data), 16):
        chunk = data[i:min(i + 16, len(data))]
        chunk = struct.pack('>BHB', len(chunk), addr & 0xffff, 0) + chunk
        checksum = (-(sum(chunk))) & 0xff
        hexline = ':%s%02X' % (str(binascii.hexlify(chunk), 'utf8').upper(),
                               checksum)
        output.append(hexline)
        addr += 16
    return '\n'.join(output)


def embed_hex(python_hex, runtime_hex):
    """
    Takes a hex encoded Python fragment and appropriately embeds it into the
    referenced MicroPython runtime hex.

    Returns a string representation of the resulting combination.

    If the python_hex is empty, will return the unmodified runtime_hex.
    """
    if not runtime_hex:
        raise ValueError('MicroPython runtime hex required.')
    if not python_hex:
        return runtime_hex
    py_list = python_hex.split()
    runtime_list = runtime_hex.split()
    embedded_list = []
    # The embedded list should be the original runtime with the Python based
    # hex embedded two lines from the end.
    embedded_list.extend(runtime_list[:-2])
    embedded_list.extend(py_list)
    embedded_list.extend(runtime_list[-2:])
    return '\n'.join(embedded_list) + '\n'


def _get_volume_name(disk_name):
    """
    Each disk or external device connected to windows has an attribute
    called "volume name". This function returns the volume name for
    the given disk/device.

    Code from http://stackoverflow.com/a/12056414
    """
    vol_name_buf = ctypes.create_unicode_buffer(1024)
    serial_number = max_component_length = file_system_flags = fs_name = None
    ctypes.windll.kernel32.GetVolumeInformationW(
        ctypes.c_wchar_p(disk_name),
        vol_name_buf,
        ctypes.sizeof(vol_name_buf),
        serial_number,
        max_component_length,
        file_system_flags,
        fs_name,
        0,
    )
    return vol_name_buf.value


def find_microbit():
    """
    Returns a path on the filesystem that represents the plugged in BBC
    micro:bit to be flashed.

    Returns None if no micro:bit is found.
    """
    # Check what sort of operating system we're on.
    if os.name == 'posix':
        # 'posix' means we're on Linux or OSX (Mac).
        # Call the unix "mount" command to list the mounted volumes.
        mount_output = check_output('mount').splitlines()
        mounted_volumes = [x.split()[2] for x in mount_output]
        for volume in mounted_volumes:
            if volume.endswith(b'MICROBIT'):
                return volume.decode('utf-8')  # Return a string not bytes.
    elif os.name == 'nt':
        # 'nt' means we're on Windows.
        for disk in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            path = '{}:\\'.format(disk)
            if os.path.exists(path) and _get_volume_name(path) == 'MICROBIT':
                return path
    else:
        # We don't support an unknown operating system.
        raise NotImplementedError('OS not supported.')


def save_hex(hex_file, path):
    """
    Given a string representation of a hex file, copies it to the specified
    path thus causing the device mounted at that point to be flashed.

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
    flash it onto the microbit.

    If the path_to_python is unspecified it will simply flash the unmodified
    MicroPython runtime onto the device.

    If the path_to_microbit is unspecified it will attempt to find the device's
    path automatically. If the automatic discovery fails, then it will raise
    an IOError.
    """
    # Check for the correct version of Python.
    if not (sys.version_info[0] == 3 and sys.version_info[1] >= 3):
        raise RuntimeError('Will only run on Python 3.3 or later.')
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
    # Generate the resulting hex file.
    micropython_hex = embed_hex(python_hex, firmware_hex)
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

    Will print help text if the optional first argument is "help". Otherwise
    it will ensure the optional first argument ends in ".py" (the source
    Python script). An optional second argument can reference the path to the
    micro:bit device. Any more arguments are ignored.

    Exceptions are caught and printed back to the user.
    """
    arg_len = len(argv)
    try:
        if arg_len == 0:
            flash()
        elif arg_len >= 1:
            if argv[0] == 'help':
                print(HELP_TEXT)
            if not argv[0].lower().endswith('.py'):
                raise ValueError('Python files must end in ".py".')
            if arg_len == 1:
                flash(argv[0])
            elif arg_len > 1:
                flash(argv[0], argv[1])
    except Exception as ex:
        # The exception of no return. Respond with something nice to the user.
        print(ex)
