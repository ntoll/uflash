# -*- coding: utf-8 -*-
"""
Tests for the uflash module.
"""
import ctypes
import os
import os.path
import sys
import tempfile
import time
import threading

import pytest
import uflash

try:
    from unittest import mock
except ImportError:
    import mock
else:
    # mock_open can't read binary data in < 3.4.3
    # https://bugs.python.org/issue23004
    if (3, 4) <= sys.version_info < (3, 4, 3):
        import mock


if sys.version_info.major == 2:
    import __builtin__ as builtins
else:
    import builtins


TEST_SCRIPT = b"""from microbit import *

display.scroll('Hello, World!')
"""

TEST_SCRIPT_FS = b'This is a slightly longer bit of test that ' \
    b'should be more than a single block\nThis is a slightly longer bit of ' \
    b'test that should be more than a single block'
TEST_SCRIPT_FS_V1_HEX_LIST = [
    ':020000040003F7',
    ':108C0000FE26076D61696E2E70795468697320695C',
    ':108C100073206120736C696768746C79206C6F6E67',
    ':108C200067657220626974206F66207465737420B2',
    ':108C3000746861742073686F756C64206265206D60',
    ':108C40006F7265207468616E20612073696E676C55',
    ':108C50006520626C6F636B0A5468697320697320C6',
    ':108C60006120736C696768746C79206C6F6E6765DE',
    ':108C70007220626974206F662074657374207402B8',
    ':108C8000016861742073686F756C64206265206D83',
    ':108C90006F7265207468616E20612073696E676C05',
    ':108CA0006520626C6F636BFFFFFFFFFFFFFFFFFF3D',
    ':108CB000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC4',
    ':108CC000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFB4',
    ':108CD000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFA4',
    ':108CE000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF94',
    ':108CF000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF84',
    ':01F80000FD0A',
]
TEST_SCRIPT_FS_V2_HEX_LIST = [
    ':020000040006F4',
    ':10D0000DFE26076D61696E2E70795468697320690B',
    ':10D0100D73206120736C696768746C79206C6F6E16',
    ':10D0200D67657220626974206F6620746573742061',
    ':10D0300D746861742073686F756C64206265206D0F',
    ':10D0400D6F7265207468616E20612073696E676C04',
    ':10D0500D6520626C6F636B0A546869732069732075',
    ':10D0600D6120736C696768746C79206C6F6E67658D',
    ':10D0700D7220626974206F66207465737420740267',
    ':10D0800D016861742073686F756C64206265206D32',
    ':10D0900D6F7265207468616E20612073696E676CB4',
    ':10D0A00D6520626C6F636BFFFFFFFFFFFFFFFFFFEC',
    ':10D0B00DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF73',
    ':10D0C00DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF63',
    ':10D0D00DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF53',
    ':10D0E00DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF43',
    ':10D0F00DFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF33',
    ':020000040007F3',
    ':0120000DFDD5',
]


def test_get_version():
    """
    Ensure a call to get_version returns the expected string.
    """
    result = uflash.get_version()
    assert result == '.'.join([str(i) for i in uflash._VERSION])


def test_get_minifier():
    """
    When a minifier was loaded a string identifing it should be
    returned, otherwise None
    """
    with mock.patch('uflash.can_minify', False):
        assert uflash.get_minifier() is None
    with mock.patch('uflash.can_minify', True):
        assert len(uflash.get_minifier()) > 0


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
    Ensure that we can get the script back out using unhexlify and that the
    result is a properly decoded string.
    """
    hexlified = uflash.hexlify(TEST_SCRIPT)
    unhexlified = uflash.unhexlify(hexlified)
    assert unhexlified == TEST_SCRIPT.decode('utf-8')


def test_unhexlify_not_python():
    """
    Test that the MicroPython script start format is present.
    """
    assert '' == uflash.unhexlify(
           ':020000040003F7\n:10E000000000000000000000000000000000000010')


def test_unhexlify_bad_unicode():
    """
    Test that invalid Unicode is dealt gracefully returning an empty string.
    """
    assert '' == uflash.unhexlify(
           ':020000040003F7\n:10E000004D50FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')


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
    start_of_python_from_end = len(py_list) + 5
    start_of_python = len(result_list) - start_of_python_from_end
    assert result_list[start_of_python:-5] == py_list
    # The firmware should enclose the Python correctly.
    firmware_list = uflash._RUNTIME.split()
    assert firmware_list[:-5] == result_list[:-start_of_python_from_end]
    assert firmware_list[-5:] == result_list[-5:]


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
    The script should be returned as a string (if there is one).
    """
    python = uflash.hexlify(TEST_SCRIPT)
    result = uflash.embed_hex(uflash._RUNTIME, python)
    extracted = uflash.extract_script(result)
    assert extracted == TEST_SCRIPT.decode('utf-8')


def test_extract_sandwiched():
    """
    The script hex is packed with additional data above and bellow and should
    still be returned as a the original string only.
    """
    python = uflash.hexlify(TEST_SCRIPT)
    python_hex_lines = python.split('\n')
    python_sandwiched = [python_hex_lines[0]] + \
        [':10DFE000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF41'] + \
        python_hex_lines[1:] + [':10E50000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF1B']
    result = uflash.embed_hex(uflash._RUNTIME, '\n'.join(python_sandwiched))
    extracted = uflash.extract_script(result)
    assert extracted == TEST_SCRIPT.decode('utf-8')


