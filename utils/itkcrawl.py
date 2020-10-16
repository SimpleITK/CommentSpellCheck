#! /usr/bin/env python

import itk

wrds = dir(itk)

result= []

for w in wrds:
    x = getattr(itk,w)
    for y in dir(x):
        if "_" in y:
            continue
        result.append(y)


result2 = sorted(set(result))

for w in result2:
    if len(w)>2:
        print(w)
