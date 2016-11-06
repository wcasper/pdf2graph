#!/usr/bin/python

##
# This script contains routines for extracting the vector objects from an
# EPS file.  It assumes that the EPS file was converted from a pdf by
# cairo, and therefore that the key bindings are a certain way
##
# Author: W.R. Casper
##

import numpy as np

##
# This function removes entries between lines starting with a certain word and
# lines starting with another word
def remove_data_between(lines0,start,end):
  lines = lines0.copy() # don't pulverize incoming data
  nlines = len(lines)
  lstart = len(start)
  lend   = len(end)
  li = 0
  # begin loop over lines
  while True:
    if(li >= len(lines)):
      break
    line = lines[li]
    if(len(line) >= lstart and line[:lstart] == start):
      while True:
        if(line[:lend] == end):
          # delete the end line
          lines.pop(li)
          nlines -= 1
          break
        else:
          # delete first or in-between line
          lines.pop(li)
          nlines -= 1

        # prevent a possible out of bounds array access, even though this
        # shouldn't happen unless eps file format is nonstandard
        if(li == nlines):
          break

        # reset the current line
        line = lines[li]

    else:
      # move to the next line
      # if we've covered all the lines, then exit the loop
      li += 1
      if(li >= nlines):
        break
  # end loop over lines
  return lines

##
# Text in the eps file is bounded by the entries BT and ET
# This function removes all lines between such entries (including BT and ET)
##
def remove_text(lines):
  return remove_data_between(lines,"BT\n","ET\n")

##
# Additional resources in EPS file are bounded by %%BeginResource and
#%%EndResource comments.  This function removes resource entries.
##
def remove_resources(lines):
  return remove_data_between(lines,"%%BeginResource: ","%%EndResource\n")

def remove_page_setup(lines):
  return remove_data_between(lines,"%%BeginPageSetup\n","%%EndPageSetup\n")

def remove_remainder(lines):
  lines = remove_data_between(lines,"%!PS","%%Page:")
  lines = remove_data_between(lines,"showpage\n","%%EOF")
  return lines




