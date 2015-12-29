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


def test_get_version():
    """
    Ensure a call to get_version returns the expected string.
    """
    result = uflash.get_version()
    assert result == '.'.join([str(i) for i in uflash._VERSION])


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


def test_unhexlify():
    """
    Ensure that we can get the script back out using unhexlify
    """
    hexlified = uflash.hexlify(TEST_SCRIPT)
    unhexlified = uflash.unhexlify(hexlified)
    assert unhexlified == TEST_SCRIPT


def test_hexlify_empty_script():
    """
    The function returns an empty string if the script is empty.
    """
    assert uflash.hexlify('') == ''


def test_embed_hex():
    """
    Ensure the good case works as expected.
    """
    python = uflash.hexlify(TEST_SCRIPT)
    result = uflash.embed_hex(uflash._RUNTIME, python)
    # The resulting hex should be of the expected length.
    assert len(result) == len(python) + len(uflash._RUNTIME) + 1  # +1 for \n
    # The hex should end with a newline '\n'
    assert result[-1:] == '\n'
    # The Python hex should be in the correct location.
    py_list = python.split()
    result_list = result.split()
    start_of_python_from_end = len(py_list) + 2
    start_of_python = len(result_list) - start_of_python_from_end
    assert result_list[start_of_python:-2] == py_list
    # The firmware should enclose the Python correctly.
    firmware_list = uflash._RUNTIME.split()
    assert firmware_list[:-2] == result_list[:-start_of_python_from_end]
    assert firmware_list[-2:] == result_list[-2:]


def test_embed_no_python():
    """
    The function returns the firmware hex value if there is no Python hex.
    """
    assert uflash.embed_hex('foo') == 'foo'


def test_embed_no_runtime():
    """
    The function raises a ValueError if there is no runtime hex.
    """
    with pytest.raises(ValueError) as ex:
        uflash.embed_hex(None)
    assert ex.value.args[0] == 'MicroPython runtime hex required.'


def test_extract():
    """
    The script should be returned if there is one
    """
    python = uflash.hexlify(TEST_SCRIPT)
    result = uflash.embed_hex(uflash._RUNTIME, python)
    extracted = uflash.extract_script(result)
    assert extracted == TEST_SCRIPT


def test_extract_not_valid_hex():
    """
    Return a sensible message if the hex file isn't valid
    """
    with pytest.raises(ValueError) as e:
        uflash.extract_script('invalid input')
    assert 'Bad input hex file' in e.value.args[0]


def test_extract_no_python():
    """
    What to do here?
    """
    assert uflash.extract_script(uflash._RUNTIME) == b''


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


