import uflash
import argparse
import sys
import os

_HELP_TEXT = """
A simple utility script intended for creating hexified versions of MicroPython
scripts on the local filesystem _NOT_ the microbit.  Does not autodetect a
microbit.  Accepts multiple input scripts and optionally one output directory.
"""


def main(argv=None):
    if not argv:    # pragma: no cover
            argv = sys.argv[1:]

    parser = argparse.ArgumentParser(description=_HELP_TEXT)
    parser.add_argument('source', nargs='*', default=None)
    parser.add_argument('-r', '--runtime', default=None,
                        help="Use the referenced MicroPython runtime.")
    parser.add_argument('-o', '--outdir', default=None,
                        help="Output directory")
    parser.add_argument('-m', '--minify',
                        action='store_true',
                        help='Minify the source')
    parser.add_argument('--version', action='version',
                        version=uflash.get_version())
    args = parser.parse_args(argv)

    for py_file in args.source:
        if not args.outdir:
            (script_path, script_name) = os.path.split(py_file)
            args.outdir = script_path
        uflash.flash(path_to_python=py_file,
                     path_to_runtime=args.runtime,
                     paths_to_microbits=[args.outdir],
                     minify=args.minify,
                     keepname=True) # keepname is always True in hexify


if __name__ == '__main__':  # pragma: no cover
    main(sys.argv[1:])
