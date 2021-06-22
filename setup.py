#!/usr/bin/env python3
from setuptools import setup
from uflash import get_version


with open("README.rst") as f:
    readme = f.read()
with open("CHANGES.rst") as f:
    changes = f.read()


setup(
    name="uflash",
    version=get_version(),
    description="A module and utility to flash Python onto the BBC micro:bit.",
    long_description=readme + "\n\n" + changes,
    author="Nicholas H.Tollervey",
    author_email="ntoll@ntoll.org",
    url="https://github.com/ntoll/uflash",
    py_modules=["uflash", "py2hex"],
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Education",
        "Topic :: Software Development :: Embedded Systems",
    ],
    python_requires="==2.7.*,>=3.5",
    entry_points={
        "console_scripts": ["uflash=uflash:main", "py2hex=uflash:py2hex"],
    },
)
