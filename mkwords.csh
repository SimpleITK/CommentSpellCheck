#! /bin/csh -f

itkcrawl.py > itk-words.txt
sitkcrawl.py > sitk-words.txt
cat additional_dictionary.txt  sitk-words.txt itk-words.txt  | sort -u > mywords.txt
