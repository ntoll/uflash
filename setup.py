#!/usr/bin/env python
from setuptools import setup

with open('README.rst') as f:
    readme = f.read()
with open('CHANGES.rst') as f:
    changes = f.read()


setup(
    name='uflash',
    version='0.0.1',
    description='A module and utility to flash Python onto the BBC micro:bit.',
    long_description=readme + '\n\n' + changes,
    author='Nicholas H.Tollervey',
    author_email='ntoll@ntoll.org',
    url='http://micropython.org/',
    package_dir={'uflash': 'uflash'},
    package_data={'': ['firmware.hex', 'README.rst', 'CHANGES.rst', 'LICENSE',
                       'AUTHORS']},
    license='MIT',
)