def test_extract_not_valid_hex():
    """
    Return a sensible message if the hex file isn't valid
    """
    assert uflash.extract_script('invalid input') == ''


def test_extract_no_python():
    """
    Ensure that if there's no Python in the input hex then just return an empty
    (False) string.
    """
    assert uflash.extract_script(uflash._RUNTIME) == ''


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
                assert uflash.find_microbit() is None


def test_find_microbit_nt_exists():
    """
    Simulate being on os.name == 'nt' and a disk with a volume name 'MICROBIT'
    exists indicating a connected micro:bit device.
    """
    mock_windll = mock.MagicMock()
    mock_windll.kernel32 = mock.MagicMock()
    mock_windll.kernel32.GetVolumeInformationW = mock.MagicMock()
    mock_windll.kernel32.GetVolumeInformationW.return_value = None
    #
    # Have every drive claim to be removable
    #
    mock_windll.kernel32.GetDriveTypeW = mock.MagicMock()
    mock_windll.kernel32.GetDriveTypeW.return_value = 2
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
                assert uflash.find_microbit() is None


def test_find_microbit_nt_removable_only():
    """
    We should only be considering removable drives as candidates for
    micro:bit devices. (Especially so as to avoid interrogating disconnected
    network drives).

    Have every drive claim to be a micro:bit, but only drive B: claim
    to be removable
    """
    def _drive_type(letter):
        if letter == "B:\\":
            return 2  # removable
        else:
            return 4  # network

    mock_windll = mock.MagicMock()
    mock_windll.kernel32 = mock.MagicMock()
    mock_windll.kernel32.GetVolumeInformationW = mock.MagicMock()
    mock_windll.kernel32.GetVolumeInformationW.return_value = None
    mock_windll.kernel32.GetDriveTypeW = mock.MagicMock()
    mock_windll.kernel32.GetDriveTypeW.side_effect = _drive_type
    with mock.patch('os.name', 'nt'):
        with mock.patch('os.path.exists', return_value=True):
            return_value = ctypes.create_unicode_buffer('MICROBIT')
            with mock.patch('ctypes.create_unicode_buffer',
                            return_value=return_value):
                ctypes.windll = mock_windll
                assert uflash.find_microbit() == 'B:\\'


def test_find_microbit_unknown_os():
    """
    Raises a NotImplementedError if the host OS is not supported.
    """
    with mock.patch('os.name', 'foo'):
        with pytest.raises(NotImplementedError) as ex:
            uflash.find_microbit()
    assert ex.value.args[0] == 'OS "foo" not supported.'


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


def test_flash_with_path_to_multiple_microbits():
    """
    Flash the referenced paths to the micro:bit with a hex file generated from
    the MicroPython firmware and the referenced Python script.
    """
    with mock.patch('uflash.save_hex') as mock_save:
        uflash.flash('tests/example.py', ['test_path1', 'test_path2'])
        assert mock_save.call_count == 2
        # Create the hex we're expecting to flash onto the device.
        with open('tests/example.py', 'rb') as py_file:
            python = uflash.hexlify(py_file.read())
        assert python
        expected_hex = uflash.embed_hex(uflash._RUNTIME, python)

        assert mock_save.call_args_list[0][0][0] == expected_hex
        expected_path = os.path.join('test_path1', 'micropython.hex')
        assert mock_save.call_args_list[0][0][1] == expected_path

        assert mock_save.call_args_list[1][0][0] == expected_hex
        expected_path = os.path.join('test_path2', 'micropython.hex')
        assert mock_save.call_args_list[1][0][1] == expected_path


def test_flash_with_path_to_microbit():
    """
    Flash the referenced path to the micro:bit with a hex file generated from
    the MicroPython firmware and the referenced Python script.
    """
    with mock.patch('uflash.save_hex') as mock_save:
        uflash.flash('tests/example.py', ['test_path'])
        assert mock_save.call_count == 1
        # Create the hex we're expecting to flash onto the device.
        with open('tests/example.py', 'rb') as py_file:
            python = uflash.hexlify(py_file.read())
        assert python
        expected_hex = uflash.embed_hex(uflash._RUNTIME, python)
        assert mock_save.call_args[0][0] == expected_hex
        expected_path = os.path.join('test_path', 'micropython.hex')
        assert mock_save.call_args[0][1] == expected_path


def test_flash_with_keepname():
    """
    Flash the referenced path to the micro:bit with a hex file generated from
    the MicroPython firmware and the referenced Python script and keep the
    original filename root.
    """
    with mock.patch('uflash.save_hex') as mock_save:
        uflash.flash('tests/example.py', ['test_path'], keepname=True)
        assert mock_save.call_count == 1
        # Create the hex we're expecting to flash onto the device.
        with open('tests/example.py', 'rb') as py_file:
            python = uflash.hexlify(py_file.read())
        assert python
        expected_hex = uflash.embed_hex(uflash._RUNTIME, python)
        assert mock_save.call_args[0][0] == expected_hex
        expected_path = os.path.join('test_path', 'example.hex')
        assert mock_save.call_args[0][1] == expected_path


