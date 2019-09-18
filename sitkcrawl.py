#! /usr/bin/env python

import SimpleITK as sitk

wrds = dir(sitk)

result= []

for w in wrds:
  x = getattr(sitk,w)
  for y in dir(x):
    if "_" in y:
      continue
    result.append(y)


result2 = sorted(set(result))

for w in result2:
  print(w)
