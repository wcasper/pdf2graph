#!/usr/bin/python

from epsclass import *
from embeddedgraph import *

import numpy as np

##
# Given a list of eps objects, we try to determine which
# are likely nodes and which are edges,
# and based on this, construct graphs
##
def graph_guess(objects):
  nobjects = len(objects)
  guess = [""]*nobjects
  g = EmbeddedGraph()
  # first get all the nodes
  for iobj in range(nobjects):
    obj = objects[iobj]
    if(isinstance(obj,EPSVectorPath)):
      # if the path is completed and curved, it probably is a node
      if(obj.completed and "c" in obj.t and not "l" in obj.t):
        x = np.mean(obj.x)
        y = np.mean(obj.y)
        g.add_node(x,y)
        guess[iobj] = "node"

  # next get all the edges
  for iobj in range(nobjects):
    obj = objects[iobj]
    if(isinstance(obj,EPSVectorPath)):
      # if the path is not completed, it probably is an edge
      # we should therefore connect any nodes occuring as
      # coordinates in order in the sequence of the path
      if(guess[iobj] != "node" and obj.color < 0.01):
        v = [-1]*obj.n
        for i in range(obj.n):
          x = obj.x[i]
          y = obj.y[i]
          idx,ds = g.nearest_node(x,y)
          if(ds < 10):
            v[i] = idx
            if(i >= 0 and v[i-1] >= 0):
              g.add_edge(v[i],v[i-1])
        guess[iobj] = "edge"

  return g

