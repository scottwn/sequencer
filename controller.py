from gui import *
import sys
import wave
import time
import numpy
import scales
from scipy import interpolate
from operator import itemgetter

from PyQt5.QtWidgets import QApplication
import pyaudio

#TODO: stop on window close


NUM_COL = 8
NUM_ROW = 13


class App():
	def __init__(self,args):
		self.app = QApplication(args)
		self.gui = Gui()

		self.bpm = self.gui.controlpanel.tempoSlider.value()
		self.sleepTime = 60/float(self.bpm)
		self.max_frames = int((60/float(self.bpm))*15000)
		print(self.max_frames)


		# global event handlers
		self.gui.controlpanel.tempoSlider.valueChanged.connect(self.updateTempo)
		self.gui.controlpanel.volumeSlider.valueChanged.connect(self.updateGlobalVolume)
		self.gui.controlpanel.selectBox.currentIndexChanged.connect(self.updateMode)


		et = scales.EvenTempered(528)
		pythag = scales.Pythagorean(528)
		dodec = scales.Dodecaphonic(528)
		ptolemy = scales.Ptolemy(528)
		mt = scales.MeanTone(528)
		allScales = [pythag,dodec,et,mt,ptolemy]

		self.grid = []
		for i in range(13):
			rowObj = Row(i)
			for scale in allScales:
				if (i < len(scale.scale)):
					#rowObj.scaleData.append(self.pluck(scale.get_frequency(i+1)))
					pluckData = self.pluck(scale.get_frequency(i+1))
					rowObj.scaleDataUnchanged.append(pluckData)
					rowObj.scaleData.append(pluckData)
					#rowObj.scaleData.append(numpy.multiply(pluckData,0.75))
				else:
					rowObj.scaleData.append(numpy.zeros(1))
					rowObj.scaleDataUnchanged.append(numpy.zeros(1))

			self.grid.append(rowObj)

		self.mode = self.gui.controlpanel.selectBox.currentIndex()

		self.curColumn = 0
		self.playButton = self.gui.controlpanel.playButton
		
		self.playButton.clicked.connect(self.play)

		self.volume = 100
		self.globalVolumeFactor = 1.0

		self.playing = False

		print("MAX FRAMES: " + str(self.max_frames))
	
		cwd = os.getcwd()
		sampleDir = cwd+'/samples/'
		for child in self.gui.grid.children():
			if (isinstance(child,GridFileButton)):
				if (child.fileName!=""):
					waveObj = waveFile(child.fileName)
					#print(len(waveObj.intData))
					if (len(waveObj.intData)>self.max_frames):
						print("OVER: " + str(len(waveObj.intData)))
						waveObj.intData = self.truncate(waveObj)
					else:
						waveObj.intData = self.addZeros(waveObj)

			
					self.grid[child.row].fileObj = waveObj
			if (isinstance(child,GridButton)):
				child.clicked.connect(self.updateGrid)
			if (isinstance(child,GridVolumeDial)):
				child.valueChanged.connect(self.updateRowVolume)
			if (isinstance(child,GridCheckbox)):
				child.clicked.connect(self.updateStresses)

	def makehit(self, hit_data):
		'''
		Returns numpy array of compiled hits
		'''
		if (len(hit_data)==0):
			return ""
		#decoded_data = [numpy.fromstring(data, numpy.int32) for data in hit_data]
		_max = max([len(d) for d in hit_data])
		mixed = numpy.zeros(_max, dtype=numpy.int32)
		denom = len(hit_data)
		for _data in hit_data:
			mixed[:len(_data)] += ((_data/denom).astype(numpy.int32))

		return mixed.tostring()

	def shape(self, data, points, kind='slinear'):
		items = points.items()
		items.sort(key=itemgetter(0))
		keys = map(itemgetter(0), items)
		vals = map(itemgetter(1), items)
		interp = interpolate.interp1d(keys, vals, kind=kind)
		factor = 1.0 / len(data)
		shape = interp(np.arange(len(data)) * factor)
		return data * shape

	def truncate(self,waveObj):
		return waveObj.intData[:int(self.max_frames)]
		#TODO: shape the tail
		#chunk = numpy.fromstring(waveObj.data, numpy.int32)
		#return self.shape(_data, {0.0: 0.0, 0.005: 1.0, 0.25: 0.5, 0.9: 0.1, 1.0:0.0})
		#waveObj.data = shaped.tostring()

	def shape(self, data, points, kind='slinear'):
		items = list(points.items())
		items.sort(key=itemgetter(0))
		keys = list(map(itemgetter(0), items))
		vals = list(map(itemgetter(1), items))
		interp = interpolate.interp1d(keys, vals, kind=kind)
		factor = 1.0 / len(data)
		shape = interp(numpy.arange(len(data)) * factor)
		return data * shape

	def harmonics(self,freq,length):
		#make sure it takes in self.max_frames
		a = scales.sine(freq*1.00, (self.max_frames/44100), 44100)
		b = scales.sine(freq*2.00, (self.max_frames/44100), 44100)
		return (a+b)*.2

	def pluck(self,freq):
		chunk = self.harmonics(freq, 1)
		return self.shape(chunk, {0.0:0.0,0.005:1.0,0.25:0.5,0.9:0.0,1.1:0.0})

	def chord(self,freqs):
		thechord = sum([pluck(freq) for freq in freqs])
		return thechord

	def addZeros(self,waveObj):
		'''
		add (max_frames - len(waveObj.intData)) zeros to end
		'''
		diff = self.max_frames - (len(waveObj.intData))
		arr = numpy.zeros(diff)
		return numpy.append(waveObj.intData,arr)


	def play(self):
		#TODO: change stream based on scale or wav files 

		p = pyaudio.PyAudio()
		if (self.mode==0):
			stream = p.open(format=pyaudio.paInt32, 
								channels=1, 
								rate=44100, 
								output=True)
		else:
			stream = p.open(format=pyaudio.paFloat32, 
								channels=1, 
								rate=44100, 
								output=True)

		if (self.playButton.playing):
			print("Play->Pause")
			self.gui.controlpanel.playButton.setText("Play")
		else:
			print("Pause->Play")
			self.gui.controlpanel.playButton.setText("Pause")
		self.playButton.playing = not self.playButton.playing

		if (self.mode=="rhythm"):		
			self.updateFiles()

		while (self.playButton.playing):
			self.updateGrid() # gets state of button in gui and updates controller array
			if (self.mode==0):
				hitData = []
				for row in self.grid:
					self.app.processEvents() #THIS IS SUPER IMPORTANT! else use threading:/
					pressed = row.array[self.curColumn]
					if (pressed and (row.fileObj)):
						_data = numpy.multiply(row.fileObj.intData,row.stressFactors[self.curColumn])
						hitData.append(_data)
				compiledHit = self.makehit(hitData)
				stream.write(compiledHit)	
			else:
				freqs = []
				for row in self.grid:
					self.app.processEvents()
					pressed = row.array[self.curColumn]
					if (pressed and (len(row.scaleData[self.mode-1])>1)):
						freqs.append(row.scaleData[self.mode-1])
				if (len(freqs)>0):
					playData = sum([freqData for freqData in freqs])
					_data = numpy.multiply(playData,row.stressFactors[self.curColumn])
					stream.write(_data.astype(numpy.float32).tostring())

			#snchanged to update colors
			for child in self.gui.grid.children():
				if(isinstance(child, GridButton)):
					if child.col == self.curColumn:
						print(child.row, child.col, "green")
						child.setStyleSheet("background-color: green")
					else:
						child.setStyleSheet("background-color: gray")

			print("process")
		
			self.curColumn+=1
			self.curColumn%=8


			for i in range(1000):
				self.app.processEvents() #THIS IS SUPER IMPORTANT! else use threading:/
				time.sleep(self.sleepTime/float(1000))
		
		stream.stop_stream()
		stream.close()
		p.terminate()


	### EVENT HANDLERS ###
	def updateGrid(self):
		button = self.app.sender()

		if (not isinstance(button,PlayButton)):
			button.pressed = not button.pressed
			if (button.pressed):
				self.grid[button.row].array[button.col] = True
			else:
				self.grid[button.row].array[button.col] = False
			print(str(button.row)+', '+str(button.col))

	def updateFiles(self):
		'''
		Update the underlying wave data when new file is selected
		'''
		for child in self.gui.grid.children():
			if (isinstance(child,GridFileButton)):
				if (child.fileName!=""):
					if (child.fileName != self.grid[child.row].fileObj.fileName):
						print("FILE CHANGED: "+child.fileName)
						# Update the underlying file
						waveObj = waveFile(child.fileName)
						#print(len(waveObj.intData))
						if (len(waveObj.intData)>self.max_frames):
							waveObj.intData = self.truncate(waveObj)
						else:
							waveObj.intData = self.addZeros(waveObj)

						#print(len(waveObj.intData))
						self.grid[child.row].fileObj = waveObj

	def updateMode(self):
		'''
		Changes row data based on change in mode
		'''
		sender = self.app.sender()
		print("now "+str(sender.currentIndex())+ " "+sender.currentText())
		self.mode= sender.currentIndex()

		for child in self.gui.grid.children():
			if (isinstance(child,GridFileButton)):
				if (self.mode == 0):
					if (child.fileName!=""):
						child.setText(child.fileName.split("/")[-1].split(".")[0])
					else:
						child.setText("Select File")
				#snchanged to put interval names in boxes instead of numers
				elif self.mode == 1:
					if child.row > 7:
						child.setText("")
					else:
						child.setText(str(child.row + 1))
				elif (self.mode == 2) | (self.mode == 4):
					child.setText(self.interval_name_dodecaphonic(child.row))
				else:
					child.setText(self.interval_name(child.row))



	def updateTempo(self):
		slider = self.app.sender()
		self.bpm = slider.value() * 3 #snchanged to make it play faster
		self.sleepTime = 60/float(self.bpm)

		return

	def updateStresses(self):
		checkbox = self.app.sender()
		for rowObj in self.grid:
			rowObj.stressFactors[checkbox.col] = 1.0

			

		print("Checkbox col: "+str(checkbox.col))

	def updateGlobalVolume(self):
		slider = self.app.sender()
		factor = (slider.value()/100.0)
		print(factor)
		self.globalVolumeFactor = factor
		for rowObj in self.grid:
			rowVolumeFactor = factor*rowObj.volumeFactor
			if (rowObj.fileObj):
				rowObj.fileObj.intData = numpy.multiply(rowObj.fileObj.intDataUnchanged,rowVolumeFactor)
				lenDiff = self.max_frames-len(rowObj.fileObj.intData)
				if (lenDiff>0):
					rowObj.fileObj.intData = numpy.append(rowObj.fileObj.intData,numpy.zeros(lenDiff))

			for i in range(len(rowObj.scaleData)):
				rowObj.scaleData[i] = numpy.multiply(rowObj.scaleDataUnchanged[i],rowVolumeFactor)
				lenDiff = self.max_frames - len(rowObj.scaleData[i])
				if (lenDiff > 0):
					rowObj.scaleData[i] = numpy.append(rowObj.scaleData[i],numpy.zeros(lenDiff))



	def updateRowVolume(self):
		slider = self.app.sender()
		rowObj = self.grid[slider.row]
		factor = slider.value()/100.0
		print("Local factor: " + str(factor))
		print("Global factor: " + str(self.globalVolumeFactor))
		rowObj.volumeFactor = factor
		effectiveFactor = rowObj.volumeFactor*self.globalVolumeFactor
		print("effectiveFactor: " + str(effectiveFactor))
		rowObj.fileObj.intData = numpy.multiply(rowObj.fileObj.intDataUnchanged,effectiveFactor)
		lenDiff = self.max_frames-len(rowObj.fileObj.intData)
		print(lenDiff)
		if (lenDiff>0):
			rowObj.fileObj.intData = numpy.append(rowObj.fileObj.intData,numpy.zeros(lenDiff))

		for i in range(len(rowObj.scaleData)):
			rowObj.scaleData[i] = numpy.multiply(rowObj.scaleDataUnchanged[i],effectiveFactor)
			lenDiff = self.max_frames - len(rowObj.scaleData[i])
			if (lenDiff > 0):
				rowObj.scaleData[i] = numpy.append(rowObj.scaleData[i],numpy.zeros(lenDiff))

	#snchanged to put interval names in boxes instead of numbers
	def interval_name(self, row_number):
		return {
			0: "1",
			1: "m2",
			2: "M2",
			3: "m3",
			4: "M3",
			5: "4",
			6: "b5",
			7: "5",
			8: "m6",
			9: "M6",
			10: "m7",
			11: "M7",
			12: "Octave",
		}[row_number]

	def interval_name_dodecaphonic(self, row_number):
		return {
			0: "1",
			1: "m2",
			2: "M2",
			3: "m3",
			4: "M3",
			5: "4",
			6: "b5-",
			7: "b5+",
			8: "5",
			9: "m6",
			10: "M6",
			11: "m7",
			12: "M7"
		}[row_number]


