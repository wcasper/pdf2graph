#!/usr/bin/python

from graph import *

import numpy as np
from matplotlib import pyplot as plt


EMBEDDING_TOLERANCE = 1e-2  # values differing by tolerance are equal

class EmbeddedGraph(Graph):
  def __init__(self):
    Graph.__init__(self)
    self.x = []
    self.y = []

  def plot(self):
    plt.plot(self.x,self.y,'bo')
    for edge in self.e:
      xe = [self.x[edge[0]],self.x[edge[1]]]
      ye = [self.y[edge[0]],self.y[edge[1]]]
      plt.plot(xe,ye,"r-")

  def nearest_node(self,x,y):
    i_min  = 0
    ds_min = 1e20
    for i in range(self.n):
      x1 = self.x[i]
      y1 = self.y[i]
      dx = x1-x
      dy = y1-y
      ds = np.sqrt(dx*dx + dy*dy)

      if(ds < ds_min):
        ds_min = ds
        i_min = i

    return (i_min, ds_min)


  def add_node(self,x,y):
    [i,ds] = self.nearest_node(x,y)
    if(ds < EMBEDDING_TOLERANCE):
      return

    self.v.append(self.n)
    self.n += 1
    self.x.append(x)
    self.y.append(y)
    
  def add_edge(self,i,j):
    if(not [i,j] in self.e and not [j,i] in self.e):
      self.e.append([i,j])


def get_connected_embedded_subgraphs(g0):
  subgraphs = get_connected_subgraphs(g0)

  embedded_subgraphs = []

  for subg in subgraphs:
    embsubg = EmbeddedGraph()

    embsubg.n = subg.n
    embsubg.v = list(range(subg.n))
    for edge in subg.e:
      i = subg.v.index(edge[0])
      j = subg.v.index(edge[1])
      embsubg.add_edge(i,j)
    for i in range(subg.n):
      embsubg.x.append(g0.x[subg.v[i]])
      embsubg.y.append(g0.y[subg.v[i]])

    embedded_subgraphs.append(embsubg)

  return embedded_subgraphs


