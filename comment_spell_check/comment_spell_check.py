#!/usr/bin/env python3

# ==========================================================================
#
#   Copyright NumFOCUS
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0.txt
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ==========================================================================*/

"""spell check the comments in code."""

import sys
import os
import fnmatch
import glob
import argparse
import re
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

from comment_parser import comment_parser

from spellchecker import SpellChecker

try:
    # This loads the modules from the installed package
    from comment_spell_check.lib import bibtex_loader
    from comment_spell_check.lib import create_checker
except ImportError:
    # This loads the modules from the source directory
    from lib import bibtex_loader
    from lib import create_checker

__version__ = "unknown"

try:
    __version__ = version("comment_spell_check")
except PackageNotFoundError:
    # package is not installed
    pass


SUFFIX2MIME = {
    ".h": "text/x-c++",
    ".cxx": "text/x-c++",
    ".c": "text/x-c++",
    ".hxx": "text/x-c++",
    ".py": "text/x-python",
    ".ruby": "text/x-ruby",
    ".java": "text/x-java-source",
    ".txt": "text/plain",
    ".rst": "text/plain",
    ".md": "text/plain",
}


CONTRACTIONS = ["'d", "'s", "'th"]


def split_camel_case(word):
    """Split a camel case string into individual words."""

    result = []

    current_word = ""

    for x in word:
        if x.isupper():
            if current_word != "":
                result.append(current_word)
            current_word = ""
        current_word = current_word + x

    if len(current_word) > 0:
        result.append(current_word)

    return result


def get_mime_type(filepath):
    """Map ``filepath`` extension to file type."""
    parts = os.path.splitext(filepath)
    return SUFFIX2MIME.get(parts[1], "text/plain")


