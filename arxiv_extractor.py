import arxiv
import pdf2graphs
import argparse

from shutil import copyfile
from os import mkdir, listdir, path

parser = argparse.ArgumentParser(description="extracts and runs pdf2graphs on arXiv tar")
parser.add_argument('arxiv', type=str, help='name of arxiv to process')
parser.add_argument('output', type=str, help='name of output tar')
args = parser.parse_args()

output_folder = 'art'
write_folder = 'wrt'

# for tar_arxiv in os.listdir(directory):
arxiv_reader = arxiv.helper(args.arxiv, write_name=args.output, write=write_folder, output=output_folder, messages=True)

# extract next article
while arxiv_reader.next_article():
	documents = listdir(output_folder)
	if not path.isdir(write_folder):
		mkdir(write_folder)

	# check file types
	for document in documents:
		name, ext = path.splitext(document)
		document_path = path.join(output_folder,document)
		if ext == '.pdf':
			pdf2graphs.extract(document_path, write=write_folder)

		elif ext == '.tex':
			# parse tex file, retrieve source image filenames
			images = pdf2graphs.parse_tex(document_path)
			
			# unable to read file
			if not images:
				arxiv_reader.skipped.append(document)
				continue

			for image in images:
				if image[0] in documents:
					copyfile(path.join(output_folder,image[0]), path.join(write_folder,image[0]))
					image_name, _ = path.splitext(image[0])
					if len(image[1]) > 0:
						tag_file = open(path.join(write_folder, "%s.tag" % image_name),'w+')
						for tag in image[1]:
							tag_file.write("%s\n" % tag)

						tag_file.close()

		elif ext not in ['.eps','.ps','.jpg','.png','.sty']:
			print("unknown type %s" % document)

	arxiv_reader.write()

arxiv_reader.close()