def test_main_keepname_message(capsys):
    """
    Ensure that the correct message appears when called as from py2hex.
    """
    uflash.flash('tests/example.py', paths_to_microbits=['tests'],
                 keepname=True)
    stdout, stderr = capsys.readouterr()
    expected = 'Hexifying example.py as: tests/example.hex'
    assert (expected in stdout) or (expected in stderr)


def test_flash_with_path_to_runtime():
    """
    Use the referenced runtime hex file when building the hex file to be
    flashed onto the device.
    """
    mock_o = mock.mock_open(read_data=b'script')
    with mock.patch.object(builtins, 'open', mock_o) as mock_open:
        with mock.patch('uflash.embed_hex', return_value='foo') as em_h:
            with mock.patch('uflash.find_microbit', return_value='bar'):
                with mock.patch('uflash.save_hex') as mock_save:
                    uflash.flash('tests/example.py',
                                 path_to_runtime='tests/fake.hex')
                    assert mock_open.call_args[0][0] == 'tests/fake.hex'
                    assert em_h.call_args[0][0] == b'script'
                    expected_hex_path = os.path.join('bar', 'micropython.hex')
                    mock_save.assert_called_once_with('foo', expected_hex_path)


def test_flash_with_python_script():
    """
    If a byte representation of a Python script is passed into the function it
    should hexlify that.
    """
    python_script = b'import this'
    with mock.patch('uflash.save_hex'):
        with mock.patch('uflash.find_microbit', return_value='bar'):
            with mock.patch('uflash.hexlify') as mock_hexlify:
                uflash.flash(python_script=python_script)
                mock_hexlify.assert_called_once_with(python_script, False)


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
    for version in [(2, 6, 3), (3, 2, 0)]:
        with pytest.raises(RuntimeError) as ex:
            with mock.patch('sys.version_info', version):
                uflash.flash()
            assert 'Will only run on Python ' in ex.value.args[0]


def test_hexlify_minify_without_minifier():
    """
    When minification but no minifier is available a ValueError
    should be raised
    """
    with pytest.raises(ValueError):
        with mock.patch('uflash.can_minify', False):
            uflash.hexlify(TEST_SCRIPT, minify=True)


def test_hexlify_minify():
    """
    Check mangle is called as expected
    """
    with mock.patch('nudatus.mangle') as mangle:
        uflash.hexlify(TEST_SCRIPT, minify=True)
        mangle.assert_called_once_with(TEST_SCRIPT.decode('utf-8'))


def test_main_no_args():
    """
    If there are no args into the main function, it simply calls flash with
    no arguments.
    """
    with mock.patch('sys.argv', ['uflash', ]):
        with mock.patch('uflash.flash') as mock_flash:
            uflash.main()
            mock_flash.assert_called_once_with(path_to_python=None,
                                               paths_to_microbits=[],
                                               path_to_runtime=None,
                                               minify=False,
                                               keepname=False)


def test_main_first_arg_python():
    """
    If there is a single argument that ends with ".py", it calls flash with
    it as the path to the source Python file.
    """
    with mock.patch('uflash.flash') as mock_flash:
        uflash.main(argv=['foo.py'])
        mock_flash.assert_called_once_with(path_to_python='foo.py',
                                           paths_to_microbits=[],
                                           path_to_runtime=None,
                                           minify=False,
                                           keepname=False)


def test_main_first_arg_help(capsys):
    """
    If there is a single argument of "--help", it prints some help and exits.
    """
    with pytest.raises(SystemExit):
        uflash.main(argv=['--help'])

    stdout, _ = capsys.readouterr()
    # argparse manipulates the help text (e.g. changes line wrap)
    # so it isn't trivial to compare the output to uflash._HELP_TEXT.
    expected = 'Flash Python onto the BBC micro:bit'
    assert expected in stdout


def test_main_first_arg_version(capsys):
    """
    If there is a single argument of "--version", it prints the version
    and exits.
    """
    with pytest.raises(SystemExit):
        uflash.main(argv=['--version'])

    stdout, stderr = capsys.readouterr()
    expected = uflash.get_version()
    # On python 2 --version prints to stderr. On python 3 to stdout.
    # https://bugs.python.org/issue18920
    assert (expected in stdout) or (expected in stderr)


def test_main_first_arg_not_python(capsys):
    """
    If the first argument does not end in ".py" then it should display a useful
    error message.
    """
    with pytest.raises(SystemExit):
        uflash.main(argv=['foo.bar'])

    _, stderr = capsys.readouterr()
    expected = 'Python files must end in ".py".'
    assert expected in stderr


def test_flash_raises(capsys):
    """
    If the flash system goes wrong, it should say that's what happened
    """
    with mock.patch('uflash.flash', side_effect=RuntimeError("boom")):
        with pytest.raises(SystemExit):
            uflash.main(argv=['test.py'])

    _, stderr = capsys.readouterr()
    expected = 'Error flashing test.py'
    assert expected in stderr


