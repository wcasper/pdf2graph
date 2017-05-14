#!/usr/bin/python

import os
import sys
import subprocess
import argparse
import re

from epstrim import *
from epsinterpreter import *
from graph_guess import *
from imagecv import *

##
# parse command line input
##
parser = argparse.ArgumentParser()
parser.add_argument('-f','--first',action='store',nargs=1,default=[1],help='first page')
parser.add_argument('-l','--last',action='store',nargs=1,default=[1023],help='last page')
parser.add_argument('-g','--graphs',action='store_true',default=False,help='only extract vector image graphs from pdf')
parser.add_argument('-i','--images',action='store_true',default=False,help='only extract images from pdf')
parser.add_argument('-a','--author',action='store',nargs=1,default='',help='author information for database entries')
parser.add_argument('-o','--output',action='store',nargs=1,default='png',help='filetype for image output, supports png, jpeg, and eps')
parser.add_argument('--folder',action='store_true',default=False,help='specify folder of pdfs instead of pdf name')
parser.add_argument('pdf')


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

##
# extract graphs from vector objects
##
def extract_graphs(page,eps_objects,write='.'):
	graph = graph_guess(eps_objects)
	graphs = get_connected_embedded_subgraphs(graph)

	print("Found %i graphs!" % (len(graphs)))
	# generate report page
	for g in graphs:
		g.plot()
	
	if(len(graphs) > 0):
		if not os.path.isdir(write):
			os.mkdir(write)
		
		plt.savefig("%s/page_%i.png" % (write,page))
		plt.clf()
		ofile_name = "%s/page_%i.json" % (write,page)
		ofile = open(ofile_name,"w")

		metadata = [["comments", "Graph found on page %i of %s" % (page,args.pdf)],\
								["references", args.pdf],\
								["authors", args.author]]

		for ig in range(len(graphs)):
			g = graphs[ig]
			label = "page%igraph%i" % (page,ig)
			write_json(label,metadata,g,ofile)
		
		ofile.close()

##
# extract images from image objects
##
def extract_images(page,lines,eps_objects,write='.',image_type='png'):
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
			if not os.path.isdir(write):
				os.mkdir(write)

			ofile = open("%s/%s.eps" % (write,image_name),'w+')
			for line in header1:
				ofile.write(line)

			ofile.write("%%%%BoundingBox: 0 0 %s %s\n" % (image.setup.values[1],image.setup.values[2]))
			for line in header2:
				ofile.write(line)

			# write image
			if image.setup.values[11] is not None:
				ofile.write("%s setcolorspace\n" % image.setup.values[11])
			ofile.write("8 dict dup begin\n")
			ofile.write("	/ImageType %s def\n" % image.setup.values[0])
			ofile.write("	/Width %s def\n" % image.setup.values[1])
			ofile.write("	/Height %s def\n" % image.setup.values[2])
			if image.setup.values[3] is not None:
				ofile.write("	/Interpolate %s def\n" % str(image.setup.values[3]).lower())

			ofile.write("	/BitsPerComponent %s def\n" % image.setup.values[4])
			ofile.write("	/Decode [ %s ] def\n" % ' '.join(image.setup.values[5]))
			ofile.write("	/DataSource %s /ASCII85Decode %s %s %s def\n" % tuple(image.setup.values[6:10]))
			ofile.write("	/ImageMatrix [ %s ] def\n" % ' '.join(image.setup.values[10]))
			ofile.write("end\n%s\n" % image.setup.values[12])
			ofile.write('\n '.join(image.encoded))
			if image.encoded[-1][-2:] == '~>':
				ofile.write('\nQ\n')
			else:
				ofile.write('\n')

			for line in footer:
				ofile.write(line)

			ofile.close()

			if image_type != 'eps':
				batcmd2 = "convert %s/%s.eps %s/%s.%s" % (read,image_name,write,image_name,image_type)
				result2 = subprocess.check_output(batcmd2, shell=True)

