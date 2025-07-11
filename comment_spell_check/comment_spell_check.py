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
import re
import unicodedata
import logging
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError

from comment_parser import comment_parser

from spellchecker import SpellChecker

from comment_spell_check.utils import parseargs
from comment_spell_check.utils import bibtex_loader
from comment_spell_check.utils import create_checker
from comment_spell_check.utils import url_remove

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
    ".cs": "text/x-c++",
    ".py": "text/x-python",
    ".R": "text/x-python",
    ".rb": "text/x-ruby",
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


def find_misspellings(spell: SpellChecker, line: str) -> list[str]:
    """Find misspellings in a line of text."""

    logger = logging.getLogger("comment_spell_check")
    words = filter_string(line)

    mistakes = []

    for word in words:
        if not (word.lower() in spell or word in spell):
            logger.info("Misspelled word: %s", word)
            mistakes.append(word)
    return mistakes


def remove_contractions(word: str):
    """Remove contractions from the word."""

    logger = logging.getLogger("comment_spell_check")
    for contraction in CONTRACTIONS:
        if word.endswith(contraction):
            logger.info("Contraction: %s -> %s", word, word[: -len(contraction)])
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
) -> list[str]:
    """Check comment and return list of identified issues if any."""

    logger = logging.getLogger("comment_spell_check")
    logger.info("Line #%d: %s", c.line_number(), c.text())

    line = c.text()
    if "https://" in line or "http://" in line:
        line = url_remove.remove_urls(line)
        logger.debug("    Removed URLs: %s", line)

    bad_words = find_misspellings(spell, line)

    mistakes = []
    for error_word in bad_words:
        logger.debug("    Error: %s", error_word)

        error_word = remove_contractions(error_word)

        prefixes = prefixes or []
        error_word = remove_prefix(error_word, prefixes)

        if not error_word:
            continue
        if error_word in spell or error_word.lower() in spell:
            continue

        # Try splitting camel case words and checking each sub-word
        sub_words = split_camel_case(error_word)
        logger.debug("    Trying splitting camel case word: %s", error_word)
        logger.debug("    Sub-words: %s", sub_words)

        if len(sub_words) > 1 and spell_check_words(spell, sub_words):
            continue

        msg = f"'{error_word}', " + f"suggestions: {spell.candidates(error_word)}"
        mistakes.append(msg)

    return mistakes


def spell_check_file(
    filename: str,
    spell_checker: SpellChecker,
    mime_type: str = "",
    prefixes=None,
):
    """Check spelling in ``filename``."""

    if len(mime_type) == 0:
        mime_type = get_mime_type(filename)

    logger = logging.getLogger("comment_spell_check")
    logger.info("spell_check_file: %s, %s", filename, mime_type)

    # Returns a list of comment_parser.parsers.common.Comments
    if mime_type == "text/plain":
        clist = load_text_file(filename)
    else:
        try:
            clist = comment_parser.extract_comments(filename, mime=mime_type)
        except TypeError:
            logger.error("Parser failed, skipping file %s", filename)
            return []

    bad_words = []
    line_count = 0

    for c in clist:
        mistakes = spell_check_comment(spell_checker, c, prefixes=prefixes)
        if len(mistakes) > 0:
            logger.info("\nLine number %s", c.line_number())
            logger.info(c.text())
            for m in mistakes:
                logger.info("    %s", m)
                bad_words.append([m, filename, c.line_number()])
        line_count = line_count + 1

    bad_words = sorted(bad_words)

    logger.info("Results")
    for x in bad_words:
        logger.info(x)

    return bad_words, line_count


def exclude_check(name: str, exclude_list: list[str] = None):
    """Return True if ``name`` matches any of the regular expressions listed in
    ``exclude_list``."""
    if exclude_list is None:
        return False
    for pattern in exclude_list:
        match = re.findall(pattern, name)
        if len(match) > 0:
            return True
    return False


def skip_check(name: str, skip_list: list[str] = None):
    """Return True if ``name`` matches any of the glob pattern listed in
    ``skip_list``."""
    if skip_list is None:
        return False
    for skip in ",".join(skip_list).split(","):
        if fnmatch.fnmatch(name, skip):
            return True
    return False


