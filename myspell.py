#! /usr/bin/env python

import os
from enchant.checker import SpellChecker
from enchant.tokenize import Filter, EmailFilter, URLFilter
from enchant import DictWithPWL


def myspell(fname):
    my_dict = DictWithPWL('en_US', 'mywords.txt')
    print(my_dict)

    spell_checker = SpellChecker(my_dict, filters = [EmailFilter, URLFilter])

    fp = open(fname, 'r')

    lc = 1
    for x in fp:
      spell_checker.set_text(x)
      for error in spell_checker:
        print("Error:", error.word, "(line", lc, ")")
      lc = lc+1


#myspell('/Users/dchen/SimpleITK/Documentation/docs/source/faq.rst')
myspell('/Users/dchen/SimpleITK/Code/Common/include/sitkImage.h')

