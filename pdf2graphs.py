#!/usr/bin/python

import os
import sys
import subprocess
import argparse

from epstrim import *
from epsinterpreter import *
from graph_guess import *
from tex2eps import *


parser = argparse.ArgumentParser()
parser.add_argument('-f','--first',action='store',nargs=1,default=[1],help='first page')
parser.add_argument('-l','--last',action='store',nargs=1,default=[1023],help='last page')
parser.add_argument('-g','--graphs',action='store_true',default=False,help='only extract vector image graphs from pdf')
parser.add_argument('-i','--images',action='store_true',default=False,help='only extract images from pdf')
parser.add_argument('-a','--author',action='store',nargs=1,default='',help='author information for database entries')
parser.add_argument('-o','--output',action='store',nargs=1,default='png',help='filetype for image output, supports png, jpeg, and eps')
parser.add_argument('--folder',action='store_true',default=False,help='specify folder of pdfs instead of pdf name')
parser.add_argument('pdf')

args = parser.parse_args()

##
# convert pdf pages to graphs and output in json format
##

def write_json(label,metadata,g,ofile):
  ofile.write("\"%s\": {\n" % label)
  ofile.write("  \"vertices\": [")
  ofile.write(','.join([str(vert + 1) for vert in g.v]))
  ofile.write("],\n")
  ofile.write("  \"edges\": [")
  ofile.write(','.join(["[%i,%i]" % (edge[0]+1,edge[1]+1) for edge in g.e]))
  ofile.write("],\n")
  ofile.write("  \"embedding\": [")
  ofile.write(','.join(["[%.3f,%.3f]" % (g.x[i],g.y[i]) for i in range(g.n)]))
  ofile.write("],\n")
  ofile.write("  \"degrees\": [")
  degrees = g.get_degree_sequence()
  ofile.write(','.join([str(deg) for deg in degrees]))
  ofile.write("],\n")
  for pair in metadata[:-2]:
    ofile.write("  \"%s\": [\"%s\"],\n" % (pair[0],pair[1]))
  pair = metadata[-1]
  ofile.write("  \"%s\": [\"%s\"]\n" % (pair[0],pair[1]))
  ofile.write("}\n\n")


def extract_graphs(page,eps_objects,folder='.'):
  graph = graph_guess(eps_objects)
  graphs = get_connected_embedded_subgraphs(graph)

  print("Found %i graphs!" % (len(graphs)))
  # generate report page
  for g in graphs:
    g.plot()
  
  if(len(graphs) > 0):
    plt.savefig("%s/page_%i.png" % (folder,page))
    plt.clf()
    ofile_name = "%s/page_%i.json" % (folder,page)
    ofile = open(ofile_name,"w")

    metadata = [["comments", "Graph found on page %i of %s" % (page,args.pdf)],\
                ["references", args.pdf],\
                ["authors", args.author]]

    for ig in range(len(graphs)):
      g = graphs[ig]
      label = "page%igraph%i" % (page,ig)
      write_json(label,metadata,g,ofile)
    
    ofile.close()


def extract_images(page,lines,eps_objects,folder='.',output='png'):
  header1, header2 = get_headers(lines)
  footer = get_footer(lines)

  images = list()
  for obj in eps_objects:
    if isinstance(obj,EPSImage):
      images.append(obj)

  print("Found %i images!" % len(images))

  # extract images
  for i,image in enumerate(images):
    if image.encoded is not None: 
      image_name = "%d-%d" % (page,i+1)
      ofile = open("%s/%s.eps" % (folder,image_name),'w+')
      for line in header1:
        ofile.write(line)

      ofile.write("%%%%BoundingBox: 0 0 %s %s\n" % (image.setup.values[1],image.setup.values[2]))
      for line in header2:
        ofile.write(line)

      # write image
      if image.setup.values[11] is not None:
        ofile.write("%s setcolorspace\n" % image.setup.values[11])
      ofile.write("8 dict dup begin\n")
      ofile.write("  /ImageType %s def\n" % image.setup.values[0])
      ofile.write("  /Width %s def\n" % image.setup.values[1])
      ofile.write("  /Height %s def\n" % image.setup.values[2])
      if image.setup.values[3] is not None:
        ofile.write("  /Interpolate %s def\n" % str(image.setup.values[3]).lower())

      ofile.write("  /BitsPerComponent %s def\n" % image.setup.values[4])
      ofile.write("  /Decode [ %s ] def\n" % ' '.join(image.setup.values[5]))
      ofile.write("  /DataSource %s /ASCII85Decode %s %s %s def\n" % tuple(image.setup.values[6:10]))
      ofile.write("  /ImageMatrix [ %s ] def\n" % ' '.join(image.setup.values[10]))
      ofile.write("end\n%s\n" % image.setup.values[12])
      ofile.write('\n '.join(image.encoded))
      if image.encoded[-1][-2:] == '~>':
        ofile.write('\nQ\n')
      else:
        ofile.write('\n')

      for line in footer:
        ofile.write(line)

      ofile.close()

      if output != 'eps':
        batcmd2 = "convert %s/%s.eps %s/%s.%s" % (folder,image_name,folder,image_name,output)
        result2 = subprocess.check_output(batcmd2, shell=True)
  

