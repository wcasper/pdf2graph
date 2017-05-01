import os
import subprocess
import arxiv
import pdfs2graphs


directory = 'arxiv'
output_folder = 'art'
write_folder = 'wrt'

for tar_arxiv in os.listdir(directory):
	arxiv_reader = arxiv.helper(tar_arxiv, output=output_folder, messages=True)

	# extract next article
	while arxiv_reader.next_article():
		for document in os.listdir(output):
			name, ext = os.path.splitext(document)
			if ext == '.pdf':
				# run pdfs2graphs on pdf
				pass
			if ext == '.ps' or ext == '.eps':
				# convert to png
				subprocess.check_output("convert %s %s.png" % (document, name), shell=True)
				# move file to write folder
			elif ext == '.tex':
				# compile to pdf
				# compile to ps
				pass
			# if old postscript
				# convert to pdf
				# convert pdf to new postscript
			# if sty
				# skip loop
			# add to write folder
		# add all images in folder to write folder
		# run pdf2graphs on it, place output in write folder
		arxiv.write(write_folder)

	arxiv_reader.close()
