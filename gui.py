#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
from PyQt5.QtWidgets import (QWidget, QPushButton, 
    QFrame, QApplication, QMainWindow, QDial, 
    QVBoxLayout, QHBoxLayout, QSlider, QLabel,
    QComboBox, QFileDialog, QCheckBox, QSpacerItem)
import PyQt5.QtGui

#TODO: create a construct for the row

#TODO: There needs to be some underlying structure the Gui to the audio logic...
#TODO: overtone slider
#TODO: add mute/solo

#default values
NUM_COL = 8
NUM_ROW = 13

class Gui(QMainWindow):
    
    def __init__(self):
        super().__init__()
        
        self.initGui()

    def initGui(self):

        wrapperWidget = QWidget()
        wrapperLayout = QVBoxLayout()
        wrapperLayout.setContentsMargins(0,0,0,0)
        wrapperLayout.setSpacing(0)
        self.statusBar = self.statusBar()
        self.grid = Grid(wrapperWidget)

        self.controlpanel = ControlPanel(wrapperWidget)


        wrapperLayout.addWidget(self.controlpanel)
        wrapperLayout.addWidget(self.grid)
        wrapperWidget.setLayout(wrapperLayout)

        self.setCentralWidget(wrapperWidget)
        self.show()

class PlayButton(QPushButton):
    def __init__(self,text):
        super().__init__(text)
        self.playing = False


#Control panel on top: [volume][tempo][play][pause]
class ControlPanel(QWidget):

    def __init__(self,parent):
        super().__init__(parent)
        self.initControlPanel()

    def initControlPanel(self):
        layout = QVBoxLayout()
        layout.setSpacing(0)

        selectAndPlayLayout = QHBoxLayout()

        self.playButton = PlayButton('Play')
        self.playButton.setMaximumWidth(60)
        self.playButton.setMaximumHeight(40)

        self.selectBox = QComboBox()
        self.selectBox.setMaximumWidth(200)
        self.selectBox.setCurrentText("Rhythm")
        self.selectBox.addItem("Rhythm")
        self.selectBox.addItem("Pythagorean")
        self.selectBox.addItem("Dodecaphonic")
        self.selectBox.addItem("Even Tempered")
        self.selectBox.addItem("Mean Tone")
        self.selectBox.addItem("Ptolemic")

        selectAndPlayLayout.addWidget(self.playButton)
        selectAndPlayLayout.addWidget(self.selectBox)


        sliderLayout = QHBoxLayout()

        volumeLayout = QVBoxLayout()
        volumeLabel = QLabel("Volume")
        self.volumeSlider = QSlider(1,None)
        self.volumeSlider.setMaximumWidth(200)
        self.volumeSlider.setRange(0,75)
        self.volumeSlider.setValue(75)
        volumeLayout.addWidget(self.volumeSlider)
        volumeLayout.addWidget(volumeLabel)

        tempoLayout = QVBoxLayout()
        tempoLayout.setSpacing(0)
        tempoLabel = QLabel("Tempo")
        self.tempoSlider = QSlider(1,None)
        self.tempoSlider.setMaximumWidth(200)
        self.tempoSlider.setRange(0,300) #Edit as neccessary... test ranger
        self.tempoSlider.setValue(125)       
        tempoLayout.addWidget(self.tempoSlider)
        tempoLayout.addWidget(tempoLabel)

        sliderLayout.addLayout(tempoLayout)
        sliderLayout.addLayout(volumeLayout)

        layout.addLayout(selectAndPlayLayout)
        layout.addLayout(sliderLayout)

        self.setLayout(layout)



class GridButton(QPushButton):
    def __init__(self, text, row, col):
        super().__init__(text)
        self.pressed = False
        self.row = row
        self.col = col

class GridFileButton(QPushButton):
    def __init__(self, row, text=""):
        super().__init__(text)
        self.row = row
        self.fileName = ""

    def setFile(self,_file):
        self.fileName = _file

class GridVolumeDial(QDial):
    def __init__(self, row):
        super().__init__()
        self.row = row

class GridCheckbox(QCheckBox):
    def __init__(self,col):
        super().__init__()
        self.col = col


class Grid(QWidget):

    def __init__(self,parent):
        super().__init__(parent)
        self.initUI()
        self.gridFiles = []


    def initUI(self):
        cwd = os.getcwd()
        sampledir = cwd+'/samples'
        fileNames = [_file for _file in os.listdir(sampledir) if _file.endswith(".wav")]
        #TODO: gotta name the grid buttons somehow

        gridLayout = QVBoxLayout()
        gridLayout.setContentsMargins(15,0,20,0)
        gridLayout.setSpacing(0)

        #stressWrapperLayout = QHBoxLayout()
        stressLayout = QHBoxLayout()
        #spacer = QSpacerItem(100,10)
        #stressWrapperLayout.addLayout(spacer)
        for i in range(8):
            checkbox = GridCheckbox(i)

            stressLayout.addWidget(checkbox)
        #stressWrapperLayout.addLayout(stressLayout)
        #gridLayout.addLayout(stressWrapperLayout)
        gridLayout.addLayout(stressLayout)

        for i in range(NUM_ROW):
            #Create Horizontal Layout: [file_input][QDial][M][S][_]*NUM_COL
            rowLayout = QHBoxLayout()

            volumeDial = GridVolumeDial(i)
            volumeDial.setMaximumHeight(40)
            volumeDial.setMaximumWidth(60)
            volumeDial.setNotchTarget(11.0)
            volumeDial.setWrapping(False)
            volumeDial.setNotchesVisible(True)
            volumeDial.setRange(0,100)
            volumeDial.setValue(75)
            fileSelect = GridFileButton(i)

            if (i < len(fileNames)):
                fileSelect.setText(fileNames[i].split(".")[0])
                fileSelect.setFile(cwd+'/samples/'+fileNames[i])
            else:
                fileSelect.setText("Select File")

            fileSelect.setMinimumHeight(20)
            fileSelect.setMaximumHeight(30)
            fileSelect.setMaximumWidth(130)
            fileSelect.setMinimumWidth(130)
            #Wire button press to showFile()
            fileSelect.clicked.connect(self.showFiles)            

            rowLayout.addWidget(volumeDial)
            rowLayout.addWidget(fileSelect)
            rowLayout.setSpacing(50)

            for j in range(NUM_COL):

                b = GridButton(' ', i, j)
                b.setMinimumHeight(20)
                b.setMaximumHeight(30)
                b.setMaximumWidth(40)
                b.setCheckable(True)

                rowLayout.addWidget(b)

            gridLayout.addLayout(rowLayout)

        self.setLayout(gridLayout)

        self.setGeometry(300, 0, 300, 150)
        self.setWindowTitle('sup')


    def showFiles(self):
        '''
        Presents users with files in current directory to use.
        If the user in scale mode (harmonic, pythag, etc.) just return.
        '''
        sender = self.sender()

        cwd = os.getcwd()
        fname = QFileDialog.getOpenFileName(self, 'Open audo file', cwd)

        localname = fname[0].split('/')[-1]
        #Check that file is supported format
        #if file.endswith(.wav)
        #else return

        if fname[0]:
            sender.setText(localname)
            sender.setFile(fname[0])
            return fname
                    
'''
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    gui = Gui()
    sys.exit(app.exec_())
'''


