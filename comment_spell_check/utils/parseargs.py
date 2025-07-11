"""command line argument parser for comment_spell_check."""

import argparse
from importlib.metadata import version, PackageNotFoundError

__version__ = "unknown"

try:
    __version__ = version("comment_spell_check")
except PackageNotFoundError:
    # package is not installed
    pass


def create_parser():
    """Create an argument parser for the command-line interface."""
    parser = argparse.ArgumentParser()

    parser.add_argument("filenames", nargs="*")

    parser.add_argument(
        "--brief",
        "-b",
        action="store_true",
        default=False,
        dest="brief",
        help="Make output brief",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        dest="verbose",
        help="Make output verbose",
    )

    parser.add_argument(
        "--first",
        "-f",
        action="store_true",
        default=False,
        dest="first",
        help="Show only first occurrence of a mispelling",
    )

    parser.add_argument(
        "--vim",
        "-V",
        action="store_true",
        default=False,
        dest="vim",
        help="Output results in vim command format",
    )

    parser.add_argument(
        "--dict",
        "-d",
        "--ignore-words",
        "-I",
        action="append",
        dest="dict",
        help="File that contains words that will be ignored."
        " Argument can be passed multiple times."
        " File must contain 1 word per line."
        " Argument can also be a URL to a text file with words.",
    )

    parser.add_argument(
        "--exclude",
        "-e",
        action="append",
        dest="exclude",
        help="Specify regex for excluding files."
        " Argument can be passed multiple times.",
    )

    parser.add_argument(
        "--skip",
        "-S",
        action="append",
        help="Comma-separated list of files to skip. It "
        "accepts globs as well. E.g.: if you want "
        "coment_spell_check.py to skip .eps and .txt files, "
        'you\'d give "*.eps,*.txt" to this option.'
        " Argument can be passed multiple times.",
    )

    parser.add_argument(
        "--prefix",
        "-p",
        action="append",
        default=[],
        dest="prefixes",
        help="Add word prefix. Argument can be passed multiple times.",
    )

    parser.add_argument(
        "--miss",
        "-m",
        action="store_true",
        default=False,
        dest="miss",
        help="Only output the misspelt words",
    )

    parser.add_argument(
        "--suffix",
        "-s",
        action="append",
        default=[".h"],
        dest="suffix",
        help="File name suffix. Argument can be passed multiple times.",
    )

    parser.add_argument(
        "--type",
        "-t",
        action="store",
        default="",
        dest="mime_type",
        help="Set file mime type. File name suffix will be ignored.",
    )

    parser.add_argument(
        "--bibtex",
        action="append",
        dest="bibtex",
        help="Bibtex file to load for additional dictionary words.",
    )

    parser.add_argument("--version", action="version", version=f"{__version__}")
    return parser


def parse_args(parser=create_parser()):
    """parse the command-line arguments."""

    args = parser.parse_args()
    return args
