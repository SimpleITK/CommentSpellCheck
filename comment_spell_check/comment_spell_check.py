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
import unicodedata
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

from comment_parser import comment_parser

from spellchecker import SpellChecker

try:
    # This loads the modules from the installed package
    from comment_spell_check.utils import bibtex_loader
    from comment_spell_check.utils import create_checker
    from comment_spell_check.utils import url_remove
except ImportError:
    # This loads the modules from the source directory
    from utils import bibtex_loader
    from utils import create_checker
    from utils import url_remove

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


def remove_accents(input_str):
    """Removes accents from a string using Unicode normalization."""
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def filter_string(input_str: str):
    """Filter out unwanted characters from the input string.
    That includes removing single quote that are not part of a
    contraction."""

    # map accented characters to their unaccented equivalent
    line = remove_accents(input_str)

    # Keep letters and single quotes
    line = re.sub(r"[^a-zA-Z']", " ", line)

    # Split the line into words
    words = line.split()

    contraction_apostrophe = re.compile(r"\b\w+'\w+\b")

    w2 = []

    # Check each word for contractions and apostrophes
    for w in words:
        if "'" in w:
            matches = contraction_apostrophe.findall(w)
            if len(matches) > 0:
                # if there is a contraction, allow it
                w2.append(w)
            else:
                # apostrophe is not in a contraction so remove it
                new_word = re.sub("'", "", w)
                if len(new_word) > 0:
                    w2.append(new_word)
        else:
            w2.append(w)

    return w2


def spell_check_words(spell_checker: SpellChecker, words: list[str]):
    """Check each word and report False if at least one has an spelling
    error."""
    for word in words:
        if not (word in spell_checker or word.lower() in spell_checker):
            return False
    return True


def find_misspellings(
    spell: SpellChecker, line: str, verbose: bool = False
) -> list[str]:
    """Find misspellings in a line of text."""

    words = filter_string(line)

    mistakes = []

    for word in words:
        if not (word.lower() in spell or word in spell):
            print(f"Misspelled word: {word}\n" if verbose else "", end="")
            mistakes.append(word)
    return mistakes


def remove_contractions(word: str, verbose: bool = False):
    """Remove contractions from the word."""
    for contraction in CONTRACTIONS:
        if word.endswith(contraction):
            print(
                (
                    f"    Contraction: {word} -> {word[: -len(contraction)]}\n"
                    if verbose
                    else ""
                ),
                end="",
            )
            return word[: -len(contraction)]
    return word


def remove_prefix(word: str, prefixes: list[str]):
    """Remove the prefix from the word."""
    for prefix in prefixes:
        if word.startswith(prefix):
            return word[len(prefix) :]
    return word


def spell_check_comment(
    spell: SpellChecker,
    c: comment_parser.common.Comment,
    prefixes: list[str] = None,
    output_lvl=2,
) -> list[str]:
    """Check comment and return list of identified issues if any."""

    print(f"Line {c.line_number()}: {c}\n" if output_lvl > 1 else "", end="")

    line = c.text()
    if "https://" in line or "http://" in line:
        line = url_remove.remove_urls(line)
        print(f"    Removed URLs: {line}\n" if output_lvl > 1 else "", end="")

    bad_words = find_misspellings(spell, line, verbose=output_lvl > 1)

    mistakes = []
    for error_word in bad_words:
        print(f"    Error: {error_word}\n" if output_lvl > 1 else "", end="")

        error_word = remove_contractions(error_word, output_lvl > 1)

        prefixes = prefixes or []
        error_word = remove_prefix(error_word, prefixes)

        if len(error_word) == 0 or error_word in spell or error_word.lower() in spell:
            continue

        # Try splitting camel case words and checking each sub-word
        sub_words = split_camel_case(error_word)
        print(
            (
                f"    Trying splitting camel case word: {error_word}\n"
                + f"    Sub-words: {sub_words}\n"
                if output_lvl > 1
                else ""
            ),
            end="",
        )

        if len(sub_words) > 1 and spell_check_words(spell, sub_words):
            continue

        msg = f"'{error_word}', " + f"suggestions: {spell.candidates(error_word)}"
        mistakes.append(msg)

    return mistakes


def spell_check_file(
    filename, spell_checker, mime_type="", output_lvl=1, prefixes=None
):
    """Check spelling in ``filename``."""

    if len(mime_type) == 0:
        mime_type = get_mime_type(filename)

    print(
        f"spell_check_file: {filename}, {mime_type}\n" if output_lvl > 0 else "", end=""
    )

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
    line_count = 0

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
                print(f"    {m}" if output_lvl >= 0 else "")
                bad_words.append([m, filename, c.line_number()])
        line_count = line_count + 1

    bad_words = sorted(bad_words)

    if output_lvl > 1:
        print("\nResults")
        for x in bad_words:
            print(x)

    return bad_words, line_count


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
    print(f"Additional dictionary: {filename}" if verbose else "", end="")

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
        print(f"Loading bibtex file: {bibtex_file}\n" if verbose else "", end="")
        bibtex_loader.add_bibtex(spell, bibtex_file, verbose=verbose)


def get_output_lvl(args):
    """Set the amount of debugging messages to print."""
    output_lvl = 1
    if args.brief:
        output_lvl = 0
    else:
        if args.verbose:
            output_lvl = 2
    if args.miss:
        output_lvl = -1
    return output_lvl


def output_results(args, bad_words):
    """Output the results of the spell check."""

    print("\nBad words\n" if not args.miss else "", end="")

    previous_word = ""

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

    print(f"\n{len(bad_words)} misspellings found")


def main():
    """comment_spell_check main function."""
    args = parse_args()

    output_lvl = get_output_lvl(args)

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

    print(
        (
            f"Prefixes: {prefixes}\nSuffixes: {suffixes}\n"
            if any([args.brief, output_lvl >= 0])
            else ""
        ),
        end="",
    )

    file_count = 0
    line_count = 0

    #
    # Spell check the files
    #
    for f in file_list:
        print(f"\nChecking {f}\n" if not args.miss else "", end="")

        # If f is a directory, recursively check for files in it.
        if os.path.isdir(f):
            # f is a directory, so search for files inside
            dir_entries = []
            for s in suffixes:
                dir_entries = dir_entries + glob.glob(f + "/**/*" + s, recursive=True)

            print(dir_entries if output_lvl > 0 else "", end="")

            # spell check the files found in f
            for x in dir_entries:
                if exclude_check(x, args.exclude) or skip_check(x, args.skip):
                    print(f"\nExcluding {x}\n" if not args.miss else "", end="")
                    continue

                print(f"\nChecking {x}\n" if not args.miss else "", end="")
                result, lc = spell_check_file(
                    x,
                    spell,
                    args.mime_type,
                    output_lvl=output_lvl,
                    prefixes=prefixes,
                )
                bad_words = sorted(bad_words + result)
                file_count = file_count + 1
                line_count = line_count + lc

        else:
            # f is a file
            if exclude_check(f, args.exclude) or skip_check(f, args.skip):
                print(f"\nExcluding {x}\n" if not args.miss else "", end="")
                continue

            # f is a file, so spell check it
            result, lc = spell_check_file(
                f,
                spell,
                args.mime_type,
                output_lvl=output_lvl,
                prefixes=prefixes,
            )
            bad_words = sorted(bad_words + result)
            file_count = file_count + 1
            line_count = line_count + lc

    output_results(args, bad_words)

    print(
        (
            f"{file_count} files checked, {line_count} lines checked\n"
            if not args.miss
            else ""
        ),
        end="",
    )

    sys.exit(len(bad_words))


if __name__ == "__main__":
    main()
