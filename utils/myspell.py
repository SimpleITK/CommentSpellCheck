#! /usr/bin/env python

#==========================================================================
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
#==========================================================================*/

import sys
from enchant.checker import SpellChecker
from enchant.tokenize import EmailFilter, URLFilter
from enchant import DictWithPWL


def myspell(fname):
    my_dict = DictWithPWL("en_US", "mywords.txt")
    print(my_dict)

    spell_checker = SpellChecker(my_dict, filters=[EmailFilter, URLFilter])

    fp = open(fname, "r")

    lc = 1
    for x in fp:
        spell_checker.set_text(x)
        for error in spell_checker:
            print("Error:", error.word, "(line", lc, ")", file=sys.stderr)
        lc = lc + 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for x in sys.argv[1:]:
            myspell(x)
    else:
        print("Usage: myspell.py file1 ... fileN")
