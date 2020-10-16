# SimpleITKSpellChecking

A script that automatically spell checks the comments of a code base.
It is intended to be run on the SimpleITK and ITK code bases.

Here is how it is typically run:

    python codespell.py --exclude Ancillary $SIMPLEITK_SOURCE_DIR/Code

This will recursively find all the '.h' files in a directory, extract
the C/C++ comments from the code and run a spell checker on them.

In addition to pyenchant's English dictionary, we use the words in 
**additional_dictionary.txt**.  These are proper names and technical
terms harvest by hand from SimpleITK and ITK.

In addition to checking each word against the dictionary, if a word
fails, we try two additional checks.

First, if the word starts with some know prefix, the prefix is removed 
and the remaining word is checked.  The prefixes currently checked
are 'sitk', 'itk', and 'vtk'.  Additional prefixes can be specified
with the '--prefix' command line argument.

Second, we attempt to split the word by capitalization and check each
sub-word.  This is an attempt to detect camel-case words such as
'GetArrayFromImage', which would get split into 'Get', 'Array', 'From',
and 'Image'.  Camel-case words are very commonly used for code elements.
