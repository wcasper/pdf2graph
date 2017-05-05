import os
import re
import shutil
import tarfile
import gzip


class helper:
	# opens tarfile for reading
	def __init__(self, name, output='out', messages=False):
		if tarfile.is_tarfile(name):
			# create tar reader, articles are still compressed
			self.block_reader = tarfile.open(name, 'r:')
			self.messages = messages
			if self.messages:
				print('finished opening %s' % name)

			# create iterator for compressed article names
			self.article_names = iter(self.block_reader.getnames())
			self.article = False

			self.block_writer = tarfile.open('labels_%s' % name, 'w:')
			
			self.temp_path = 'tmp'
			self.output_path = output

			self.skipped = list()
		else:
			raise IOError("file is not recognized as tar")

	# fetches next article, unzips and untars it
	# returns none if no more articles
	def next_article(self):
		# delete previous articles
		if self.article:
			if self.messages:
				print("closing article %s" % self.article)
			# remove files from previous article
			if os.path.isdir(self.temp_path):
				shutil.rmtree(self.temp_path)
			if os.path.isdir(self.output_path):
				shutil.rmtree(self.output_path)

		
		self.article = next(self.article_names)
		if self.article.endswith('.pdf'):
			if self.messages:
				print("decompressing pdf %s" % self.article)

			self.block_reader.extract(self.article, path=self.temp_path)
			return self.output_path

		# make sure next article name is a gzip file
		if self.article and not self.article.endswith('.gz'):
			if self.messages:
				print("%s is not a gzip file" % self.article)

			self.skipped.append(self.article)
			return self.next_article()

		# open next article
		if self.article:
			if self.messages:
				print("decompressing article %s" % self.article)
			# uncompress gz file into temp folder
			try:
				self.block_reader.extract(self.article, path=self.temp_path)
				article_tar = tarfile.open(os.path.join(self.temp_path, self.article), 'r:gz')
				article_tar.extractall(path=self.output_path)
				return self.output_path
			except tarfile.ReadError:
				if self.messages:
					print("%s is not gzip or tar file" % self.article)
				
				self.skipped.append(self.article)
				return self.next_article()
		else:
			return None

	# writes input to new tar file with same format
	def write(self, input_folder, name=self.article):
		if not self.article:
			raise Exception("no article has been extracted yet")

		if not os.path.isdir(input_folder):
			raise IOError("%s is not a folder" % input_folder)

		if not os.path.isdir(self.temp_path):
			os.mkdir(self.temp_path)

		# make path if path does not exist
		tar_path = os.path.join(self.temp_path, "%s.tar" % self.article[:-3])
		if not os.path.isdir(os.path.dirname(tar_path)):
			os.mkdir(os.path.dirname(tar_path))

		write_tar = tarfile.open(tar_path, 'w:gz')

		# add files in folder to tar
		for file_name in os.listdir(input_folder):
			write_tar.add(os.path.join(input_folder, file_name), arcname=file_name)

		write_tar.close()

		# add gz file to overall tar file
		self.block_writer.add(tar_path, arcname=name)

		if self.messages:
			print("written items in %s" % input_folder)

	# delete temp folder once done
	# close tarfile
	def close(self):
		if self.messages:
			print("closing arXiv helper")

		if os.path.isdir(self.temp_path):
			shutil.rmtree(self.temp_path)
		if os.path.isdir(self.output_path):
			shutil.rmtree(self.output_path)

		self.block_reader.close()
		self.block_writer.close()