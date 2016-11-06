#!/usr/bin/python

class Graph:
  def __init__(self):
    self.n = 0
    self.v = []
    self.e = []

  def add_node(self,val):
    if(not val in self.v):
      self.n += 1
      self.v.append(val)

  def del_node(self,val):
    try:
      self.v.remove(val)
      self.n -= 1
    except:
      return

  def add_edge(self,val1,val2):
    if [val1,val2] in self.e:
      return
    elif [val2,val1] in self.e:
      return
    else:
      self.e.append([val1,val2])

  def del_edge(self,val1,val2):
    if [val1,val2] in self.e:
      self.e.remove([val1,val2])
    elif [val2,val1] in self.e:
      self.e.remove([val2,val1])

  def copy(self):
    g = Graph()
    g.n = self.n
    g.v = self.v[:]
    g.e = self.e[:]
    return g

##
# Return the connected subgraphs of a graph X
##
def get_connected_subgraphs(g0):
  # array of subgraphs
  subgraphs = []

  g = g0.copy()   # copy to avoid pulverizing input
  while(g.n > 0 and len(g.v) > 0 and len(g.e) > 0):
    # get the connected component of first vertex
    # and remove this from the total graph
    subg = Graph()

    subg.add_node(g.v[0])
    g.del_node(g.v[0])

    finished_subgraph = False
    while(not finished_subgraph):
      finished_subgraph = True
      for edge in g.e:
        if(not edge[0] in g.v or not edge[1] in g.v):
          finished_subgraph = False
          if(not edge[0] in subg.v):
            subg.add_node(edge[0])
            g.del_node(edge[0])
          if(not edge[1] in subg.v):
            subg.add_node(edge[1])
            g.del_node(edge[1])
          subg.add_edge(edge[0],edge[1])
          g.del_edge(edge[0],edge[1])
      
    subgraphs.append(subg)
  return subgraphs




