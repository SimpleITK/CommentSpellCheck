# CommentSpellCheck

![python testing](https://github.com/SimpleITK/CommentSpellCheck/actions/workflows/python-app.yml/badge.svg)


A script that automatically spell checks the comments of a code base.
It is intended to be run on the SimpleITK and ITK code bases.

Here is how it is typically run:

    python comment_spell_check.py --exclude Ancillary $SIMPLEITK_SOURCE_DIR/Code

This command will recursively find all the '.h' files in a directory,
extract the C/C++ comments from the code, and run a spell checker on them.
The **'--exclude'** flag tells the script to ignore any file that has
'Ancillary' in its full path name.  This flag will accept any
regular expression.

In addition to pyenchant's English dictionary, we use the words in
**additional_dictionary.txt**.  These words are proper names and
technical terms harvest by hand from the SimpleITK and ITK code bases.

If a word is not found in the dictionaries, we try two additional checks.

1. If the word starts with some known prefix, the prefix is removed
...and the remaining word is checked against the dictionary.  The prefixes
...used by default are **'sitk'**, **'itk'**, and **'vtk'**.  Additional
...prefixes can be specified with the **'--prefix'** command line argument.

2. We attempt to split the word by capitalization and check each
...sub-word against the dictionary.  This method is an attempt to detect
...camel-case words such as 'GetArrayFromImage', which would get split into
...'Get', 'Array', 'From', and 'Image'.  Camel-case words are very commonly
...used for code elements.

The script can also process other file types.  With the **'--suffix'**
option, the following file types are available: Python (.py), C/C++
(.c/.cxx), Text (.txt), reStructuredText(.rst), Markdown (.md), Ruby (.ruby),
and Java (.java).  Note that reStructuredText files are treated as standard
text.  Consequentially, all markup keywords that are not actual words will
need to be added to the additional/exception dictionary.
