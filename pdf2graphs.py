#!/usr/bin/python

import sys
import subprocess
from epstrim import *
from epsinterpreter import *
from graph_guess import *
from image_decode import *

##
# parse command line input
##
try:
  pdfname = sys.argv[1]
except:
  print("Error: expected input file name on command line")
  sys.exit(1)


##
# convert pdf pages to graphs and output in json format
##

def write_json(label,metadata,g,ofile):
  ofile.write("{ \"%s\": {\n" % label)
  ofile.write("  \"vertices\": [")
  ofile.write(','.join([str(vert + 1) for vert in g.v]))
  ofile.write("],\n")
  ofile.write("  \"edges\": [")
  ofile.write(','.join(["[%i,%i]" % (edge[0]+1,edge[1]+1) for edge in g.e]))
  ofile.write("],\n")
  for pair in metadata[:-2]:
    ofile.write("  \"%s\": [\"%s\"],\n" % (pair[0],pair[1]))
  pair = metadata[-1]
  ofile.write("  \"%s\": [\"%s\"]\n" % (pair[0],pair[1]))
  ofile.write("}}\n\n")

if __name__ == '__main__':
  # get number of pages for pdf
  batcmd="pdfinfo %s | grep -i Pages" % pdfname
  result = subprocess.check_output(batcmd, shell=True)
  npages = int(str(result).split()[1].replace("\\n'",""))
  print("PDF has", npages, "pages")

  # TODO, extract images by decoding (ascii85?) string after image tags and types
  # TODO, pair recreations of graphs with extracted JSON in validation step
  # TODO, simple graph check, removes graphs with no edges or low vertices (2 or less)

  # for each pdf page, remove text and convert to jpeg
  images = []
  for ip in range(1,npages+1):
    print("Converting page %i" % ip)
    batcmd1 = "pdftocairo -f %i -l %i -eps %s page.eps" % (ip,ip,pdfname)
    result1 = subprocess.check_output(batcmd1, shell=True)

    ifile = open("page.eps")
    lines = ifile.readlines()
    ifile.close()

    
    lines = remove_text(lines);
    lines = remove_resources(lines);
    lines = remove_page_setup(lines);
    lines = remove_remainder(lines);

    content = ' '.join(lines)
    eps_objects = get_eps_objects(content)

    graph = graph_guess(eps_objects)
    graphs = get_connected_embedded_subgraphs(graph)

    print("Found %i graphs!" % (len(graphs)))

    images = list()
    count = 1
    for obj in eps_objects:
      if isinstance(obj,EPSImage):
        # decode
        # output decoding as %i-%i.png % (ip, count)
        images.append(obj)
        count += 1


    print("Found %i images!" % len(images))

    # generate report page
    for g in graphs:
      g.plot()
    if(len(graphs) > 0):
      plt.savefig("page_%i.png" % ip)
      plt.clf()
      ofile_name = "page_%i.json" % ip
      ofile = open(ofile_name,"w")

      metadata = [["comments", "Graph found on page %i of %s" % (ip, pdfname)],\
                  ["references", pdfname]]

      for ig in range(len(graphs)):
        g = graphs[ig]
        label = "page%igraph%i" % (ip,ig)
        write_json(label,metadata,g,ofile)
    
      ofile.close()
