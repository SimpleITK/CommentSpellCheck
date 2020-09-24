#! /usr/bin/env

import sys
import argparse

from enchant.checker import SpellChecker
from enchant.tokenize import Filter, EmailFilter, URLFilter
from enchant import DictWithPWL

from comment_parser import comment_parser


src_file = '/Users/dchen/SimpleITK/Code/Common/include/sitkImage.h'



def spell_check_file(filename, spell_checker, mimetype='text/x-c++', output_lvl=1):

    # Returns a list of comment_parser.parsers.common.Comments
    clist = comment_parser.extract_comments(filename, mime=mimetype)

    bad_words = set()

    for c in clist:
        mistakes=[]
        spell_checker.set_text(c.text())
        for error in spell_checker:
            if output_lvl > 1:
                msg = 'error: '+ '\'' + error.word +'\', ' + 'suggestions: ' \
                      + str(spell_checker.suggest())
            else:
                msg = error.word
            mistakes.append(msg)
        if len(mistakes):
            if output_lvl > 0:
                print("\nLine number", c.line_number())
            if output_lvl > 1:
                print(c.text())
            for m in mistakes:
                if output_lvl >= 0:
                    print("   ", m)
                bad_words.add(m)

    return sorted(bad_words)

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

    args = parser.parse_args()
    return args


def add_dict(enchant_dict, filename):
    with open(filename) as f:
        lines = f.read().splitlines()

    # You better not have more than 1 word in a line
    for wrd in lines:
        enchant_dict.add_to_pwl(wrd)



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

    bad_words = spell_check_file(src_file, spell_checker, output_lvl=output_lvl)


    if not args.miss:
        print ("\nBad words\n")
    for x in bad_words:
        print(x)
