# from PyQt4.QtCore import *
# from PyQt4.QtGui import *
from scipy import interpolate
import abc
import pandas as pd
import numpy as np
from operator import *
import pyaudio
import math
import time
import sys


class Collection(metaclass=abc.ABCMeta):
	@abc.abstractmethod
	def get_frequency(self, inteval_number):
		return


class EvenTempered(Collection):
	'''
	Even Tempered series class.
	'''

	def __init__(self, base_frequency):
		self.scale = [base_frequency]
		self.name = "Even Tempered"
		for i in range(1, 13):
			self.scale.append(self.scale[i - 1] * pow(2, 1.0 / 12.0))

	def get_frequency(self, inteval_number):
		return self.scale[inteval_number - 1]


class Pythagorean(Collection):
	'''
	Pythagorean series class.
	'''
	def __init__(self, base_frequency):
		self.name = "Pythagorean"
		self.temp_scale = []
		self.scale = []
		self.temp_scale.append(base_frequency)
		for i in range(1, 6):
			self.temp_scale.append(self.temp_scale[i - 1] * 1.5)
			while self.temp_scale[i] > base_frequency * 2:
				self.temp_scale[i] /= 2
		self.temp_scale.append(base_frequency / 1.5 * 2)
		self.sort(7)
		self.scale.append(base_frequency * 2)

	def sort(self, degrees):
		j = 0
		for i in range(0, degrees):
			self.scale.append(0)
		for i in range(0, degrees):
			for k in range(0, degrees):
				if self.temp_scale[i] > self.temp_scale[k]:
					j += 1
			self.scale[j] = self.temp_scale[i]
			j = 0
		return

	def get_frequency(self, inteval_number):
		return self.scale[inteval_number - 1]


class Dodecaphonic(Pythagorean):
	'''
	Dodecaphonic series class
	'''
	COMMA = 81.0 / 80.0

	def __init__(self, base_frequency):
		super(Dodecaphonic, self).__init__(base_frequency)
		self.name = "Dodecaphonic"
		self.temp_scale.append(self.temp_scale[6])
		self.temp_scale[6] = self.temp_scale[5] * 0.75
		for i in range(8, 13):
			down_degree = i - 6
			self.temp_scale.append(self.temp_scale[i - 1] / 1.5)
			while self.temp_scale[i] < base_frequency:
				self.temp_scale[i] *= 2
		self.sort(13)


class Ptolemy(Dodecaphonic):

	def __init__(self, base_frequency):
		super(Ptolemy, self).__init__(base_frequency)
		self.name = "Ptolemy"
		self.scale[1] *= self.COMMA
		self.scale[3] *= self.COMMA
		self.scale[4] /= self.COMMA
		self.scale[9] *= self.COMMA
		self.scale[10] /= self.COMMA
		self.scale[12] /= self.COMMA
		del self.scale[6]
		self.scale[12] = base_frequency * 2
		self.scale[6] = 64.0 / 45.0 * base_frequency


class MeanTone(Dodecaphonic):

	def __init__(self, base_frequency):
		super(MeanTone, self).__init__(base_frequency)
		self.name = "Mean Tone"
		for i in range(1, 7):
			adjustment = pow(pow(self.COMMA, -1), (i / 4.0))
			self.temp_scale[i] *= adjustment
		for i in range(7, 13):
			adjustment = pow(self.COMMA, ((i - 6) / 4.0))
			self.temp_scale[i] *= adjustment
		self.sort(13)
'''
************************************
		Helper functions.
************************************
'''


def sine(frequency, length, rate):
	'''
	Generates a Numpy sine wave
	'''
	length = int(length * rate)
	interval = float(frequency) * (math.pi * 2) / rate
	return np.sin(np.arange(length) * interval)


def play_frequency(stream, frequency, amplitude=.5, length=1):
	'''
	Plays a specific frequency
	'''
	rate = 44100
	chunks = []
	chunks.append(sine(frequency, length, rate))
	chunk = np.concatenate(chunks) * amplitude
	stream.write(chunk.astype(np.float32).tostring())


def get_gcd(a, b):
	'''
	Returns greatest common denominator/devisor
	'''
	while b:
		a, b = b, a % b
	return a
