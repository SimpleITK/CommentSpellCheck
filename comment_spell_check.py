#!/usr/bin/env python3

import sys
import os
import fnmatch
import glob
import argparse
import re
from pathlib import Path

from enchant.checker import SpellChecker
from enchant.tokenize import EmailFilter, URLFilter
from enchant import Dict

from comment_parser import comment_parser

from importlib.metadata import version, PackageNotFoundError

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


def splitCamelCase(word):
    """Split a camel case string into individual words."""

    result = []

    current_word = ""

    for x in word:
        if x.isupper():
            if current_word != "":
                result.append(current_word)
            current_word = ""
        current_word = current_word + x

    if len(current_word):
        result.append(current_word)

    return result


def getMimeType(filepath):
    """Map ``filepath`` extension to file type."""
    name, ext = os.path.splitext(filepath)
    return SUFFIX2MIME.get(ext, "text/plain")


def load_text_file(filename):
    """Parse plain text file as list of ``comment_parser.common.Comment``.

    For a regular text file, we don't need to parse it for comments. We
    just pass every line to the spellchecker.
    """

    output = []
    lc = 0
    with open(filename) as fp:
        for line in fp:
            line = line.strip()
            lc = lc + 1
            comment = comment_parser.common.Comment(line, lc)
            output.append(comment)
    return output


def spell_check_words(spell_checker: SpellChecker, words: list[str]):
    """Check each word and report False if at least one has an spelling error."""
    for word in words:
        if not spell_checker.check(word):
            return False
    return True


def spell_check_comment(
    spell_checker: SpellChecker,
    c: comment_parser.common.Comment,
    prefixes: list[str] = [],
    output_lvl=2,
) -> list[str]:
    """Check comment and return list of identified issues if any."""

    if output_lvl > 1:
        print(f"Line {c.line_number()}: {c}")

    mistakes = []
    spell_checker.set_text(c.text())

    for error in spell_checker:
        error_word = error.word

        if output_lvl > 1:
            print(f"Error: {error_word}")

        valid = False

        # Check for contractions
        for contraction in CONTRACTIONS:
            if error_word.endswith(contraction):
                original_error_word = error_word
                error_word = error_word[: -len(contraction)]
                if output_lvl > 1:
                    print(
                        f"Stripping contraction: {original_error_word} -> {error_word}"
                    )
                if spell_checker.check(error_word):
                    valid = True
                break

        if valid:
            continue

        # Check if the bad word starts with a prefix.
        # If so, spell check the word without that prefix.
        for pre in prefixes:
            if error_word.startswith(pre):
                # check if the word is only the prefix
                if len(pre) == len(error_word):
                    if output_lvl > 1:
                        print(f"Prefix '{pre}' matches word")
                    valid = True
                    break

                # remove the prefix
                wrd = error_word[len(pre) :]
                if output_lvl > 1:
                    print(f"Trying without '{pre}' prefix: {error_word} -> {wrd}")
                try:
                    if spell_checker.check(wrd):
                        valid = True
                        break
                    else:
                        # Try splitting camel case words and checking each sub-words
                        if output_lvl > 1:
                            print("Trying splitting camel case word: {wrd}")
                        sub_words = splitCamelCase(wrd)
                        if len(sub_words) > 1 and spell_check_words(
                            spell_checker, sub_words
                        ):
                            valid = True
                            break
                except BaseException:
                    print(f"Caught an exception for word {error_word} {wrd}")

        if valid:
            continue

        # Try splitting camel case words and checking each sub-word
        if output_lvl > 1:
            print(f"Trying splitting camel case word: {error_word}")
        sub_words = splitCamelCase(error_word)
        if len(sub_words) > 1 and spell_check_words(spell_checker, sub_words):
            continue

        if output_lvl > 1:
            msg = f"error: '{error_word}', suggestions: {spell_checker.suggest()}"
        else:
            msg = error_word
        mistakes.append(msg)

    return mistakes


def spell_check_file(filename, spell_checker, mime_type="", output_lvl=1, prefixes=[]):
    """Check spelling in ``filename``."""

    if len(mime_type) == 0:
        mime_type = getMimeType(filename)

    if output_lvl > 0:
        print(f"spell_check_file: {filename}, {mime_type}")

    # Returns a list of comment_parser.parsers.common.Comments
    if mime_type == "text/plain":
        clist = load_text_file(filename)
    else:
        try:
            clist = comment_parser.extract_comments(filename, mime=mime_type)
        except BaseException:
            print(f"Parser failed, skipping file {filename}")
            return []

    bad_words = []

    for c in clist:
        mistakes = spell_check_comment(
            spell_checker, c, prefixes=prefixes, output_lvl=output_lvl
        )
        if len(mistakes):
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
        match = re.findall("%s" % pattern, name)
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

    parser.add_argument("--version", action="version", version=f"{__version__}")

    args = parser.parse_args()
    return args


def add_dict(enchant_dict, filename, verbose=False):
    """Update ``enchant_dict`` spell checking dictionary with the words listed
    in ``filename`` (one word per line)."""
    if verbose:
        print(f"Additional dictionary: {filename}")

    with open(filename) as f:
        lines = f.read().splitlines()

    # You better not have more than 1 word in a line
    for wrd in lines:
        if not enchant_dict.check(wrd):
            enchant_dict.add(wrd)


def main():
    args = parse_args()

    sitk_dict = Dict("en_US")

    # Set the amount of debugging messages to print.
    output_lvl = 1
    if args.brief:
        output_lvl = 0
    else:
        if args.verbose:
            output_lvl = 2
    if args.miss:
        output_lvl = -1

    # Load the dictionary files
    #
    initial_dct = Path(__file__).parent / "additional_dictionary.txt"
    if not initial_dct.exists():
        initial_dct = None
    else:
        add_dict(sitk_dict, str(initial_dct), any([args.brief, output_lvl >= 0]))

    if args.dict is not None:
        for d in args.dict:
            add_dict(sitk_dict, d, any([args.brief, output_lvl >= 0]))

    spell_checker = SpellChecker(sitk_dict, filters=[EmailFilter, URLFilter])

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
                    spell_checker,
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
                spell_checker,
                args.mime_type,
                output_lvl=output_lvl,
                prefixes=prefixes,
            )

            bad_words = sorted(bad_words + result)

    # Done spell checking.  Print out all the words not found in our dictionary.
    #
    if not args.miss:
        print("\nBad words\n")

    previous_word = ""

    for misspelled_word, found_file, line_num in bad_words:
        if misspelled_word != previous_word:
            print(f"\n{misspelled_word}:")

        if (misspelled_word == previous_word) and args.first:
            sys.stderr.write(".")
            continue

        if args.vim:
            print(f"    vim +{line_num} {found_file}", file=sys.stderr)
        else:
            print(f"    {found_file}, {line_num}", file=sys.stderr)

        previous_word = misspelled_word

    print("")
    print(f"{len(bad_words)} misspellings found")

    sys.exit(len(bad_words))


if __name__ == "__main__":
    main()
