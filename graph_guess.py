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
  xs = []
  ys = []
  sizes = []  # node symbol sizes
  indices=[]  # symbol indices
  # first get all the nodes
  for iobj in range(nobjects):
    obj = objects[iobj]
    if(isinstance(obj,EPSVectorPath)):
      # if the path is completed and curved, it probably is a node
      # We will guess that an object is a node if any of the following
      # sets of conditions hold for the  object
      # 1) the object is curved, filled, and small
      # 2) the object is completed, curved, and small
      node_conditions_fulfilled = False
      if(obj.filled and "c" in obj.t):
        node_conditions_fulfilled = True
      if(obj.completed and "c" in obj.t):
        node_conditions_fulfilled = True
       
      if(node_conditions_fulfilled):
        x = np.mean(obj.x)
        y = np.mean(obj.y)
        u = np.array(obj.x)-x
        v = np.array(obj.y)-y
        # estimate node symbol size
        sizes.append(np.mean(np.sqrt(u*u+v*v)))
        indices.append(iobj)
        xs.append(x)
        ys.append(y)
        guess[iobj] = "node"

  # we expect nodes to be of uniform size
  # here we throw away any nodes whose size is more than
  # twenty percent of the mean
  nnodes = len(sizes)
  if (nnodes > 1):
    meansize = np.mean(sizes)
    for i in range(nnodes-1,-1,-1):
      if(sizes[i] < meansize*1.2): 
        g.add_node(xs[i],ys[i])
      else:
        guess[indices[i]] = ""
        del sizes[i]
        del indices[i]
        del xs[i]
        del ys[i]
      
  # next get all the edges
  for iobj in range(nobjects):
    obj = objects[iobj]
    connected_nodes = []
    connected_posit = []
    if(isinstance(obj,EPSVectorPath)):
      # if the path is not completed, it probably is an edge
      # we should therefore connect any nodes occuring as
      # coordinates in order in the sequence of the path
      if(guess[iobj] != "node" and obj.color < 0.01):
        for j in range(obj.n-1):
          x1 = obj.x[j]
          y1 = obj.y[j]
          x2 = obj.x[j+1]
          y2 = obj.y[j+1]
          for i in range(g.n):
            x=g.x[i]
            y=g.y[i]
            u1=np.array([x1-x,y1-y])
            u2=np.array([x2-x,y2-y])
            v=(u2-u1)
            nn=np.linalg.norm(v)
            dd = 1e10
            ww = 0.01
            d1=np.linalg.norm(u1)
            d2=np.linalg.norm(u2)
            if(nn < 1e-2):
              if(d1 < d2):
                dd = d1
                ww = 0.01
              else:
                dd = d2
                ww = 0.99
            else:
              v=v/nn
              comp = np.dot(v,u1)
              d3=np.linalg.norm(u1-comp*v)
              ww = -comp/nn
              if(ww < 0.01 or ww > 0.99):
                if(d1 < d2):
                  dd = d1
                  ww = 0.01
                else:
                  dd = d2
                  ww = 0.99
              else:
                dd = d3
            if(dd-sizes[i]*1.2 < TOUCH_TOLERANCE):
              connected_nodes.append(i)
              connected_posit.append(ww + j)

        # connect approximate nodes in order of appearance
        nn_num = len(connected_nodes)
        if(nn_num>1):
          connected_posit = np.array(connected_posit)
          connected_nodes = np.array(connected_nodes)
          connected_nodes = connected_nodes[connected_posit.argsort()]
          for i in range(nn_num-1):
            g.add_edge(connected_nodes[i],connected_nodes[i+1])

        guess[iobj] = "edge"

  return g