if __name__ == '__main__':
  if args.folder:
    for filename in os.listdir(args.pdf):
      if filename.endswith('.pdf'):
        # get number of pages for pdf
        batcmd="pdfinfo %s/%s | grep -i Pages" % (args.pdf,filename)
        result = subprocess.check_output(batcmd, shell=True)
        npages = int(str(result).split()[1].replace("\\n'",""))
        print(filename,"has", npages,"pages")

        if not os.path.exists(filename[:-4]):
          os.makedirs(filename[:-4])

        # for each pdf page, remove text and convert to jpeg
        images = []
        for ip in range(1,npages+1):
          print("Converting page %i" % ip)
          batcmd1 = "pdftocairo -f %i -l %i -eps %s/%s page.eps" % (ip,ip,args.pdf,filename)
          result1 = subprocess.check_output(batcmd1, shell=True)

          ifile = open("page.eps")
          lines = ifile.readlines()
          ifile.close()

          temp = remove_text(lines)
          temp = remove_resources(temp)
          temp = remove_page_setup(temp)
          temp = remove_remainder(temp)

          content = ' '.join(lines)
          eps_objects = get_eps_objects(content)

          if args.graphs or not args.images:
            extract_graphs(ip,eps_objects,folder=filename[:-4])

          if not args.graphs or args.images:
            extract_images(ip,lines,eps_objects,folder=filename[:-4],output=args.output)

  else: 
    if args.pdf.endswith('.pdf'):
      # get number of pages for pdf
      batcmd="pdfinfo %s | grep -i Pages" % args.pdf
      result = subprocess.check_output(batcmd, shell=True)
      npages = int(str(result).split()[1].replace("\\n'",""))
      print("PDF has", npages, "pages")

      first_page = max(1,min(int(args.first[0]),npages))
      last_page = min(npages,max(int(args.last[0]),1)) + 1

      # for each pdf page, remove text and convert to jpeg
      images = []
      for ip in range(first_page,last_page):
        print("Converting page %i" % ip)
        batcmd1 = "pdftocairo -f %i -l %i -eps %s page.eps" % (ip,ip,args.pdf)
        result1 = subprocess.check_output(batcmd1, shell=True)

        ifile = open("page.eps")
        lines = ifile.readlines()
        ifile.close()

        temp = remove_text(lines)
        temp = remove_resources(temp)
        temp = remove_page_setup(temp)
        temp = remove_remainder(temp)

        content = ' '.join(lines)
        eps_objects = get_eps_objects(content)

        if args.graphs or not args.images:
          extract_graphs(ip,eps_objects)

        if not args.graphs or args.images:
          extract_images(ip,lines,eps_objects,output=args.output)


    elif args.pdf.endswith('.eps'):
      # already an eps image
      # convert to pdf and then back to eps with cairo
      batcmd="epstopdf %s -o tmp.pdf" % (args.pdf)
      result = subprocess.check_output(batcmd, shell=True)
      batcmd="pdftocairo tmp.pdf -ps tmp.ps -origpagesizes"
      result = subprocess.check_output(batcmd, shell=True)

      epsfile = open("tmp.ps","r")
      lines = epsfile.readlines()
      epsfile.close()


      temp = remove_text(lines)
      temp = remove_resources(temp)
      temp = remove_page_setup(temp)
      temp = remove_remainder(temp)

      content = ' '.join(lines)
      eps_objects = get_eps_objects(content)

      if args.graphs or not args.images:
        extract_graphs(0,eps_objects)

      if not args.graphs or args.images:
        extract_images(0,lines,eps_objects,output=args.output)


#  result3 = subprocess.check_output("rm -f *.eps", shell=True)

