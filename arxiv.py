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
			self.article = next(self.article_names)

			# check structure of tar file
			if not re.match(r'\d\d\d\d', self.article):
				raise IOError("file format does not match arXiv format")

			self.block_writer = tarfile.open('labels_%s' % name, 'w:')
			self.temp_path = 'tmp'
			self.output_path = output
		else:
			raise IOError("file is not recognized as tar")

	# fetches next article, unzips and untars it
	# returns none if no more articles
	def next_article(self):
		# delete previous articles
		if not re.match(r'^\d\d\d\d$', self.article):
			if self.messages:
				print("closing article %s" % self.article)
			# remove files from previous article
			if os.path.isdir(self.temp_path):
				shutil.rmtree(self.temp_path)
			if os.path.isdir(self.output_path):
				shutil.rmtree(self.output_path)

		# make sure next article name is a gzip file
		self.article = next(self.article_names)
		if self.article and not self.article.endswith('.gz'):
			if self.messages:
				print("%s is not a gzip file" % self.article)
			return self.next_article()

		# open next article
		if self.article:
			if self.messages:
				print("decompressing article %s" % self.article)
			# uncompress gz file into temp folder
			self.block_reader.extract(self.article, path=self.temp_path)

			# unzip and read gz file
			gz_path = os.path.join(self.temp_path, self.article)
			with gzip.open(gz_path, 'rb') as gz:
				gz_bytes = gz.read()
				gz.close()

			# write bytes to new file
			tar_path = os.path.join(self.temp_path, self.article[:-3]) 
			with open(tar_path, 'wb') as tar:
				tar.write(gz_bytes)
				tar.close()

			if self.messages:
				print("untarring output of article %s" % self.article)

			# read new tar file, extract contents to output folder
			if tarfile.is_tarfile(tar_path):
				article_tar = tarfile.open(tar_path, 'r:')
				article_tar.extractall(path=self.output_path)
				return self.output_path
			else:
				if self.messages:
					print("%s does not decompress into a tar file" % self.article)
				return self.next_article()
				#raise IOError("%s does not decompress into a tar file" % self.article)
		else:
			return None

	# writes input to new tar file with same format
	def write(self, input_folder):
		if not os.path.isdir(input_folder):
			raise IOError("%s is not a folder" % input_folder)

		tar_path = os.path.join(self.temp_path, "%s.tar" % self.article[:-3])
		write_tar = tarfile.open(tar_path, 'w:')

		# add files in folder to tar
		for file_name in os.listdir(input_folder):
			write_tar.add(os.path.join(input_folder, file_name))

		write_tar.close()

		with open(tar_path, 'rb') as tar:
			tar_bytes = tar.read()
			tar.close()

		gz_bytes = gzip.compress(tar_bytes)

		gz_path = os.path.join(self.temp_path, 'out',self.article)
		with gzip.open(gz_path, 'wb') as gz:
			gz.write(gz_bytes)
			gz.close()

		# add gz file to overall tar file
		self.block_writer.add(os.path.join(self.temp_path, 'out'))

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