def test_flash_raises_with_info(capsys):
    """
    When flash goes wrong it should mention everything you tell it
    """
    with mock.patch('uflash.flash', side_effect=RuntimeError("boom")):
        with pytest.raises(SystemExit):
            uflash.main(argv=['test.py'])

    _, stderr = capsys.readouterr()
    expected = 'Error flashing test.py to microbit: boom\n'
    assert stderr == expected

    with mock.patch('uflash.flash', side_effect=RuntimeError("boom")):
        with pytest.raises(SystemExit):
            uflash.main(argv=['test.py', 'D:\\'])

    _, stderr = capsys.readouterr()
    expected = 'Error flashing test.py to ' + repr(['D:\\']) + ': boom\n'
    assert stderr == expected

    with mock.patch('uflash.flash', side_effect=RuntimeError("boom")):
        with pytest.raises(SystemExit):
            uflash.main(argv=['-r', 'foo.hex', 'test.py', 'D:\\'])

    _, stderr = capsys.readouterr()
    expected = 'Error flashing test.py to ' + repr(['D:\\']) + \
               'with runtime foo.hex: boom\n'
    assert stderr == expected


def test_watch_raises(capsys):
    """
    If the watch system goes wrong, it should say that's what happened
    """
    with mock.patch('uflash.watch_file', side_effect=RuntimeError("boom")):
        with pytest.raises(SystemExit):
            uflash.main(argv=['--watch', 'test.py'])

    _, stderr = capsys.readouterr()
    expected = 'Error watching test.py'
    assert expected in stderr


def test_extract_raises(capsys):
    """
    If the extract system goes wrong, it should say that's what happened
    """
    with mock.patch('uflash.extract', side_effect=RuntimeError("boom")):
        with pytest.raises(SystemExit):
            uflash.main(argv=['--extract', 'test.py'])

    _, stderr = capsys.readouterr()
    expected = 'Error extracting test.py'
    assert expected in stderr


def test_main_two_args():
    """
    If there are two arguments passed into main, then it should pass them onto
    the flash() function.
    """
    with mock.patch('uflash.flash', return_value=None) as mock_flash:
        uflash.main(argv=['foo.py', '/media/foo/bar'])
        mock_flash.assert_called_once_with(
            path_to_python='foo.py',
            paths_to_microbits=['/media/foo/bar'],
            path_to_runtime=None,
            minify=False,
            keepname=False)


def test_main_multiple_microbits():
    """
    If there are more than two arguments passed into main, then it should pass
    them onto the flash() function.
    """
    with mock.patch('uflash.flash', return_value=None) as mock_flash:
        uflash.main(argv=[
            'foo.py', '/media/foo/bar', '/media/foo/baz', '/media/foo/bob'])
        mock_flash.assert_called_once_with(
            path_to_python='foo.py',
            paths_to_microbits=[
                '/media/foo/bar', '/media/foo/baz', '/media/foo/bob'],
            path_to_runtime=None,
            minify=False,
            keepname=False)


def test_main_runtime():
    """
    If there are three arguments passed into main, then it should pass them
    onto the flash() function.
    """
    with mock.patch('uflash.flash') as mock_flash:
        uflash.main(argv=['-r' 'baz.hex', 'foo.py', '/media/foo/bar'])
        mock_flash.assert_called_once_with(
            path_to_python='foo.py',
            paths_to_microbits=['/media/foo/bar'],
            path_to_runtime='baz.hex',
            minify=False,
            keepname=False)


def test_main_named_args():
    """
    Ensure that named arguments are passed on properly to the flash() function.
    """
    with mock.patch('uflash.flash') as mock_flash:
        uflash.main(argv=['-r', 'baz.hex'])
        mock_flash.assert_called_once_with(path_to_python=None,
                                           paths_to_microbits=[],
                                           path_to_runtime='baz.hex',
                                           minify=False,
                                           keepname=False)


def test_main_watch_flag():
    """
    The watch flag cause a call the correct function.
    """
    with mock.patch('uflash.watch_file') as mock_watch_file:
        uflash.main(argv=['-w'])
        mock_watch_file.assert_called_once_with(None,
                                                uflash.flash,
                                                path_to_python=None,
                                                paths_to_microbits=[],
                                                path_to_runtime=None)


def test_extract_command():
    """
    Test the command-line script extract feature
    """
    with mock.patch('uflash.extract') as mock_extract:
        uflash.main(argv=['-e', 'hex.hex', 'foo.py'])
        mock_extract.assert_called_once_with('hex.hex', ['foo.py'])


def test_extract_paths():
    """
    Test the different paths of the extract() function.
    It should open and extract the contents of the file (input arg)
    When called with only an input it should print the output of extract_script
    When called with two arguments it should write the output to the output arg
    """
    mock_e = mock.MagicMock(return_value=b'print("hello, world!")')
    mock_o = mock.mock_open(read_data='script')

    with mock.patch('uflash.extract_script', mock_e) as mock_extract_script, \
            mock.patch.object(builtins, 'print') as mock_print, \
            mock.patch.object(builtins, 'open', mock_o) as mock_open:
        uflash.extract('foo.hex')
        mock_open.assert_called_once_with('foo.hex', 'r')
        mock_extract_script.assert_called_once_with('script')
        mock_print.assert_called_once_with(b'print("hello, world!")')

        uflash.extract('foo.hex', 'out.py')
        assert mock_open.call_count == 3
        mock_open.assert_called_with('out.py', 'w')
        assert mock_open.return_value.write.call_count == 1


