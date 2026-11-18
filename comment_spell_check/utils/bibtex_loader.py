"""Load Bibtex files into a spell checking dictionary."""

import logging
import bibtexparser
import spellchecker


def split_bibtex_name(name: str) -> list[str]:
    """
    Split a Bibtex name, which is two words seperated by a number.
    """

    # map any digit to space
    mytable = str.maketrans("0123456789", "          ")
    new_name = name.translate(mytable)

    # split by space
    words = new_name.split()
    return words


def add_bibtex(spell: spellchecker.SpellChecker, filename: str):
    """Update ``spell`` spell checking dictionary with names
    from ``filename``, a Bibtex file."""

    logger = logging.getLogger("comment_spell_check.bibtex_loader")
    logger.info("Bibtex file: %s", filename)

    word_list = []

    if hasattr(bibtexparser, "parse_file"):
        bib_database = bibtexparser.parse_file(filename)
        entry_keys = (entry.key for entry in bib_database.entries)
    else:
        with open(filename, "rt", encoding="utf-8") as biblatex_file:
            bib_database = bibtexparser.load(biblatex_file)
        entry_keys = bib_database.get_entry_dict()

    for key in entry_keys:
        words = split_bibtex_name(key)
        word_list.extend(words)

    logger.info("Words: %s", word_list)
    spell.word_frequency.load_words(word_list)
