# -*- coding: utf-8 -*-
"""
Tests for the uflash module.
"""
import tempfile
import os
import os.path
import ctypes
from unittest import mock

import pytest
import uflash


TEST_SCRIPT = b"""from microbit import *

display.scroll('Hello, World!')
"""


def test_hexlify():
    """
    Ensure we get the expected .hex encoded result from a "good" call to the
    function.
    """
    result = uflash.hexlify(TEST_SCRIPT)
    lines = result.split()
    # The first line should be the extended linear address, ox0003
    assert lines[0] == ':020000040003F7'
    # There should be the expected number of lines.
    assert len(lines) == 5


def test_hexlify_empty_script():
    """
    The function returns an empty string if the script is empty.
    """
    assert uflash.hexlify('') == ''


def test_embed_hex():
    """
    Ensure the good case works as expected.
    """
    with open('firmware.hex', 'r') as firmware_file:
        firmware = firmware_file.read()
    assert firmware
    python = uflash.hexlify(TEST_SCRIPT)
    result = uflash.embed_hex(python, firmware)
    # The resulting hex should be of the expected length.
    assert len(result) == len(python) + len(firmware) + 1  # +1 for final \n
    # The hex should end with a newline '\n'
    assert result[-1:] == '\n'
    # The Python hex should be in the correct location.
    py_list = python.split()
    result_list = result.split()
    start_of_python_from_end = len(py_list) + 2
    start_of_python = len(result_list) - start_of_python_from_end
    assert result_list[start_of_python:-2] == py_list
    # The firmware should enclose the Python correctly.
    firmware_list = firmware.split()
    assert firmware_list[:-2] == result_list[:-start_of_python_from_end]
    assert firmware_list[-2:] == result_list[-2:]


def test_embed_no_python():
    """
    The function returns the firmware hex value if there is no Python hex.
    """
    assert uflash.embed_hex('', 'foo') == 'foo'


def test_embed_no_firmware():
    """
    The function returns an empty string if there is no firmware hex.
    """
    assert uflash.embed_hex('foo', '') == ''


def test_find_microbit_posix_exists():
    """
    Simulate being on os.name == 'posix' and a call to "mount" returns a
    record indicating a connected micro:bit device.
    """
    with open('tests/mount_exists.txt', 'rb') as fixture_file:
        fixture = fixture_file.read()
        with mock.patch('os.name', 'posix'):
            with mock.patch('uflash.check_output', return_value=fixture):
                assert uflash.find_microbit() == '/media/ntoll/MICROBIT'


def test_find_microbit_posix_missing():
    """
    Simulate being on os.name == 'posix' and a call to "mount" returns a
    no records associated with a micro:bit device.
    """
    with open('tests/mount_missing.txt', 'rb') as fixture_file:
        fixture = fixture_file.read()
        with mock.patch('os.name', 'posix'):
            with mock.patch('uflash.check_output', return_value=fixture):
                assert uflash.find_microbit() == None


def test_find_microbit_nt_exists():
    """
    Simulate being on os.name == 'nt' and a disk with a volume name 'MICROBIT'
    exists indicating a connected micro:bit device.
    """
    mock_windll = mock.MagicMock()
    mock_windll.kernel32 = mock.MagicMock()
    mock_windll.kernel32.GetVolumeInformationW = mock.MagicMock()
    mock_windll.kernel32.GetVolumeInformationW.return_value = None
    with mock.patch('os.name', 'nt'):
        with mock.patch('os.path.exists', return_value=True):
            return_value = ctypes.create_unicode_buffer('MICROBIT')
            with mock.patch('ctypes.create_unicode_buffer',
                            return_value=return_value):
                ctypes.windll = mock_windll
                assert uflash.find_microbit() == 'A:\\'


def test_find_microbit_nt_missing():
    """
    Simulate being on os.name == 'nt' and a disk with a volume name 'MICROBIT'
    does not exist for a micro:bit device.
    """
    mock_windll = mock.MagicMock()
    mock_windll.kernel32 = mock.MagicMock()
    mock_windll.kernel32.GetVolumeInformationW = mock.MagicMock()
    mock_windll.kernel32.GetVolumeInformationW.return_value = None
    with mock.patch('os.name', 'nt'):
        with mock.patch('os.path.exists', return_value=True):
            return_value = ctypes.create_unicode_buffer(1024)
            with mock.patch('ctypes.create_unicode_buffer',
                            return_value=return_value):
                ctypes.windll = mock_windll
                assert uflash.find_microbit() == None


def test_save_hex():
    """
    Ensure the good case works.
    """
    # Ensure we have a temporary file to write to that doesn't already exist.
    path_to_hex = os.path.join(tempfile.gettempdir(), 'microbit.hex')
    if os.path.exists(path_to_hex):
        os.remove(path_to_hex)
    assert not os.path.exists(path_to_hex)
    # Create the hex file we want to "flash"
    with open('firmware.hex', 'r') as firmware_file:
        firmware = firmware_file.read()
    assert firmware
    python = uflash.hexlify(TEST_SCRIPT)
    hex_file = uflash.embed_hex(python, firmware)
    # Save the hex.
    uflash.save_hex(hex_file, path_to_hex)
    # Ensure the hex has been written as expected.
    assert os.path.exists(path_to_hex)
    with open(path_to_hex) as written_file:
        assert written_file.read() == hex_file


def test_save_hex_no_hex():
    """
    The function raises a ValueError if no hex content is provided.
    """
    with pytest.raises(ValueError) as ex:
        uflash.save_hex('', 'foo')
    assert ex.value.args[0] == 'Cannot flash an empty .hex file.'


def test_save_hex_path_not_to_hex_file():
    """
    The function raises a ValueError if the path is NOT to a .hex file.
    """
    with pytest.raises(ValueError) as ex:
        uflash.save_hex('foo', '')
    assert ex.value.args[0] == 'The path to flash must be for a .hex file.'


def test_flash_no_args():
    """
    The good case. When it's possible to find a path to the micro:bit.
    """
    assert False


def test_flash_no_path_to_microbit():
    """
    The good case. When it's possible to find a path to the micro:bit.
    """
    assert False


def test_flash_no_path_to_python():
    """
    Flash the referenced path to the micro:bit with the unmodified MicroPython
    firmware.
    """
    assert False


def test_flash_with_paths():
    """
    Flash the referenced path to the micro:bit with a hex file generated from
    the MicroPython firmware and the referenced Python script.
    """
    assert False


def test_flash_cannot_find_microbit():
    """
    Ensure an IOError is raised if it is not possible to find the micro:bit.
    """
    assert False