def test_find_microbit_unknown_os():
    """
    Raises a NotImplementedError if the host OS is not supported.
    """
    with mock.patch('os.name', 'foo'):
        with pytest.raises(NotImplementedError) as ex:
            uflash.find_microbit()
    assert ex.value.args[0] == 'OS not supported.'


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
    python = uflash.hexlify(TEST_SCRIPT)
    hex_file = uflash.embed_hex(uflash._RUNTIME, python)
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
    The good case with no arguments to the flash() function. When it's
    possible to find a path to the micro:bit.

    If no path to a Python script is supplied then just flash the unmodified
    MicroPython firmware onto the device.
    """
    with mock.patch('uflash.find_microbit', return_value='foo'):
        with mock.patch('uflash.save_hex') as mock_save:
            uflash.flash()
            assert mock_save.call_count == 1
            assert mock_save.call_args[0][0] == uflash._RUNTIME
            expected_path = os.path.join('foo', 'micropython.hex')
            assert mock_save.call_args[0][1] == expected_path


def test_flash_has_python_no_path_to_microbit():
    """
    The good case with a path to a Python file. When it's possible to find a
    path to the micro:bit.

    The resulting payload should be a correctly created micropython.hex file.
    """
    with mock.patch('uflash.find_microbit', return_value='foo'):
        with mock.patch('uflash.save_hex') as mock_save:
            uflash.flash('tests/example.py')
            assert mock_save.call_count == 1
            # Create the hex we're expecting to flash onto the device.
            with open('tests/example.py', 'rb') as py_file:
                python = uflash.hexlify(py_file.read())
            assert python
            expected_hex = uflash.embed_hex(uflash._RUNTIME, python)
            assert mock_save.call_args[0][0] == expected_hex
            expected_path = os.path.join('foo', 'micropython.hex')
            assert mock_save.call_args[0][1] == expected_path


def test_flash_with_paths():
    """
    Flash the referenced path to the micro:bit with a hex file generated from
    the MicroPython firmware and the referenced Python script.
    """
    with mock.patch('uflash.save_hex') as mock_save:
        uflash.flash('tests/example.py', 'test_path')
        assert mock_save.call_count == 1
        # Create the hex we're expecting to flash onto the device.
        with open('tests/example.py', 'rb') as py_file:
            python = uflash.hexlify(py_file.read())
        assert python
        expected_hex = uflash.embed_hex(uflash._RUNTIME, python)
        assert mock_save.call_args[0][0] == expected_hex
        expected_path = os.path.join('test_path', 'micropython.hex')
        assert mock_save.call_args[0][1] == expected_path


def test_flash_cannot_find_microbit():
    """
    Ensure an IOError is raised if it is not possible to find the micro:bit.
    """
    with mock.patch('uflash.find_microbit', return_value=None):
        with pytest.raises(IOError) as ex:
            uflash.flash()
        expected = 'Unable to find micro:bit. Is it plugged in?'
    assert ex.value.args[0] == expected


def test_flash_wrong_python():
    """
    Ensures a call to flash will fail if it's not reported that we're using
    Python 3.
    """
    with mock.patch('sys.version_info', (2, 7, 9)):
        with pytest.raises(RuntimeError) as ex:
            uflash.flash()
    assert ex.value.args[0] == 'Will only run on Python 3.3 or later.'


def test_main_no_args():
    """
    If there are no args into the main function, it simply calls flash with
    no arguments.
    """
    with mock.patch('sys.argv', ['uflash', ]):
        with mock.patch('uflash.flash') as mock_flash:
            uflash.main()
            assert mock_flash.called_once_with(None, None)


def test_main_first_arg_python():
    """
    If there is a single argument that ends with ".py", it calls flash with
    it as the path to the source Python file.
    """
    with mock.patch('uflash.flash') as mock_flash:
        uflash.main(argv=['foo.py'])
        assert mock_flash.called_once_with('foo.py')


def test_main_first_arg_help():
    """
    If there is a single argument of "help", it prints some help.
    """
    with mock.patch('builtins.print') as mock_print:
        uflash.main(argv=['help'])
        assert mock_print.called_once_with(uflash._HELP_TEXT)


def test_main_first_arg_not_python():
    """
    If the first argument does not end in ".py" then it should display a useful
    error message.
    """
    with mock.patch('builtins.print') as mock_print:
        uflash.main(argv=['foo.bar'])
        expected = ValueError('Python files must end in ".py".')
        assert mock_print.called_once_with(expected)


def test_main_two_args():
    """
    If there are two arguments passed into main, then it should pass them onto
    the flash() function.
    """
    with mock.patch('uflash.flash') as mock_flash:
        uflash.main(argv=['foo.py', '/media/foo/bar'])
        assert mock_flash.called_once_with('foo.py', '/media/foo/bar')


def test_extract_command():
    """
    Test the command-line script extract feature
    """
    with mock.patch('uflash.extract') as mock_extract:
        uflash.main(argv=['-e', 'hex.hex', 'foo.py'])
        assert mock_extract.called_once_with('hex.hex', 'foo.py')


def test_extract_paths():
    """
    Test the different paths of the extract() function.
    It should open and extract the contents of the file (input arg)
    When called with only an input it should print the output of extract_script
    When called with two arguments it should write the output to the output arg
    """
    mock_e = mock.MagicMock(return_value=mock.sentinel.script)
    mock_o = mock.MagicMock()
    mock_o.return_value.__enter__ = lambda s: s
    mock_o.return_value.__exit__ = mock.Mock()
    mock_o.return_value.read.return_value = 'script'
    mock_o.return_value.write = mock.Mock()

    with mock.patch('uflash.extract_script', mock_e) as mock_extract_script, \
            mock.patch('builtins.print') as mock_print, \
            mock.patch('builtins.open', mock_o) as mock_open:
        uflash.extract('foo.hex')
        assert mock_open.called_once_with('foo.hex')
        assert mock_extract_script.called_once_with(mock.sentinel.file_handle)
        assert mock_print.called_once_with(mock.sentinel.script)

        uflash.extract('foo.hex', 'out.py')
        assert mock_open.call_count == 3
        assert mock_open.called_with('out.py', 'w')
        assert mock_open.return_value.write.call_count == 1


def test_extract_command_source_only():
    """
    If there is no target file the extract command should write to stdout
    """
    with mock.patch('uflash.extract') as mock_extract:
        uflash.main(argv=['hex.hex'])
        assert mock_extract.called_once_with('hex.hex')


def test_extract_command_no_source():
    """
    If there is no source file the extract command should complain
    """
    with pytest.raises(TypeError):
        uflash.extract(None, None)
