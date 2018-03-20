Release History
===============

1.1.1
-----

* Update to the latest version of MicroPython for the BBC micro:bit -- fixes a
  bug relating to flooding and the radio module. As always, many thanks to
  Damien George for his work on MicroPython.

1.1.0
-----

* Update to latest version of MicroPython for the BBC micro:bit (many thanks to Damien George for his amazing efforts!).
* Add a --version flag to uflash that causes it to print the current version number (many thanks to Lenz Grimmer for this work).
* Allow uflash to accept the content of a script as well as the path to a script (many thanks to Zander Brown for this work).
* Ensure uflash works nicely / better with external tools (many thanks to Lex Robinson for this work).
* Added copyright and license information to the start of the script.

1.0.8
-----

* Refactor hex extraction to not depend on extended address record before script (thanks Carlos).
* Refactor tox tests to fix Windows related Gremlin (thanks again, Carlos).

1.0.7
-----

* Watch for changes in a script. Automatically flash on save.

1.0.5
-----

* Update runtime to include latest bug fixes and inclusion of input() builtin.
* Detecting drives on Windows 10 no longer causes pop-ups in certain situations.
* Documentation updates.

1.0.4
-----

* Add support for flash multiple microbits.

1.0.3
-----

* Update runtime to include audio and speech modules.

1.0.2
-----

* Update runtime to include the new radio module.

1.0.1
-----

* Update runtime to include file system related changes.

1.0.0.final.0
-------------

* Runtime updated to version 1.0 of MicroPython for the BBC micro:bit.

1.0.0.beta.7
------------

* Runtime update to fix display related bug.

1.0.0.beta.6
------------

* Runtime update to latest version of the DAL (swaps pins 4 and 5).

1.0.0.beta.5
------------

* Runtime update to fix error reporting bug.

1.0.0.beta.4
------------

* Documentation update.
* Help text update.

1.0.0.beta.3
------------

* Add ability to specify a MicroPython runtime to use.
* Test fixes.

1.0.0.beta.2
------------

* Updated to latest version of MicroPython runtime.

1.0.0.beta.1
------------

* Works with Python 2.7 (thanks to @Funkyhat).
* Updated to the latest build of MicroPython for the BBC micro:bit.
* Minor refactoring and updates to the test suite due to MicroPython updates.

0.9.17
------

* Minor code refactor.
* Documentation update.

0.9.14
------

* Feature complete.
* Comprehensive test suite - 100% coverage.
* Tested on Linux and Windows.
* Documentation.
* Access via the "uflash" command.

0.0.1
-----

* Initial release. Basic functionality.