def parse_tex(filename):
	# parse tex file
	try:
		tex_file = open(filename,'r')
		lines = tex_file.readlines()
		tex_file.close()
	except UnicodeDecodeError:
		print("unable to parse %s" % filename)
		return None

	images = list()

	# while next_line
	i = 0
	while i < len(lines):
		if lines[i].startswith('%'):
			# line is a comment
			pass

		elif "\\begin{figure}" in lines[i]:
			tags = set()
			filename = str()
			i += 1
			while i < len(lines) and "\\end{figure}" not in lines[i]:
				if "\\caption" in lines[i]:
					# get keywords from caption
					caption = re.search("\\caption{(.*)}", lines[i])
					if caption:
						tokens = re.sub("[^\w']", ' ', caption.group(1)).split()
						for token in tokens:
							if len(token) > 3:
								tags.add(token.lower())
					else:
						content = lines[i].split("\\caption{")
						if len(content) > 1:
							tokens = re.sub("[^\w']", ' ', content[1]).split()
							for token in tokens:
								if len(token) > 3:
									tags.add(token.lower())

						# multiline caption
						while i < len(lines) and '}' not in lines[i]:
							tokens = re.sub("[^\w']", ' ', lines[i]).split()
							for token in tokens:
								if len(token) > 3:
									tags.add(token.lower())

							i += 1

						if i < len(lines):
							content = lines[i].split('}')[0]
							tokens = re.sub("[^\w']", ' ', content).split()
							for token in tokens:
								if len(token) > 3:
									tags.add(token.lower())
							
							i += 1
			
				elif "\\includegraphics" in lines[i]:
					# get filename
					search = re.search("\\includegraphics(\[.*\])?{([\w\.\-]+)}", lines[i])
					if search:
						filename = search.group(2)		
					
				elif "\\psfig" in lines[i]:
					# get filename
					search = re.search("\\psfig{(file=)?([\w\.\-]+)(,[^=]+=[^=]+)*}", lines[i])
					if search:
						filename = search.group(2)

				elif "\\epsffile" in lines[i]:
					search = re.search("\\epsffile{([\w\.\-]+)}", lines[i])
					if search:
						filename = search.group(1)

				elif "\\plotone" in lines[i]:
					search = re.search("\\plotone{([\w\.\-]+)}", lines[i])
					if search:
						filename = search.group(1)
				
				i += 1
				
			if i < len(lines):
				images.append((filename, tags))

		elif "\\includegraphics" in lines[i]:
			# get filename
			search = re.search("\\includegraphics(\[.*\])?{([\w\.\-]+)}", lines[i])
			if search:
				images.append((search.group(2), list()))
			
		elif "\\psfig" in lines[i]:
			# get filename
			search = re.search("\\psfig{(file=)?([\w\.\-]+)(,[^=]+=[^=]+)*}", lines[i])
			if search:
				images.append((search.group(2), list()))

		elif "\\epsffile" in lines[i]:
			search = re.search("\\epsffile{([\w\.\-]+)}", lines[i])
			if search:
				images.append((search.group(1), list()))

		elif "\\plotone" in lines[i]:
			search = re.search("\\plotone{([\w\.\-]+)}", lines[i])
			if search:
				images.append((search.group(1), list()))

		i += 1
	
	return images

def extract(filename,write='.',image_type='png'):
	if filename.endswith('.pdf'):
		# get number of pages for pdf
		batcmd="pdfinfo %s | grep -i Pages" % filename
		result = subprocess.check_output(batcmd, shell=True)
		npages = int(str(result).split()[1].replace("\\n'",""))
		print("PDF has", npages, "pages")

		# get number of fonts used in pdf
		# if zero fonts then pdf is scanned and requires image processing
		batcmd0 = "pdffonts %s | wc -l" % filename
		nfonts = int(subprocess.check_output(batcmd0, shell=True)) - 2

		if not nfonts:
			batcmd00="pdftoppm -png %s page" % filename
			subprocess.check_output(batcmd00, shell=True)
			dirname = filename[0:-4]
			subprocess.check_output('mkdir -p ' + dirname, shell=True)

			for ip in range(1,npages+1):
				imput = "page-%s.png" % str(ip).zfill(len(str(npages)))
				find_images(imput, dirname)
		else:
			# for each pdf page, remove text and convert to jpeg
			for ip in range(1,npages+1):
				print("Converting page %i" % ip)
				batcmd1 = "pdftocairo -f %i -l %i -eps %s page.eps" % (ip,ip,filename)
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

				extract_graphs(ip,eps_objects,write=write)
				extract_images(ip,lines,eps_objects,write=write,image_type=image_type)

	elif filename.endswith('.eps'):
		# already an eps image
		# convert to pdf and then back to eps with cairo
		batcmd="epstopdf %s -o tmp.pdf" % (filename)
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

		extract_graphs(ip,eps_objects,write=write)
		extract_images(ip,lines,eps_objects,write=write,image_type=image_type)


