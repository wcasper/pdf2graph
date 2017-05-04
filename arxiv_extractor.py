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
			if ext == '.pdf' or ext == 'eps':
				# edit pdfs2graphs to handle case where eps is a figure
				pdfs2graphs.extract(os.path.join(output_folder,document), write=write_folder)
			elif ext == '.ps':
				# convert to desired image format, move to new folder
				bat_cmd = "convert %s/%s %s/%s.png" % (output_folder, document, write_folder, name)
				subprocess.check_output(bat_cmd, shell=True)
			elif ext == '.tex':
				# compile to pdf
				bat_cmd = "pdflatex %s" % document
				subprocess.check_output(bat_cmd, shell=True)
				pdfs2graphs.extract(os.path.join(output_folder,document), write=write_folder)
			else:
				# other cases
				pass
		arxiv.write(write_folder)

	arxiv_reader.close()