def test_extract_command_source_only():
    """
    If there is no target file the extract command should write to stdout.
    """
    mock_e = mock.MagicMock(return_value=b'print("hello, world!")')
    mock_o = mock.mock_open(read_data='script')
    with mock.patch('uflash.extract_script', mock_e) as mock_extract_script, \
            mock.patch.object(builtins, 'open', mock_o) as mock_open, \
            mock.patch.object(builtins, 'print') as mock_print:
        uflash.main(argv=['-e', 'hex.hex'])
        mock_open.assert_any_call('hex.hex', 'r')
        mock_extract_script.assert_called_once_with('script')
        mock_print.assert_any_call(b'print("hello, world!")')


def test_extract_command_no_source():
    """
    If there is no source file the extract command should complain
    """
    with pytest.raises(TypeError):
        uflash.extract(None, None)


def test_watch_no_source():
    """
    If there is no source file the watch command should complain.
    """
    with pytest.raises(ValueError):
        uflash.watch_file(None, lambda: "should never be called!")


@mock.patch('uflash.time')
@mock.patch('uflash.os')
def test_watch_file(mock_os, mock_time):
    """
    Make sure that the callback is called each time the file changes.
    """
    # Our function will throw KeyboardInterrupt when called for the 2nd time,
    # ending the watching gracefully.This will help in testing the
    # watch_file function.
    call_count = [0]

    def func():
        call_count[0] = call_count[0] + 1
        if call_count[0] == 2:
            raise KeyboardInterrupt()

    # Instead of modifying any file, let's change the return value of
    # os.path.getmtime. Start with initial value of 0.
    mock_os.path.getmtime.return_value = 0

    t = threading.Thread(target=uflash.watch_file,
                         args=('path/to/file', func))
    t.start()
    time.sleep(0.01)
    mock_os.path.getmtime.return_value = 1  # Simulate file change
    time.sleep(0.01)
    assert t.is_alive()
    assert call_count[0] == 1
    mock_os.path.getmtime.return_value = 2  # Simulate file change
    t.join()
    assert call_count[0] == 2


def test_hexlify_validates_script_length():
    input = b"A" * 8193
    with pytest.raises(ValueError) as excinfo:
        uflash.hexlify(input)
    assert str(excinfo.value) == "Python script must be less than 8188 bytes."


def test_py2hex_one_arg():
    """
    Test a simple call to main().
    """
    with mock.patch('uflash.flash') as mock_flash:
        uflash.py2hex(argv=['tests/example.py'])
        mock_flash.assert_called_once_with(path_to_python='tests/example.py',
                                           path_to_runtime=None,
                                           paths_to_microbits=['tests'],
                                           minify=False,
                                           keepname=True)


def test_py2hex_runtime_arg():
    """
    Test a simple call to main().
    """
    with mock.patch('uflash.flash') as mock_flash:
        uflash.py2hex(argv=['tests/example.py', '-r', 'tests/fake.hex'])
        mock_flash.assert_called_once_with(path_to_python='tests/example.py',
                                           path_to_runtime='tests/fake.hex',
                                           paths_to_microbits=['tests'],
                                           minify=False,
                                           keepname=True)


def test_py2hex_minify_arg():
    """
    Test a simple call to main().
    """
    with mock.patch('uflash.flash') as mock_flash:
        uflash.py2hex(argv=['tests/example.py', '-m'])
        mock_flash.assert_called_once_with(path_to_python='tests/example.py',
                                           path_to_runtime=None,
                                           paths_to_microbits=['tests'],
                                           minify=True,
                                           keepname=True)


def test_py2hex_outdir_arg():
    """
    Test a simple call to main().
    """
    with mock.patch('uflash.flash') as mock_flash:
        uflash.py2hex(argv=['tests/example.py', '-o', '/tmp'])
        mock_flash.assert_called_once_with(path_to_python='tests/example.py',
                                           path_to_runtime=None,
                                           paths_to_microbits=['/tmp'],
                                           minify=False,
                                           keepname=True)


def test_bytes_to_ihex():
    """
    Test bytes_to_ihex golden path for V1.
    """
    data = b'A' * 32
    expected_result = '\n'.join([
        ':020000040003F7',
        ':108C10004141414141414141414141414141414144',
        ':108C20004141414141414141414141414141414134',
    ])

    result = uflash.bytes_to_ihex(0x38C10, data, universal_data_record=False)

    assert result == expected_result


def test_bytes_to_ihex_universal():
    """
    Test bytes_to_ihex golden path for V2.
    """
    data = b'A' * 32
    expected_result = '\n'.join([
        ':020000040003F7',
        ':108C100D4141414141414141414141414141414137',
        ':108C200D4141414141414141414141414141414127',
    ])

    result = uflash.bytes_to_ihex(0x38C10, data, universal_data_record=True)

    assert result == expected_result