def extract(filename,first=0,last=sys.maxsize,graphs=True,images=True,author=None,write='.',image_type='png'):
  if filename.endswith('.pdf'):
    # get number of pages for pdf
    batcmd="pdfinfo %s | grep -i Pages" % filename
    result = subprocess.check_output(batcmd, shell=True)
    npages = int(str(result).split()[1].replace("\\n'",""))
    print("PDF has", npages, "pages")

    first_page = max(1,min(first,npages))
    last_page = min(npages,max(last,1)) + 1

    # get number of fonts used in pdf
    # if zero fonts then pdf is scanned and requires image processing
    batcmd0 = "pdffonts %s | wc -l" % filename
    nfonts = int(subprocess.check_output(batcmd0, shell=True)) - 2

    if not nfonts:
      batcmd00="pdftoppm -png %s page" % filename
      subprocess.check_output(batcmd00, shell=True)
      dirname = filename[0:-4]
      subprocess.check_output('mkdir -p ' + dirname, shell=True)

      for ip in range(first_page,last_page):
        imput = "page-%s.png" % str(ip).zfill(len(str(npages)))
        find_images(imput, dirname)
    else:
      # for each pdf page, remove text and convert to jpeg
      for ip in range(first_page,last_page):
        print("Converting page %i" % ip)
        batcmd1 = "pdftocairo -f %i -l %i -eps %s page.eps" % (ip,ip,filename)
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

        if graphs or not images:
          extract_graphs(ip,eps_objects)

        if not graphs or images:
          extract_images(ip,lines,eps_objects,write=write,image_type=image_type)

  elif filename.endswith('.eps'):
    # already an eps image
    # convert to pdf and then back to eps with cairo
    batcmd="epstopdf %s -o tmp.pdf" % (filename)
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

    if graphs or not images:
      extract_graphs(0,eps_objects)

    if not graphs or images:
      extract_images(0,lines,eps_objects,output=output)


if __name__ == '__main__':
	args = parser.parse_args()
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
				for ip in range(1,npages+1):
					# get number of fonts used in pdf
					# if zero fonts then pdf is scanned and requires image processing
					batcmd0 = "pdffonts %s | wc -l" % filename
					nfonts = int(subprocess.check_output(batcmd0, shell=True)) - 2
					if nfonts > 0:
						batcmd00="pdftoppm -png %s page" % filename
						subprocess.check_output(batcmd00, shell=True)
						dirname = filename[0:-4]
						subprocess.check_output('mkdir -p ' + dirname, shell=True)
						for ip in range(1, npages+1):
							imput = "page-%s.png" % str(ip).zfill(len(str(npages)))
							find_images(imput, dirname)
					else:
						# regular pdf, extract images and vector graphics
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

	elif args.pdf.endswith('.pdf'):
		# get number of pages for pdf
		batcmd="pdfinfo %s | grep -i Pages" % args.pdf
		result = subprocess.check_output(batcmd, shell=True)
		npages = int(str(result).split()[1].replace("\\n'",""))
		print("PDF has", npages, "pages")

		first_page = max(1,min(int(args.first[0]),npages))
		last_page = min(npages,max(int(args.last[0]),1)) + 1

		# get number of fonts used in pdf
		# if zero fonts then pdf is scanned and requires image processing
		batcmd0 = "pdffonts %s | wc -l" % args.pdf
		nfonts = int(subprocess.check_output(batcmd0, shell=True)) - 2

		if not nfonts:
			batcmd00="pdftoppm -png %s page" % args.pdf
			subprocess.check_output(batcmd00, shell=True)
			dirname = args.pdf[0:-4]
			subprocess.check_output('mkdir -p ' + dirname, shell=True)

			for ip in range(first_page,last_page):
				imput = "page-%s.png" % str(ip).zfill(len(str(npages)))
				find_images(imput, dirname)
		else:
			# for each pdf page, remove text and convert to jpeg
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

