""" Load Bibtex files into a spell checking dictionary. """

import bibtexparser


def split_bibtex_name(name):
    """
    Split a Bibtex name, which is two words seperated by a number.
    """

    # map any digit to space
    mytable = str.maketrans("0123456789", "          ")
    new_name = name.translate(mytable)

    # split by space
    words = new_name.split()
    return words


def add_bibtex(enchant_dict, filename, verbose=False):
    """Update ``enchant_dict`` spell checking dictionary with names
    from ``filename``, a Bibtex file."""

    if verbose:
        print(f"Bibtex file: {filename}")

    with open(filename, "rt", encoding="utf-8") as biblatex_file:
        bib_database = bibtexparser.load(biblatex_file)

        for k in bib_database.get_entry_dict().keys():
            words = split_bibtex_name(k)
            for w in words:
                enchant_dict.add(w)
                if verbose:
                    print("Added Bibtex word:", w)
