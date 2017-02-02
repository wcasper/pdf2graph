#!/usr/bin/python

import sys
import subprocess
from epstrim import *
from epsinterpreter import *
from graph_guess import *

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

  # for each pdf page, remove text and convert to jpeg
  images = []
  for ip in range(1,npages+1):
    print("Converting page %i" % ip)
    batcmd1 = "pdftocairo -f %i -l %i -eps %s page.eps" % (ip,ip,pdfname)
    result1 = subprocess.check_output(batcmd1, shell=True)

    ifile = open("page.eps")
    lines = ifile.readlines()
    ifile.close()

    header1, header2 = get_headers(lines)
    footer = get_footer(lines)

    lines = remove_text(lines)
    lines = remove_resources(lines)
    lines = remove_page_setup(lines)
    lines = remove_remainder(lines)

    content = ' '.join(lines)
    eps_objects = get_eps_objects(content)

    graph = graph_guess(eps_objects)
    graphs = get_connected_embedded_subgraphs(graph)

    print("Found %i graphs!" % (len(graphs)))

    images = list()
    for obj in eps_objects:
      if isinstance(obj,EPSImage):
        images.append(obj)

    print("Found %i images!" % len(images))

    # extract images
    for i,image in enumerate(images):
      image_name = "%s-%d-%d" % (pdfname[:-4],ip,i+1)
      ofile = open("%s.eps" % image_name,'w+')
      for line in header1:
        ofile.write(line)

      ofile.write("%%%%BoundingBox: 0 0 %s %s\n" % (image.setup.values[1],image.setup.values[2]))
      for line in header2:
        ofile.write(line)

      # write image
      ofile.write("%s setcolorspace\n" % image.setup.values[11])
      ofile.write("8 dict dup begin\n")
      ofile.write("  /ImageType %s def\n" % image.setup.values[0])
      ofile.write("  /Width %s def\n" % image.setup.values[1])
      ofile.write("  /Height %s def\n" % image.setup.values[2])
      if image.setup.values[3]:
        ofile.write("  /Interpolate %s def\n" % str(image.setup.values[3]).lower())

      ofile.write("  /BitsPerComponent %s def\n" % image.setup.values[4])
      ofile.write("  /Decode [ %s ] def\n" % ' '.join(image.setup.values[5]))
      ofile.write("  /DataSource %s /ASCII85Decode %s %s %s def\n" % tuple(image.setup.values[6:10]))
      ofile.write("  /ImageMatrix [ %s ] def\n" % ' '.join(image.setup.values[10]))
      ofile.write("end\nimage\n")
      ofile.write('\n '.join(image.encoded))
      if image.encoded[-1][-2:] == '~>':
        ofile.write('\nQ\n')
      else:
        ofile.write('\n')

      for line in footer:
        ofile.write(line)

      ofile.close()

      batcmd2 = "convert %s.eps %s.png" % (image_name, image_name)
      result2 = subprocess.check_output(batcmd2, shell=True)

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

    result3 = subprocess.check_output("rm -f *.eps", shell=True)