def build_dictionary_list(args):
    """build a list of dictionaries to use for spell checking."""
    dict_list = []
    initial_dct = Path(__file__).parent / "additional_dictionary.txt"

    logger = logging.getLogger("comment_spell_check")
    if initial_dct.exists():
        dict_list.append(initial_dct)
    else:
        logger.warning("Initial dictionary not found: %s", initial_dct)

    if not isinstance(args.dict, list):
        return dict_list

    dict_list.extend(args.dict)

    return dict_list


def add_bibtex_words(spell: SpellChecker, bibtex_files: list[str]):
    """Add words from bibtex files to the spell checker."""

    if list is None:
        return

    logger = logging.getLogger("comment_spell_check")

    for bibtex_file in bibtex_files:
        logger.info("Loading bibtex file: %s", bibtex_file)
        bibtex_loader.add_bibtex(spell, bibtex_file)


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
                f"file: {found_file:30}  line: {line_num:3d}  ",
                f"word: {misspelled_word}",
                file=sys.stderr,
            )

        previous_word = misspelled_word

    print(f"\n{len(bad_words)} misspellings found")


def setup_logger(args):
    """Sets up a logger that outputs to the console."""

    level = logging.INFO
    if args.verbose:
        level = logging.DEBUG
        print("Verbose mode enabled")
    if args.miss:
        level = logging.ERROR
    if args.brief:
        level = logging.WARNING

    logger = logging.getLogger("comment_spell_check")
    logger.setLevel(level)

    if level in (logging.INFO, logging.DEBUG):
        # info and debug messages will be printed to the console

        # Create a console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # Create a formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Add formatter to ch
        ch.setFormatter(formatter)

        # Add ch to logger
        logger.addHandler(ch)

    return logger


def comment_spell_check(args):
    """comment_spell_check main function."""
    logger = setup_logger(args)

    dict_list = build_dictionary_list(args)

    spell = create_checker.create_checker(dict_list)

    if args.bibtex:
        add_bibtex_words(spell, args.bibtex)

    file_list = []
    if len(args.filenames):
        file_list = args.filenames
    else:
        file_list = ["."]

    prefixes = ["sitk", "itk", "vtk"] + args.prefixes

    bad_words = []

    suffixes = [*set(args.suffix)]  # remove duplicates

    logger.info("Prefixes: %s\nSuffixes: %s", prefixes, suffixes)

    counts = [0, 0]

    #
    # Spell check the files
    #
    for f in file_list:

        # If f is a directory, recursively check for files in it.
        if os.path.isdir(f):
            # f is a directory, so search for files inside
            dir_entries = []
            for s in suffixes:
                dir_entries = dir_entries + glob.glob(f + "/**/*" + s, recursive=True)

            logger.info(dir_entries)

            # spell check the files found in f
            for x in dir_entries:
                if exclude_check(x, args.exclude) or skip_check(x, args.skip):
                    logger.info("Excluding %s", x)
                    continue

                logger.info("Checking %s", x)
                result, lc = spell_check_file(
                    x,
                    spell,
                    args.mime_type,
                    prefixes=prefixes,
                )
                bad_words = sorted(bad_words + result)
                counts[0] = counts[0] + 1
                counts[1] = counts[1] + lc

        else:
            # f is a file
            if exclude_check(f, args.exclude) or skip_check(f, args.skip):
                logger.info("Excluding %s", f)
                continue

            # f is a file, so spell check it
            result, lc = spell_check_file(
                f,
                spell,
                args.mime_type,
                prefixes=prefixes,
            )
            bad_words = sorted(bad_words + result)
            counts[0] = counts[0] + 1
            counts[1] = counts[1] + lc

    output_results(args, bad_words)

    logger.info("%s files checked, %s lines checked", counts[0], counts[1])

    sys.exit(len(bad_words))


def main():
    """Parse the command line arguments and call the spell checking function."""
    args = parseargs.parse_args()
    comment_spell_check(args)


if __name__ == "__main__":
    main()