def load_text_file(filename):
    """Parse plain text file as list of ``comment_parser.common.Comment``.

    For a regular text file, we don't need to parse it for comments. We
    just pass every line to the spellchecker.
    """

    output = []
    lc = 0
    with open(filename, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            lc = lc + 1
            comment = comment_parser.common.Comment(line, lc)
            output.append(comment)
    return output


def spell_check_words(spell_checker: SpellChecker, words: list[str]):
    """Check each word and report False if at least one has an spelling error."""
    for word in words:
        if not (word in spell_checker or word.lower() in spell_checker):
            return False
    return True


def find_misspellings(
    spell: SpellChecker, line: str, verbose: bool = False
) -> list[str]:
    """Find misspellings in a line of text."""

    l2 = re.sub(r"[^a-zA-Z]", " ", line)
    words = l2.split()

    mistakes = []

    for word in words:
        if not (word.lower() in spell or word in spell):
            if verbose:
                print(f"Misspelled word: {word}")
            mistakes.append(word)
    return mistakes


def spell_check_comment(
    spell: SpellChecker,
    c: comment_parser.common.Comment,
    prefixes: list[str] = None,
    output_lvl=2,
) -> list[str]:
    """Check comment and return list of identified issues if any."""

    if output_lvl > 1:
        print(f"Line {c.line_number()}: {c}")

    bad_words = find_misspellings(spell, c.text(), verbose=output_lvl > 1)

    mistakes = []
    for error_word in bad_words:
        if output_lvl > 1:
            print(f"    Error: {error_word}")

        valid = False

        # Check for contractions
        for contraction in CONTRACTIONS:
            if error_word.endswith(contraction):
                original_error_word = error_word
                error_word = error_word[: -len(contraction)]
                if output_lvl > 1:
                    print(
                        "    Stripping contraction: "
                        + f"{original_error_word} -> {error_word}"
                    )
                valid = error_word in spell
                break

        if valid:
            continue

        if prefixes is None:
            prefixes = []

        # Check if the bad word starts with a prefix.
        # If so, spell check the word without that prefix.

        for pre in prefixes:
            if error_word.startswith(pre):
                # check if the word is only the prefix
                if len(pre) == len(error_word):
                    if output_lvl > 1:
                        print(f"    Prefix '{pre}' matches word")
                    valid = True
                    break

                # remove the prefix
                wrd = error_word[len(pre) :]
                if output_lvl > 1:
                    print(f"    Trying without '{pre}' prefix: {error_word} -> {wrd}")
                try:
                    valid = wrd in spell
                    if not valid:
                        # Try splitting camel case words and checking each sub-words
                        if output_lvl > 1:
                            print("Trying splitting camel case word: {wrd}")
                        sub_words = split_camel_case(wrd)
                        if len(sub_words) > 1 and spell_check_words(spell, sub_words):
                            valid = True
                            break
                except TypeError:
                    print(f"    Caught an exception for word {error_word} {wrd}")

        if valid:
            continue

        # Try splitting camel case words and checking each sub-word
        if output_lvl > 1:
            print(f"    Trying splitting camel case word: {error_word}")
        sub_words = split_camel_case(error_word)
        if len(sub_words) > 1 and spell_check_words(spell, sub_words):
            continue

        if output_lvl > 1:
            msg = (
                f"    error: '{error_word}', "
                + f"suggestions: {spell.candidates(error_word)}"
            )
        else:
            msg = error_word
        mistakes.append(msg)

    return mistakes


def spell_check_file(
    filename, spell_checker, mime_type="", output_lvl=1, prefixes=None
):
    """Check spelling in ``filename``."""

    if len(mime_type) == 0:
        mime_type = get_mime_type(filename)

    if output_lvl > 0:
        print(f"spell_check_file: {filename}, {mime_type}")

    # Returns a list of comment_parser.parsers.common.Comments
    if mime_type == "text/plain":
        clist = load_text_file(filename)
    else:
        try:
            clist = comment_parser.extract_comments(filename, mime=mime_type)
        except TypeError:
            print(f"Parser failed, skipping file {filename}")
            return []

    bad_words = []

    for c in clist:
        mistakes = spell_check_comment(
            spell_checker, c, prefixes=prefixes, output_lvl=output_lvl
        )
        if len(mistakes) > 0:
            if output_lvl > 0:
                print(f"\nLine number {c.line_number()}")
            if output_lvl > 0:
                print(c.text())
            for m in mistakes:
                if output_lvl >= 0:
                    print(f"    {m}")
                bad_words.append([m, filename, c.line_number()])

    bad_words = sorted(bad_words)

    if output_lvl > 1:
        print("\nResults")
        for x in bad_words:
            print(x)

    return bad_words


def exclude_check(name, exclude_list):
    """Return True if ``name`` matches any of the regular expressions listed in
    ``exclude_list``."""
    if exclude_list is None:
        return False
    for pattern in exclude_list:
        match = re.findall(pattern, name)
        if len(match) > 0:
            return True
    return False


def skip_check(name, skip_list):
    """Return True if ``name`` matches any of the glob pattern listed in
    ``skip_list``."""
    if skip_list is None:
        return False
    for skip in ",".join(skip_list).split(","):
        if fnmatch.fnmatch(name, skip):
            return True
    return False


def parse_args():
    """parse the command-line arguments."""
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
        " File must contain 1 word per line.",
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

    args = parser.parse_args()
    return args


def add_dict(enchant_dict, filename, verbose=False):
    """Update ``enchant_dict`` spell checking dictionary with the words listed
    in ``filename`` (one word per line)."""
    if verbose:
        print(f"Additional dictionary: {filename}")

    with open(filename, encoding="utf-8") as f:
        lines = f.read().splitlines()

    # You better not have more than 1 word in a line
    for wrd in lines:
        if not wrd.replace("'", "").isidentifier():
            print(
                "Warning: adding word with non-alphanumeric characters to dictionary:",
                wrd,
            )
        if not enchant_dict.check(wrd):
            enchant_dict.add(wrd)


def build_dictionary_list(args):
    """build a list of dictionaries to use for spell checking."""
    dict_list = []
    initial_dct = Path(__file__).parent / "additional_dictionary.txt"

    if initial_dct.exists():
        dict_list.append(initial_dct)
    else:
        print("Warning: initial dictionary not found.", initial_dct)

    if not isinstance(args.dict, list):
        return dict_list

    for d in args.dict:
        dpath = Path(d)
        if dpath.exists():
            dict_list.append(dpath)

    return dict_list


def add_bibtex_words(spell, bibtex_files, verbose=False):
    """Add words from bibtex files to the spell checker."""
    for bibtex_file in bibtex_files:
        if verbose:
            print(f"Loading bibtex file: {bibtex_file}")
        bibtex_loader.add_bibtex(spell, bibtex_file, verbose=verbose)


def main():
    """comment_spell_check main function."""
    args = parse_args()

    # Set the amount of debugging messages to print.
    output_lvl = 1
    if args.brief:
        output_lvl = 0
    else:
        if args.verbose:
            output_lvl = 2
    if args.miss:
        output_lvl = -1

    dict_list = build_dictionary_list(args)

    spell = create_checker.create_checker(dict_list, output_lvl > 1)

    if args.bibtex:
        add_bibtex_words(spell, args.bibtex, verbose=output_lvl > 1)

    file_list = []
    if len(args.filenames):
        file_list = args.filenames
    else:
        file_list = ["."]

    prefixes = ["sitk", "itk", "vtk"] + args.prefixes

    bad_words = []

    suffixes = [*set(args.suffix)]  # remove duplicates

    if any([args.brief, output_lvl >= 0]):
        print(f"Prefixes: {prefixes}")
        print(f"Suffixes: {suffixes}")

    #
    # Spell check the files
    #
    for f in file_list:
        if not args.miss:
            print(f"\nChecking {f}")

        # If f is a directory, recursively check for files in it.
        if os.path.isdir(f):
            # f is a directory, so search for files inside
            dir_entries = []
            for s in suffixes:
                dir_entries = dir_entries + glob.glob(f + "/**/*" + s, recursive=True)

            if output_lvl > 0:
                print(dir_entries)

            # spell check the files found in f
            for x in dir_entries:
                if exclude_check(x, args.exclude) or skip_check(x, args.skip):
                    if not args.miss:
                        print(f"\nExcluding {x}")
                    continue

                if not args.miss:
                    print(f"\nChecking {x}")
                result = spell_check_file(
                    x,
                    spell,
                    args.mime_type,
                    output_lvl=output_lvl,
                    prefixes=prefixes,
                )
                bad_words = sorted(bad_words + result)

        else:
            # f is a file
            if exclude_check(f, args.exclude) or skip_check(f, args.skip):
                if not args.miss:
                    print(f"\nExcluding {x}")
                continue

            # f is a file, so spell check it
            result = spell_check_file(
                f,
                spell,
                args.mime_type,
                output_lvl=output_lvl,
                prefixes=prefixes,
            )

            bad_words = sorted(bad_words + result)

    # Done spell checking.  Print out all the words not found in our dictionary.
    #
    if not args.miss:
        print("\nBad words")

    previous_word = ""
    print("")

    for misspelled_word, found_file, line_num in bad_words:
        if misspelled_word != previous_word and args.first:
            print(f"\n{misspelled_word}:")

        if (misspelled_word == previous_word) and args.first:
            sys.stderr.write(".")
            continue

        if args.vim:
            print(f"vim +{line_num} {found_file}", file=sys.stderr)
        else:
            print(
                f"file: {found_file:30}  line: {line_num:3d}  word: {misspelled_word}",
                file=sys.stderr,
            )

        previous_word = misspelled_word

    print("")
    print(f"{len(bad_words)} misspellings found")

    sys.exit(len(bad_words))


if __name__ == "__main__":
    main()
