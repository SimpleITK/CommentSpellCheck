#! /usr/bin/env

import os
import glob
import sys
import argparse

from enchant.checker import SpellChecker
from enchant.tokenize import Filter, EmailFilter, URLFilter
from enchant import DictWithPWL

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


def spell_check_file(filename, spell_checker, mimetype='text/x-c++', output_lvl=1, prefixes=[]):

    if output_lvl>0:
        print("spell_check_file:", filename, ",", mimetype)

    # Returns a list of comment_parser.parsers.common.Comments
    try:
        clist = comment_parser.extract_comments(filename, mime=mimetype)
    except:
        print("Parser failed, skipping file\n")
        return []

    bad_words = set()

    for c in clist:
        mistakes=[]
        spell_checker.set_text(c.text())

        for error in spell_checker:

            # Check if the bad word starts with a prefix.
            # If so, spell check the word without that prefix.
            #
            for pre in prefixes:
                if error.word.startswith(pre):
                    l = len(pre)
                    wrd = error.word[l:]
                    if output_lvl>1:
                        print("Trying without prefix: ", wrd)
                    if spell_checker.check(wrd):
                        continue

            # Try splitting camel case words and checking each sub-word

            if output_lvl>1:
                print("Trying splitting camel case word")
            sub_words = splitCamelCase(error.word)
            if len(sub_words) > 1:
                ok_flag = True
                for s in sub_words:
                    if not spell_checker.check(s):
                        ok_flag = False
                if ok_flag:
                    continue

            if output_lvl > 1:
                msg = 'error: '+ '\'' + error.word +'\', ' + 'suggestions: ' \
                      + str(spell_checker.suggest())
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
                bad_words.add(m)

    bad_words = sorted(bad_words)

    if output_lvl>1:
        print("\nResults")
        for x in bad_words:
            print(x)

    return bad_words

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('filenames', nargs='*')

    parser.add_argument('--brief', '-b', action='store_true', default=False,
        dest='brief', help='Make output brief')

    parser.add_argument('--verbose', '-v', action='store_true', default=False,
        dest='verbose', help='Make output verbose')

    parser.add_argument('--dict', '-d', action='append',
        dest='dict', help='Add a dictionary (multiples allowed)')

    parser.add_argument('--miss', '-m', action='store_true', default=False,
        dest='miss', help='Only output the misspelt words')

    parser.add_argument('--suffix', '-s', action='store', default=".h",
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


def getMimeType(filepath):

    suffix2mime = { '.h':'text/x-c++', '.py':'text/x-python', '.ruby':'test/x-ruby',
                    '.java':'text/x-java-source' }
    name, ext = os.path.splitext(filepath)
    return suffix2mime[ext]


if __name__ == '__main__':

    args = parse_args()
    # print(args)

    sitk_dict = DictWithPWL('en_US', 'additional_dictionary.txt')

    if args.dict != None:
        for d in args.dict:
            add_dict(sitk_dict, d)

    spell_checker = SpellChecker(sitk_dict,
                                 filters = [EmailFilter, URLFilter])

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

    bad_words = []

    for f in file_list:
        if not args.miss:
            print("\nChecking", f)
        if os.path.isdir(f):
            dir_entries = glob.glob(f+'/**/*'+args.suffix, recursive=True)
            for x in dir_entries:
                if not args.miss:
                    print("\nChecking", x)
                mtype = getMimeType(x)
                result = spell_check_file(x, spell_checker, mimetype=mtype,
                                          output_lvl=output_lvl,
                                          prefixes=['sitk', 'itk', 'vtk'])
                bad_words = sorted(bad_words+result)
        else:
            mtype = getMimeType(f)
            result = spell_check_file(f, spell_checker, mimetype=mtype,
                                      output_lvl=output_lvl,
                                      prefixes=['sitk', 'itk', 'vtk'])

            bad_words = sorted(bad_words+result)


    if not args.miss:
        print ("\nBad words\n")
    for x in bad_words:
        print(x)