class waveFile(object):
	'''
	class for wave file...
	'''

	CHUNK = 1024
	def __init__(self,file_name):

		try:
			fileObj = wave.open(file_name, 'rb')
		except wave.Error as e:
			print("WAVE read error ({0}): {1}".format(e.errno, e.strerror))
			exit(0) #HANDLE THIS BETTER

		if (fileObj.getsampwidth()!=2):
			print(file_name + " not compatible :/")
			exit(0)


		'''
		allData = b''
		data = fileObj.readframes(waveFile.CHUNK)
		while (data != b''):
			allData+=str(data)
			data = fileObj.readframes(waveFile.CHUNK)

		'''
		self.fileName = file_name
		self.data = fileObj.readframes(fileObj.getnframes())
		self.intDataUnchanged = numpy.fromstring(self.data, dtype=numpy.int32)
		self.intData = numpy.fromstring(self.data, dtype=numpy.int32)
		self.file_name = file_name
		self.obj = fileObj
		self.duration = fileObj.getnframes()/float(fileObj.getframerate())


class Row():
	def __init__(self,i):
		self.fileObj = None
		self.interval = i
		self.scaleData = [] # Pythag, Dodec, ET, MT, Pt
		self.scaleDataUnchanged = []
		self.array = [False]*8 #Just a boolean array
		self.volume = 100
		self.volumeFactor = 1.0
		self.stressFactors = [.5]*8

class RhythmRow(Row):
	def __init__(self, i):
		#self.array = [GridButton() for i in range(8)]
		super().__init__()
		self.fileObj = None
		self.id = i
		

class ScaleRow(Row):
	def __init__(self, freq, i):
		self.frequency = freq
		self.id = i


if __name__ == '__main__':
	myApp = App(sys.argv)
	sys.exit(myApp.app.exec_())