def test_bytes_to_ihex_inner_extended_linear_address_record():
    """
    Test bytes_to_ihex golden path for V2.
    """
    data = b'A' * 32
    expected_result = '\n'.join([
        ':020000040003F7',
        ':10FFF00D41414141414141414141414141414141E4',
        ':020000040004F6',
        ':1000000D41414141414141414141414141414141D3',
    ])

    result = uflash.bytes_to_ihex(0x3FFF0, data, universal_data_record=True)

    assert result == expected_result


def test_script_to_fs():
    """
    Test script_to_fs with a random example without anything special about it.
    """
    script = b'A' * 364
    expected_result = '\n'.join([
        ':020000040003F7',
        ':108C0000FE79076D61696E2E7079414141414141A4',
        ':108C10004141414141414141414141414141414144',
        ':108C20004141414141414141414141414141414134',
        ':108C30004141414141414141414141414141414124',
        ':108C40004141414141414141414141414141414114',
        ':108C50004141414141414141414141414141414104',
        ':108C600041414141414141414141414141414141F4',
        ':108C70004141414141414141414141414141410223',
        ':108C80000141414141414141414141414141414114',
        ':108C900041414141414141414141414141414141C4',
        ':108CA00041414141414141414141414141414141B4',
        ':108CB00041414141414141414141414141414141A4',
        ':108CC0004141414141414141414141414141414194',
        ':108CD0004141414141414141414141414141414184',
        ':108CE0004141414141414141414141414141414174',
        ':108CF00041414141414141414141414141414103A2',
        ':108D00000241414141414141414141414141414192',
        ':108D10004141414141414141414141414141414143',
        ':108D20004141414141414141414141414141414133',
        ':108D30004141414141414141414141414141414123',
        ':108D40004141414141414141414141414141414113',
        ':108D50004141414141414141414141414141414103',
        ':108D600041414141414141414141414141414141F3',
        ':108D700041414141414141414141FFFFFFFFFFFF6F',
        ':01F80000FD0A',
        '',
    ])

    with mock.patch('uflash._FS_START_ADDR_V1', 0x38C00), \
            mock.patch('uflash._FS_END_ADDR_V1', 0x3F800):
        result = uflash.script_to_fs(script, uflash._MICROBIT_ID_V1)

    assert result == expected_result, script


def test_script_to_fs_short():
    """
    Test script_to_fs with a script smaller than a fs chunk.
    """
    script = b'Very short example'
    expected_result = '\n'.join([
        ':020000040003F7',
        ':108C0000FE1B076D61696E2E70795665727920734F',
        ':108C1000686F7274206578616D706C65FFFFFFFF8F',
        ':108C2000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF54',
        ':108C3000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF44',
        ':108C4000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF34',
        ':108C5000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF24',
        ':108C6000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF14',
        ':108C7000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF04',
        ':01F80000FD0A',
        '',
    ])

    with mock.patch('uflash._FS_START_ADDR_V1', 0x38C00), \
            mock.patch('uflash._FS_END_ADDR_V1', 0x3F800):
        result = uflash.script_to_fs(script, uflash._MICROBIT_ID_V1)

    assert result == expected_result, script


def test_script_to_fs_two_chunks():
    """
    Test script_to_fs with a script that takes two chunks for V1 and V2.
    """
    expected_result_v1 = '\n'.join(TEST_SCRIPT_FS_V1_HEX_LIST + [''])
    expected_result_v2 = '\n'.join(TEST_SCRIPT_FS_V2_HEX_LIST + [''])

    with mock.patch('uflash._FS_START_ADDR_V1', 0x38C00), \
            mock.patch('uflash._FS_END_ADDR_V1', 0x3F800):
        result_v1 = uflash.script_to_fs(TEST_SCRIPT_FS, uflash._MICROBIT_ID_V1)
        result_v2 = uflash.script_to_fs(TEST_SCRIPT_FS, uflash._MICROBIT_ID_V2)

    assert result_v1 == expected_result_v1
    assert result_v2 == expected_result_v2


