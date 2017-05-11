import os
import subprocess
import arxiv
import pdf2graphs


directory = 'arxiv'
output_folder = 'art'
write_folder = 'wrt'
tar_arxiv = 'arXiv_src_0001_001.tar'

# for tar_arxiv in os.listdir(directory):
arxiv_reader = arxiv.helper(tar_arxiv, write_name='images_0001_001', write=write_folder, output=output_folder, messages=True)

# extract next article
while arxiv_reader.next_article():
	documents = os.listdir(output_folder)
	if not os.path.isdir(write_folder):
		os.mkdir(write_folder)

	# check file types
	for document in documents:
		name, ext = os.path.splitext(document)
		document_path = os.path.join(output_folder,document)
		if ext == '.pdf':
			pdf2graphs.extract(document_path, write=write_folder)

		elif ext == '.tex':
			# parse tex file, retrieve source image filenames
			images = pdf2graphs.parse_tex(document_path)
			# retrieve source images from same directory
			for image in images:
				if image[0] in documents:
					os.rename(os.path.join(output_folder,image[0]), os.path.join(write_folder,image[0]))
					image_name, _ = os.path.splitext(image[0])
					if len(image[1]) > 0:
						tag_file = open(os.path.join(write_folder, "%s.tag" % image_name),'w+')
						for tag in image[1]:
							tag_file.write("%s\n" % tag)

						tag_file.close()

		elif ext != '.ps' and ext != '.eps':
			print("unknown type %s" % document)

	arxiv_reader.write()

arxiv_reader.close()

