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
import hexify

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


def test_main_one_arg():
    """
    Test a simple call to main().
    """
    with mock.patch('uflash.flash') as mock_flash:
        hexify.main(argv=['tests/example.py'])
        mock_flash.assert_called_once_with(path_to_python='tests/example.py',
                                           path_to_runtime=None,
                                           paths_to_microbits=['tests'],
                                           minify=False,
                                           keepname=True)



def test_main_runtime_arg():
    """
    Test a simple call to main().
    """
    with mock.patch('uflash.flash') as mock_flash:
        hexify.main(argv=['tests/example.py', '-r', 'tests/fake.hex'])
        mock_flash.assert_called_once_with(path_to_python='tests/example.py',
                                           path_to_runtime='tests/fake.hex',
                                           paths_to_microbits=['tests'],
                                           minify=False,
                                           keepname=True)


def test_main_minify_arg():
    """
    Test a simple call to main().
    """
    with mock.patch('uflash.flash') as mock_flash:
        hexify.main(argv=['tests/example.py', '-m'])
        mock_flash.assert_called_once_with(path_to_python='tests/example.py',
                                           path_to_runtime=None,
                                           paths_to_microbits=['tests'],
                                           minify=True,
                                           keepname=True)


def test_main_outdir_arg():
    """
    Test a simple call to main().
    """
    with mock.patch('uflash.flash') as mock_flash:
        hexify.main(argv=['tests/example.py', '-o', '/tmp'])
        mock_flash.assert_called_once_with(path_to_python='tests/example.py',
                                           path_to_runtime=None,
                                           paths_to_microbits=['/tmp'],
                                           minify=False,
                                           keepname=True)

