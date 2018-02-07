import os
import os.path
import errno
import codecs
import pickle
import numpy as np
import keras


# Below code sample is taken from https://github.com/pytorch/vision/blob/master/torchvision/datasets/mnist.py
class MNIST(object):
	urls = [
        'http://yann.lecun.com/exdb/mnist/train-images-idx3-ubyte.gz',
        'http://yann.lecun.com/exdb/mnist/train-labels-idx1-ubyte.gz',
        'http://yann.lecun.com/exdb/mnist/t10k-images-idx3-ubyte.gz',
        'http://yann.lecun.com/exdb/mnist/t10k-labels-idx1-ubyte.gz',
    ]
	raw_folder = 'raw'
	processed_folder = 'processed'
	training_file = 'training.pt'
	test_file = 'test.pt'

	def __init__(self, root="./data"):
            self.root = root
            if not self._check_exists():
                self.download()

            self.train_data, self.train_labels = pickle.load( open(os.path.join(self.root, self.processed_folder, self.training_file), "rb"))
            self.test_data, self.test_labels = pickle.load( open(os.path.join(self.root, self.processed_folder, self.test_file), "rb"))

	def download(self):
		"""Download the MNIST data if it doesn't exist in processed_folder already."""
		import urllib.request
		import gzip

		if self._check_exists():
			return

		# download files
		try:
			os.makedirs(os.path.join(self.root, self.raw_folder))
			os.makedirs(os.path.join(self.root, self.processed_folder))
		except OSError as e:
			if e.errno == errno.EEXIST:
				pass
			else:
				raise

		for url in self.urls:
			print('Downloading ' + url)
			data = urllib.request.urlopen(url)
			filename = url.rpartition('/')[2]
			file_path = os.path.join(self.root, self.raw_folder, filename)
			with open(file_path, 'wb') as f:
				f.write(data.read())
			with open(file_path.replace('.gz', ''), 'wb') as out_f, \
				gzip.GzipFile(file_path) as zip_f:
				out_f.write(zip_f.read())

			os.unlink(file_path)

		# process and save as torch files
		print('Processing...')
		training_set = (
			read_image_file(os.path.join(self.root, self.raw_folder, 'train-images-idx3-ubyte')),
			keras.utils.to_categorical(read_label_file(os.path.join(self.root, self.raw_folder, 'train-labels-idx1-ubyte')), 10)
			)

		test_set = (
			read_image_file(os.path.join(self.root, self.raw_folder, 't10k-images-idx3-ubyte')),
			keras.utils.to_categorical(read_label_file(os.path.join(self.root, self.raw_folder, 't10k-labels-idx1-ubyte')), 10)
			)
		with open(os.path.join(self.root, self.processed_folder, self.training_file), 'wb') as f:
			pickle.dump(training_set, f)
		with open(os.path.join(self.root, self.processed_folder, self.test_file), 'wb') as f:
                        pickle.dump(test_set, f)
		print('Done!')
	def _check_exists(self):
		return os.path.exists(os.path.join(self.root, self.processed_folder, self.training_file)) and \
			os.path.exists(os.path.join(self.root, self.processed_folder, self.test_file))


def read_label_file(path):
    with open(path, 'rb') as f:
        data = f.read()
        assert get_int(data[:4]) == 2049
        length = get_int(data[4:8])
        parsed = np.frombuffer(data, dtype=np.uint8, offset=8)
        return parsed.reshape(length)


def read_image_file(path):
    with open(path, 'rb') as f:
        data = f.read()
        assert get_int(data[:4]) == 2051
        length = get_int(data[4:8])
        num_rows = get_int(data[8:12])
        num_cols = get_int(data[12:16])
        images = []
        parsed = np.frombuffer(data, dtype=np.uint8, offset=16)
        return parsed.reshape(length, num_rows * num_cols)


def get_int(b):
    return int(codecs.encode(b, 'hex'), 16)


def get_training_data(target):
	if target == "mnist":
		return MNIST().train_data

def get_training_target(target):
	if target == "mnist":
		return MNIST().train_labels

def get_validation_data(target):
	if target == "mnist":
		return MNIST().test_data

def get_validation_target(target):
	if target == "mnist":
		return MNIST().test_labels
