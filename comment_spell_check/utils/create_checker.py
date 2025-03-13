#! /usr/bin/env python

""" Create a case sensitive spell checker with the English dictionary and
    additional dictionaries if provided.
"""

import sys
import importlib.resources
import spellchecker


def create_checker(dict_list="", verbose=False):
    """Create a case sensitive spell checker with the English dictionary and
    additional dictionaries if provided."""

    # create an empty SpellChecker object, because we want a case
    # sensitive checker
    checker = spellchecker.SpellChecker(language=None, case_sensitive=True)

    # load the English dictionary
    lib_path = importlib.resources.files(spellchecker)
    english_dict = str(lib_path) + "/resources/en.json.gz"
    if verbose:
        print("Loading English dictionary from: ", english_dict)
    checker.word_frequency.load_dictionary(english_dict)

    # load the additional dictionaries
    if not isinstance(dict_list, list):
        return checker
    if len(dict_list) > 0:
        for d in dict_list:
            if verbose:
                print("Loading additional dictionary from: ", d)
            checker.word_frequency.load_text_file(d)

    return checker


if __name__ == "__main__":
    print(sys.argv[1:])
    spell = create_checker(sys.argv[1:], True)

    # find those words that may be misspelled
    misspelled = spell.unknown(["something", "is", "hapenning", "here"])

    for word in misspelled:
        print("\nMisspelled: ", word)
        # Get the one `most likely` answer
        print(spell.correction(word))

        # Get a list of `likely` options
        print(spell.candidates(word))

    # test if case sensitive checking from the additional dictionaries works
    my_words = [
        "Zsize",
        "Zuerich",
        "accesor",
        "accessor",
        "zsize",
        "zuerich",
        "sdfasdfas",
    ]

    for w in my_words:
        print(w, w in spell)
