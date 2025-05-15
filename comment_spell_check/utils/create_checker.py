"""Create a case sensitive spell checker with the English dictionary and
additional dictionaries if provided.
"""

import logging
import importlib.resources
import spellchecker


def create_checker(dict_list: list[str] = None) -> spellchecker.SpellChecker:
    """Create a case sensitive spell checker with the English dictionary and
    additional dictionaries if provided."""

    logger = logging.getLogger("comment_spell_check.create_checker")

    # create an empty SpellChecker object, because we want a case
    # sensitive checker
    checker = spellchecker.SpellChecker(language=None, case_sensitive=True)

    # load the English dictionary
    lib_path = importlib.resources.files(spellchecker)
    english_dict = str(lib_path) + "/resources/en.json.gz"
    logger.info("Loading English dictionary from: %s", english_dict)
    checker.word_frequency.load_dictionary(english_dict)

    # load the additional dictionaries
    if not isinstance(dict_list, list):
        return checker
    if len(dict_list) > 0:
        for d in dict_list:
            logger.info("Loading additional dictionary from: %s", d)
            checker.word_frequency.load_text_file(d)

    return checker
