#!/usr/bin/env python
from setuptools import setup

with open('README.rst') as f:
    readme = f.read()
with open('CHANGES.rst') as f:
    changes = f.read()


setup(
    name='uflash',
    version='0.9.0',
    description='A module and utility to flash Python onto the BBC micro:bit.',
    long_description=readme + '\n\n' + changes,
    author='Nicholas H.Tollervey',
    author_email='ntoll@ntoll.org',
    url='https://github.com/ntoll/uflash',
    py_modules=['uflash', ],
    include_package_data=True,
    data_files=[('', ['firmware.hex', ]), ],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Education',
        'Topic :: Software Development :: Embedded Systems',
    ],
    entry_points={
        'console_scripts': ['uflash=uflash:main'],
    }
)
