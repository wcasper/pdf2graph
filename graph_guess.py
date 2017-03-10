#!/usr/bin/python

from epsclass import *
from embeddedgraph import *

import numpy as np

TOUCH_TOLERANCE = 0.1 # nodes close enough to edges are ``connected"

##
# Given a list of eps objects, we try to determine which
# are likely nodes and which are edges,
# and based on this, construct graphs
##
def graph_guess(objects):
  nobjects = len(objects)
  guess = [""]*nobjects
  g = EmbeddedGraph()
  sizes = []  # node symbol sizes
  # first get all the nodes
  for iobj in range(nobjects):
    obj = objects[iobj]
    if(isinstance(obj,EPSVectorPath)):
      # if the path is completed and curved, it probably is a node
      if(obj.completed and "c" in obj.t and not "l" in obj.t):
        x = np.mean(obj.x)
        y = np.mean(obj.y)
        u = np.array(obj.x)-x
        v = np.array(obj.y)-y
        # estimate node symbol size
        sizes.append(np.mean(np.sqrt(u*u+v*v)))
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

#        # old algorithm
#        v = [-1]*obj.n
#        for i in range(obj.n):
#          x = obj.x[i]
#          y = obj.y[i]
#          idx,ds = g.nearest_node(x,y)
#          if(ds < 10):
##            v[i] = idx
#            if(i >= 0 and v[i-1] >= 0):
#              g.add_edge(v[i],v[i-1])

        # new algorithm
        # approximate distance of each node from the vector path
        # by using a piecewise linear approximation
        # keep track of this ``closest point on curve``
        dists = [0.0]*g.n
        segment = [-1]*g.n
        wgt = [0.0]*g.n
        for i in range(g.n):
          x=g.x[i]
          y=g.y[i]
          dists[i] = 1e10
          for j in range(obj.n-1):
            u1=np.array([obj.x[j]-x,obj.y[j]-y])
            u2=np.array([obj.x[j+1]-x,obj.y[j+1]-y])
            v=(u2-u1)
            nn=np.linalg.norm(v)
            if(nn < 1e-6):
              nn = -1.0
            v=v/nn
            d1=np.linalg.norm(u1)
            d2=np.linalg.norm(u2)
            d3=np.linalg.norm(u1-np.dot(v,u1)*v)
            if((d3 < d1 and d3 < d2) or nn < 0):
              if(d1 < d2):
                dd = d1
                ww = 0.0
              else:
                dd = d2
                ww = 1.0
            else:
              dd = d3
              ww = np.abs(np.dot(v,u1))/nn
            if(dd < dists[i]):
              dists[i] = max(dd-sizes[i],0)
              segment[i] = j
              wgt[i] = ww

        # connect approximate nodes in order of appearance
        near_nodes = []
        rank = []
        for i in range(g.n):
          if dists[i] < TOUCH_TOLERANCE:
            near_nodes.append(i)
            rank.append(segment[i]+wgt[i])
        nn_num = len(near_nodes)
        if(nn_num>1):
          rank = np.array(rank)
          near_nodes = np.array(near_nodes)
          near_nodes = near_nodes[rank.argsort()]
        for i in range(nn_num-1):
          g.add_edge(near_nodes[i],near_nodes[i+1])

        guess[iobj] = "edge"

  return g