def test_script_to_fs_chunk_boundary():
    """
    Test script_to_fs edge case with the taking exactly one chunk.
    """
    script_short = b'This is an edge case test to fill the last byte of ' \
                   b'the first chunk.\n' + (b'A' * 48)
    expected_result_short = '\n'.join([
        ':020000040003F7',
        ':108C0000FE7D076D61696E2E707954686973206905',
        ':108C10007320616E206564676520636173652074ED',
        ':108C200065737420746F2066696C6C2074686520AD',
        ':108C30006C6173742062797465206F662074686556',
        ':108C4000206669727374206368756E6B2E0A4141E9',
        ':108C50004141414141414141414141414141414104',
        ':108C600041414141414141414141414141414141F4',
        ':108C70004141414141414141414141414141FFFF68',
        ':01F80000FD0A',
        '',
    ])
    script_exact = b'This is an edge case test to fill the last byte of ' \
                   b'the first chunk.\n' + (b'A' * 49)
    expected_result_exact = '\n'.join([
        ':020000040003F7',
        ':108C0000FE00076D61696E2E707954686973206982',
        ':108C10007320616E206564676520636173652074ED',
        ':108C200065737420746F2066696C6C2074686520AD',
        ':108C30006C6173742062797465206F662074686556',
        ':108C4000206669727374206368756E6B2E0A4141E9',
        ':108C50004141414141414141414141414141414104',
        ':108C600041414141414141414141414141414141F4',
        ':108C70004141414141414141414141414141410223',
        ':108C800001FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF2',
        ':108C9000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE4',
        ':108CA000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD4',
        ':108CB000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC4',
        ':108CC000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFB4',
        ':108CD000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFA4',
        ':108CE000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF94',
        ':108CF000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF84',
        ':01F80000FD0A',
        '',
    ])
    script_large = b'This is an edge case test to fill the last byte of ' \
                   b'the first chunk.\n' + (b'A' * 50)
    expected_result_large = '\n'.join([
        ':020000040003F7',
        ':108C0000FE01076D61696E2E707954686973206981',
        ':108C10007320616E206564676520636173652074ED',
        ':108C200065737420746F2066696C6C2074686520AD',
        ':108C30006C6173742062797465206F662074686556',
        ':108C4000206669727374206368756E6B2E0A4141E9',
        ':108C50004141414141414141414141414141414104',
        ':108C600041414141414141414141414141414141F4',
        ':108C70004141414141414141414141414141410223',
        ':108C80000141FFFFFFFFFFFFFFFFFFFFFFFFFFFFB0',
        ':108C9000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE4',
        ':108CA000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFD4',
        ':108CB000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC4',
        ':108CC000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFB4',
        ':108CD000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFA4',
        ':108CE000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF94',
        ':108CF000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF84',
        ':01F80000FD0A',
        '',
    ])

    with mock.patch('uflash._FS_START_ADDR_V1', 0x38C00), \
            mock.patch('uflash._FS_END_ADDR_V1', 0x3F800):
        result_short = uflash.script_to_fs(
            script_short, uflash._MICROBIT_ID_V1
        )
        result_exact = uflash.script_to_fs(
            script_exact, uflash._MICROBIT_ID_V1
        )
        result_large = uflash.script_to_fs(
            script_large, uflash._MICROBIT_ID_V1
        )

    assert result_short == expected_result_short, script_short
    assert result_exact == expected_result_exact, script_exact
    assert result_large == expected_result_large, script_large


def test_script_to_fs_script_too_long():
    """
    Test script_to_fs when the script is too long and won't fit.
    """
    script = (b'shouldfit' * 3023)[:-1]
    _ = uflash.script_to_fs(script, uflash._MICROBIT_ID_V1)

    script += b'1'
    with pytest.raises(ValueError) as ex:
        _ = uflash.script_to_fs(script, uflash._MICROBIT_ID_V1)
    assert 'Python script must be less than' in ex.value.args[0]


def test_script_to_fs_empty_code():
    """
    Test script_to_fs results an empty string if the input code is empty.
    """
    result = uflash.script_to_fs('', uflash._MICROBIT_ID_V1)
    assert result == ''


def test_script_to_fs_line_endings():
    """
    Test script_to_fs converts line endings before embedding script.
    """
    script_win_lines = TEST_SCRIPT_FS.replace(b'\n', b'\r\n')
    script_cr_lines = TEST_SCRIPT_FS.replace(b'\n', b'\r')
    expected_result = '\n'.join(TEST_SCRIPT_FS_V1_HEX_LIST + [''])

    with mock.patch('uflash._FS_START_ADDR_V1', 0x38C00), \
            mock.patch('uflash._FS_END_ADDR_V1', 0x3F800):
        result_win = uflash.script_to_fs(
            script_win_lines, uflash._MICROBIT_ID_V1
        )
        result_cr = uflash.script_to_fs(
            script_cr_lines, uflash._MICROBIT_ID_V1
        )

    assert result_win == expected_result
    assert result_cr == expected_result


def test_script_to_fs_unknown_microbit_id():
    """
    Test script_to_fs when the micro:bit ID is not recognised.
    """
    with pytest.raises(ValueError) as ex:
        _ = uflash.script_to_fs(TEST_SCRIPT_FS, '1234')

    assert 'Incompatible micro:bit ID found: 1234' in ex.value.args[0]


