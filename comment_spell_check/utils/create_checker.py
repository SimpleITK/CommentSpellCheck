"""Create a case sensitive spell checker with the English dictionary and
additional dictionaries if provided.
"""

import logging
import importlib.resources
import spellchecker
import requests


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
    checker.word_frequency.load_dictionary(english_dict)
    logger.info("Loaded %s", english_dict)
    logger.info("%d words", checker.word_frequency.unique_words)

    # load the additional dictionaries
    if not isinstance(dict_list, list) or not dict_list:
        return checker

    for d in dict_list:

        # load dictionary from URL
        try:
            response = requests.get(d)
            response.raise_for_status()
            checker.word_frequency.load_text(response.text)

        except requests.exceptions.MissingSchema:
            # URL didn't work so assume it's a local file path
            try:
                checker.word_frequency.load_text_file(d)
            except IOError:
                logger.error("Error loading %s", d)
                continue

        except requests.exceptions.RequestException as e:
            logger.error("Error loading dictionary from URL %s: %s", d, e)
            continue

        logger.info("Loaded %s", d)
        logger.info("%d words", checker.word_frequency.unique_words)

    return checker
