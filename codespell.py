#!/usr/bin/env python3

import sys
import os
import glob
import argparse
import re
from pathlib import Path

from enchant.checker import SpellChecker
from enchant.tokenize import EmailFilter, URLFilter
from enchant import Dict

from comment_parser import comment_parser


image_h = '/Users/dchen/SimpleITK/Code/Common/include/sitkImage.h'


def splitCamelCase(word):

    result = []

    current_word = ""

    for x in word:
        if x.isupper():
            if current_word != "":
                result.append(current_word)
            current_word = ""
        current_word = current_word+x

    if len(current_word):
        result.append(current_word)

    return result


def getMimeType(filepath):

    suffix2mime = { '.h': 'text/x-c++',
                    '.cxx': 'text/x-c++',
                    '.c': 'text/x-c++',
                    '.py': 'text/x-python',
                    '.ruby': 'test/x-ruby',
                    '.java': 'text/x-java-source'
                  }
    name, ext = os.path.splitext(filepath)
    return suffix2mime[ext]


def spell_check_file(filename, spell_checker, mimetype='',
                     output_lvl=1, prefixes=[]):

    if len(mimetype) == 0:
        mimetype = getMimeType(filename)

    if output_lvl > 0:
        print("spell_check_file:", filename, ",", mimetype)

    # Returns a list of comment_parser.parsers.common.Comments
    try:
        clist = comment_parser.extract_comments(filename, mime=mimetype)
    except BaseException:
        print("Parser failed, skipping file\n")
        return []

    bad_words = []

    for c in clist:
        mistakes = []
        spell_checker.set_text(c.text())

        for error in spell_checker:
            if output_lvl > 1:
                print("Error:", error.word)

            # Check if the bad word starts with a prefix.
            # If so, spell check the word without that prefix.
            #
            for pre in prefixes:
                if error.word.startswith(pre):

                    # check if the word is only the prefix
                    if len(pre) == len(error.word):
                        continue

                    # remove the prefix
                    wrd = error.word[len(pre):]
                    if output_lvl > 1:
                        print("Trying without prefix: ", error.word, wrd)
                    try:
                        if spell_checker.check(wrd):
                            continue
                    except BaseException:
                        print("Caught an exception for word", error.word, wrd)

            # Try splitting camel case words and checking each sub-word

            if output_lvl > 1:
                print("Trying splitting camel case word")
            sub_words = splitCamelCase(error.word)
            if len(sub_words) > 1:
                ok_flag = True
                for s in sub_words:
                    if not spell_checker.check(s):
                        ok_flag = False
                if ok_flag:
                    continue

            # Check for possessive words

            if error.word.endswith("'s"):
                wrd = error.word[:-2]
                if spell_checker.check(wrd):
                    continue

            if output_lvl > 1:
                msg = 'error: ' + '\'' + error.word + '\', ' \
                      + 'suggestions: ' + str(spell_checker.suggest())
            else:
                msg = error.word
            mistakes.append(msg)

        if len(mistakes):
            if output_lvl > 0:
                print("\nLine number", c.line_number())
            if output_lvl > 0:
                print(c.text())
            for m in mistakes:
                if output_lvl >= 0:
                    print("   ", m)
                bad_words.append([m, filename, c.line_number()])

    bad_words = sorted(bad_words)

    if output_lvl > 1:
        print("\nResults")
        for x in bad_words:
            print(x)

    return bad_words


def exclude_check(name, exclude_list):
    if exclude_list is None:
        return False
    for pattern in exclude_list:
        match = re.findall("%s" % pattern, name)
        if len(match) > 0:
            return True
    return False


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('filenames', nargs='*')

    parser.add_argument('--brief', '-b', action='store_true', default=False,
                        dest='brief', help='Make output brief')

    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                        dest='verbose', help='Make output verbose')

    parser.add_argument('--dict', '-d', action='append',
                        dest='dict',
                        help='Add a dictionary (multiples allowed)')

    parser.add_argument('--exclude', '-e', action='append',
                        dest='exclude',
                        help='Add exclude regex (multiples allowed)')

    parser.add_argument('--prefix', '-p', action='append', default=[],
                        dest='prefixes',
                        help='Add word prefix (multiples allowed)')

    parser.add_argument('--miss', '-m', action='store_true', default=False,
                        dest='miss', help='Only output the misspelt words')

    parser.add_argument('--suffix', '-s', action='append', default=[".h"],
                        dest='suffix', help='File name suffix')

    args = parser.parse_args()
    return args


def add_dict(enchant_dict, filename):
    with open(filename) as f:
        lines = f.read().splitlines()

    # You better not have more than 1 word in a line
    for wrd in lines:
        if not enchant_dict.check(wrd):
            enchant_dict.add_to_pwl(wrd)


def main():
    args = parse_args()

    sitk_dict = Dict('en_US')

    initial_dct = Path(__file__).parent / 'additional_dictionary.txt'
    if not initial_dct.exists():
        initial_dct = None
    else:
        add_dict(sitk_dict, str(initial_dct))

    if args.dict is not None:
        for d in args.dict:
            add_dict(sitk_dict, d)

    spell_checker = SpellChecker(sitk_dict,
                                 filters=[EmailFilter, URLFilter])

    output_lvl = 1
    if args.brief:
        output_lvl = 0
    else:
        if args.verbose:
            output_lvl = 2
    if args.miss:
        output_lvl = -1

    file_list = []
    if len(args.filenames):
        file_list = args.filenames
    else:
        file_list.append(image_h)

    prefixes = ['sitk', 'itk', 'vtk'] + args.prefixes

    bad_words = []

    if output_lvl>1:
        print("Prefixes:", prefixes)
        print("Suffixes:", args.suffix)

    for f in file_list:

        if not args.miss:
            print("\nChecking", f)

        if os.path.isdir(f):

            # f is a directory, so search for files inside
            dir_entries = []
            for s in args.suffix:
                dir_entries = dir_entries + glob.glob(f + '/**/*' + s, recursive=True)

            if output_lvl:
                print(dir_entries)

            # spell check the files found in f
            for x in dir_entries:

                if exclude_check(x, args.exclude):
                    print("\nExcluding", x)
                    continue

                if not args.miss:
                    print("\nChecking", x)
                result = spell_check_file(x, spell_checker,
                                          output_lvl=output_lvl,
                                          prefixes=prefixes)
                bad_words = sorted(bad_words + result)
        else:

            if exclude_check(f, args.exclude):
                print("\nExcluding", x)
                continue

            # f is a file, so spell check it
            result = spell_check_file(f, spell_checker,
                                      output_lvl=output_lvl, prefixes=prefixes)

            bad_words = sorted(bad_words + result)

    if not args.miss:
        print("\nBad words\n")

    prev = ""
    for x in bad_words:
        if x[0] == prev:
            sys.stdout.write('.')
            continue
        print("\n", x[0], ": ", x[1], ", ", x[2], sep='')
        prev = x[0]

    if not args.miss:
        print("")

    print(len(bad_words), "misspellings found")

    sys.exit(len(bad_words))


if __name__ == '__main__':
    main()