def test_embed_fs_uhex():
    """
    Test embed_fs_uhex to add the filesystem into a Universal Hex with standard
    two sections, one for V1 and one for V2.
    """
    uhex_list = [
        # Section for V1 starts
        ':020000040000FA',
        ':0400000A9900C0DEBB',
        ':1000000000400020218E01005D8E01005F8E010006',
        ':1000100000000000000000000000000000000000E0',
        ':10002000000000000000000000000000618E0100E0',
        ':020000040001F9',
        ':1000000003D13000F8BD4010F3E7331D0122180082',
        ':10001000F8F7B2FD4460EFE7E4B30200F0B5070083',
        ':1000200089B000201E000D00019215F0ECFB0E4B74',
        ':10003000040007609F4203D1042302791343037134',
        ':0888B00095880100C1000000E1',
        # V1 UICR
        ':020000041000EA',
        ':1010C0007CB0EE17FFFFFFFF0A0000000000E30006',
        ':0C10D000FFFFFFFF2D6D0300000000007B',
        # Section for V2 starts
        ':020000040000FA',
        ':0400000A9903C0DEB8',
        ':1000000D00040020810A000015070000610A0000AD',
        ':1000100D1F07000029070000330700000000000043',
        ':1000200D000000000000000000000000A50A000014',
        ':1000300D3D070000000000004707000051070000C9',
        # V2 UICR
        ':020000041000EA',
        ':0810140D0070070000E0070069',
        # V2 Regions table (this in flash again)
        ':020000040006F4',
        ':102FC00D0100010000B00100000000000000000041',
        ':102FD00D02021C00E46504009CA105000000000035',
        ':102FE00D03006D0000600000000000000000000004',
        ':102FF00DFE307F590100300003000C009DD7B1C198',
        ':00000001FF',
        ''
    ]
    uhex = '\n'.join(uhex_list)
    v1_fs_i = 11
    v2_fs_i = 20
    expected_uhex = '\n'.join(
        uhex_list[:v1_fs_i] +
        TEST_SCRIPT_FS_V1_HEX_LIST +
        uhex_list[v1_fs_i:v2_fs_i] +
        TEST_SCRIPT_FS_V2_HEX_LIST +
        uhex_list[v2_fs_i:]
    )

    with mock.patch('uflash._FS_START_ADDR_V1', 0x38C00), \
            mock.patch('uflash._FS_END_ADDR_V1', 0x3F800), \
            mock.patch('uflash._FS_START_ADDR_V2', 0x6D000), \
            mock.patch('uflash._FS_END_ADDR_V2', 0x72000):
        uhex_with_fs = uflash.embed_fs_uhex(uhex, TEST_SCRIPT_FS)

    assert expected_uhex == uhex_with_fs


def test_embed_fs_uhex_extra_uicr_jump_record():
    uhex_list = [
        # Section for V1 starts
        ':020000040000FA',
        ':0400000A9900C0DEBB',
        ':1000000000400020218E01005D8E01005F8E010006',
        ':1000100000000000000000000000000000000000E0',
        ':10002000000000000000000000000000618E0100E0',
        ':10003000040007609F4203D1042302791343037134',
        ':0888B00095880100C1000000E1',
        # V1 UICR
        ':020000041000EA',
        ':1010C0007CB0EE17FFFFFFFF0A0000000000E30006',
        ':0C10D000FFFFFFFF2D6D0300000000007B',
        # Section for V2 starts
        ':020000040000FA',
        ':0400000A9903C0DEB8',
        ':1000000D00040020810A000015070000610A0000AD',
        ':020000040001F9',
        ':1000000D03D13000F8BD4010F3E7331D0122180082',
        ':1000100DF8F7B2FD4460EFE7E4B30200F0B5070083',
        ':1000200D89B000201E000D00019215F0ECFB0E4B74',
        # V2 UICR with an extra extended linear address record
        ':020000040000FA',
        ':020000041000EA',
        ':0810140D0070070000E0070069',
        # V2 Regions table (this in flash again)
        ':020000040006F4',
        ':102FC00D0100010000B00100000000000000000041',
        ':102FD00D02021C00E46504009CA105000000000035',
        ':102FE00D03006D0000600000000000000000000004',
        ':102FF00DFE307F590100300003000C009DD7B1C198',
        ':00000001FF',
        ''
    ]
    uhex_ela_record = '\n'.join(uhex_list)
    v1_fs_i = 7
    v2_fs_i = 17
    expected_uhex_ela_record = '\n'.join(
        uhex_list[:v1_fs_i] +
        TEST_SCRIPT_FS_V1_HEX_LIST +
        uhex_list[v1_fs_i:v2_fs_i] +
        TEST_SCRIPT_FS_V2_HEX_LIST +
        uhex_list[v2_fs_i:]
    )
    # Replace Extended linear Address with Segmented record
    uhex_list[v2_fs_i] = ':020000020000FC'
    uhex_esa_record = '\n'.join(uhex_list)
    expected_uhex_esa_record = '\n'.join(
        uhex_list[:v1_fs_i] +
        TEST_SCRIPT_FS_V1_HEX_LIST +
        uhex_list[v1_fs_i:v2_fs_i] +
        TEST_SCRIPT_FS_V2_HEX_LIST +
        uhex_list[v2_fs_i:]
    )

    with mock.patch('uflash._FS_START_ADDR_V1', 0x38C00), \
            mock.patch('uflash._FS_END_ADDR_V1', 0x3F800), \
            mock.patch('uflash._FS_START_ADDR_V2', 0x6D000), \
            mock.patch('uflash._FS_END_ADDR_V2', 0x72000):
        uhex_ela_with_fs = uflash.embed_fs_uhex(
            uhex_ela_record, TEST_SCRIPT_FS
        )
        uhex_esa_with_fs = uflash.embed_fs_uhex(
            uhex_esa_record, TEST_SCRIPT_FS
        )

    assert expected_uhex_ela_record == uhex_ela_with_fs
    assert expected_uhex_esa_record == uhex_esa_with_fs
