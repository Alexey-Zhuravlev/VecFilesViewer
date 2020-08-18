#!python3
'''
Vector File Viewer
November 2015
Created to read and visualize vector files created by Rize3D software for use with the Alpha and Beta printers.
Written by John Fodero for Rize3D
'''


from tkinter import *
import getpass
from tkinter import filedialog
from tkinter import messagebox
import os
import struct
import math

colorCodeDict = {
	'Travel' : 'Blue',
	'Perimeter' : 'DarkGreen',
	'Core' : 'Gold',
	'Build Plate' : 'LightSkyBlue',
	'Below Release' : 'Purple',
	'Above Release' : 'LightSalmon',
	'Above Release Perimeter': 'DarkRed',
	'Above Release Small' : 'Black',
	'setTravel' : 'Orange',
	'Above Release Curve' : 'Salmon',
	'Above Release Curve Perimeter' : 'Red',
	'Small Perimeter' : 'Red',
	'Inner Hole Perimeter' : 'Red',
	'Inner Hole Perimeter Above Release' : 'Red',
	'First Solid Perimeter' : 'Red',
	'First Solid Perimeter Above Release' : 'Red',
	'Gap Fill' : 'DarkViolet',
	'Gap Fill 25' : 'DarkViolet',
	'Gap Fill 50' : 'DarkViolet',
	'Gap Fill 75' : 'DarkViolet',
	'Gap Fill 125' : 'DarkViolet',
	'Gap Fill 150' : 'DarkViolet',
	'Gap Fill 175' : 'DarkViolet',
	'Gap Fill 200' : 'DarkViolet', 
	'Part Dense Fill' : 'RoyalBlue',
	'Part Perimeters Fill' : 'RoyalBlue',
	'Part Sparse Fill' : 'Brown',
	'Support Dense Fill' : 'DarkViolet',
	'Support Perimeters Fill' : 'MediumPurple',
	'Support Sparse Fill' : 'DarkGreen',
	'Raft' : 'DarkRed',
	'Witness Perimeters' : 'Maroon',
	'Witness Fill' : 'Brown',
	}

opCodeDict = { 
	0 : 'NOP',
	1 : 'setPosition',
	2 : 'setTrajectory',
	3 : 'setTravel',
	4 : 'MAX'
	}
  
motorDict = { 
	0 : 'X axis',
	1 : 'Y axis',
	2 : 'extruder',
	3 : 'Z axis',
	4 : 'service station',
	5 : 'filament select',
	6 : 'filament drive',
	7 : 'MAX'
	}


lineTypeDict = { 
	0 : 'Travel',
	1 : 'Perimeter',
	2 : 'Core',
	3 : 'Build Plate',
	4 : 'Below Release',
	5 : 'Above Release',
	6 : 'Above Release Perimeter',
	7 : 'Above Release Small',
	8 : 'Above Release Curve',
	9 : 'Above Release Curve Perimeter',
	10 : 'Small Perimeter',
	11 : 'Inner Hole Perimeter',
	12 : 'Inner Hole Perimeter Above Release',
	13 : 'First Solid Perimeter',
	14 : 'First Solid Perimeter Above Release',
	15 : 'Gap Fill',
	16 : 'Gap Fill 25',
	17 : 'Gap Fill 50',
	18 : 'Gap Fill 75',
	19 : 'Gap Fill 125',
	20 : 'Gap Fill 150',
	21 : 'Gap Fill 175',
	22 : 'Gap Fill 200',
	23 : 'Part Dense Fill',
	24 : 'Part Perimeters Fill',
	25 : 'Part Sparse Fill',
	26 : 'Support Dense Fill',
	27 : 'Support Perimeters Fill',
	28 : 'Support Sparse Fill',
	29 : 'Raft',
	30 : 'Witness Perimeters',
	31 : 'Witness Fill',
	
	32 : 'MAX'
	}


WIDTH=1244
HEIGHT=800


class Layer:
	def __init__(self, layerNum):
		self.layerNumber = layerNum
		self.layerPosition = 0
		self.zHeight = ''
		self.xMoves = []
		self.yMoves = []
		self.stopV = []
		self.maxV = []
		self.density = []
		self.lineTypes = []
		self.supportFlags = []
class App:
	#width = 912.6
	#height = 586.6

	#width = 1368.9
	#height = 879.9

	width = WIDTH
	height = HEIGHT
	
	fileOpened = False
	showTextWindow = False
	# define the default layer height of 0.25mm
	layerThickness = 0.25
	def __init__(self, master):
	
		inFile = None
		prevX = None
		prevY = None
		currentX = None
		currentY = None
		startPos = None
		endPos = None
		layers = None
		fileSize = None
		layerSelect = None
		colors = None
		arrowSelect = None
		showMaxV = None
		showTextWindow = False
		
		xStart = 0
		yStart = 0
		xOffset = 0
		yOffset = 0
		zoomScale = 0
		
		# define the default layer height of 0.25mm
		layerThickness = 0.25

		
		frame = Frame(master, relief = RIDGE, borderwidth = 5, padx = 5, pady = 5)
		frame.bind_all("<Up>", self.next_layer_event)
		frame.bind_all("<Down>", self.previous_layer_event)
		frame.bind_all("<Right>", self.next_sequence_event)
		frame.bind_all("<Left>", self.previous_sequence_event)
		frame.bind_all("<v>", self.reset_view)
		frame.bind_all("<c>", self.colors_toggle)
		frame.bind_all("<r>", self.arrows_toggle)
		frame.bind_all("<a>", self.maxv_toggle)
		frame.bind_all("<s>", self.stopV_toggle)
		frame.bind_all("<d>", self.density_toggle)
		frame.bind_all("<o>", self.open_files_to_default)
		frame.bind_all("<z>", self.open_files_to_AppData)
		frame.bind_all("<t>", self.textWindow_toggle)
		frame.grid(sticky=N+S+E+W)      
		
		self.menubar = Menu(root, tearoff = 0)
		root.configure(menu=self.menubar)
		self.optionsMenu = Menu(self.menubar, tearoff = 0)
		
		self.menubar.add_command(label="Open (o)", command=self.open_files_to_default)
		self.menubar.add_command(label="Open from AppData (z)", command=self.open_files_to_AppData)
		self.optionsMenu.add_command(label="Reset View (v)", command=self.reset_view)
		self.optionsMenu.add_command(label="Text Viewer (t)", command=self.textWindow_toggle)
		self.optionsMenu.add_command(label="Show/Hide Colors (c)", command=self.colors_toggle)
		self.optionsMenu.add_command(label="Show/Hide Arrows (r)", command=self.arrows_toggle)
		self.optionsMenu.add_command(label="Show/Hide MaxV (a)", command=self.maxv_toggle)
		self.optionsMenu.add_command(label="Show/Hide StopVel (s)", command=self.stopV_toggle)
		self.optionsMenu.add_command(label="Show/Hide Density (d)", command=self.density_toggle)
		self.menubar.add_cascade(label="View", menu=self.optionsMenu)
		
# Row 0 ------------------------------------------------------------------------------

# Row 1 ------------------------------------------------------------------------------          
		
# Row 2 ------------------------------------------------------------------------------          
		self.layerScale = Scale(frame, from_=1, to=100, orient=HORIZONTAL, label='Layer Select (Up/Down)', resolution=1, length=self.width, command=self.layer_event, showvalue = 0)
		self.layerScale.grid(column = 0, columnspan = 1, row = 0, sticky=N+S+E+W)
# Row 3 ------------------------------------------------------------------------------          
		self.actionScale = Scale(frame, from_=0, to=100, orient=HORIZONTAL, label='Action Select (Left/Right)', resolution=1, length=self.width, command=self.action_event)
		self.actionScale.grid(column = 0, columnspan = 1, row = 1, sticky=N+S+E+W)
# Row 4 ------------------------------------------------------------------------------          
		self.lineCanvas = Canvas(frame, width=self.width, height=self.height, highlightbackground = 'Blue')
		self.lineCanvas.bind("<Button-1>", self.press)
		self.lineCanvas.bind("<B1-Motion>", self.mouse_motion)
		self.lineCanvas.bind("<MouseWheel>", self.zoom)
		self.lineCanvas.bind("<Button-3>", self.debug)
		self.lineCanvas.grid(column = 0, row = 2)

# Row/Column Configs            
		frame.grid_columnconfigure(0, weight=1) 
		frame.grid_columnconfigure(1, weight=1) 
		frame.grid_columnconfigure(2, weight=1) 
		frame.grid_columnconfigure(3, weight=1) 
		frame.grid_columnconfigure(4, weight=1)         

		frame.grid_rowconfigure(0, weight=1)
		frame.grid_rowconfigure(1, weight=1)
		frame.grid_rowconfigure(2, weight=1)
	# EVENT DRIVEN FUNCTIONS        
	def press(self, event):
		if self.fileOpened == True:
			self.xStart = event.x
			self.yStart = event.y
		return
	def mouse_motion(self, event):
		if self.fileOpened == True:
			self.xOffset += event.x - self.xStart
			self.yOffset -= event.y - self.yStart
			self.draw_moves()
			self.xStart = event.x
			self.yStart = event.y
		return
	def zoom(self, event):
		if self.fileOpened == True:
			lastZoom = self.zoomScale
			if event.delta > 0:
				self.zoomScale *= 2
			elif event.delta < 0:
				self.zoomScale /= 2
			if self.zoomScale < self.height/(HEIGHT/2):
				self.zoomScale = self.height/(HEIGHT/2)
				self.xOffset = 0
				self.yOffset = 0
			self.xOffset *= (self.zoomScale/lastZoom)
			self.yOffset *= (self.zoomScale/lastZoom)
			self.draw_moves()
		return
	def debug(self, event):
		print(str(event.x) + ' ' + str(event.y))
		return
	def action_event(self, event):
		if self.fileOpened == True:
			self.endPos = self.actionScale.get()
			self.draw_moves()
		return
	def layer_event(self, event):
		if self.fileOpened == True:
			self.layerSelect = self.layerScale.get()
			self.actionScale.config(to=len(self.layers[self.layerSelect].lineTypes))
			self.actionScale.set(len(self.layers[self.layerSelect].xMoves))
			self.draw_moves()

		return  
	def next_layer_event(self, event):
		self.layerScale.set(self.layerScale.get()+1)
		return
	def previous_layer_event(self, event):
		self.layerScale.set(self.layerScale.get()-1)
		return
	def next_sequence_event(self, event):
		self.actionScale.set(self.actionScale.get()+1)
		return
	def previous_sequence_event(self, event):
		self.actionScale.set(self.actionScale.get()-1)
		return
	# UTILITIES
	def enable_buttons(self):
		self.menubar.entryconfig("View", state = NORMAL)
		self.layerScale.config(state = NORMAL)
		self.actionScale.config(state = NORMAL)
		self.lineCanvas.config(state = NORMAL)
		self.layerScale.config(to=len(self.layers)-1)
		self.actionScale.config(to=len(self.layers[self.layerSelect].lineTypes))
		return
	def disable_buttons(self):
		self.menubar.entryconfig("View", state = DISABLED)
		self.layerScale.config(state = DISABLED)
		self.actionScale.config(state = DISABLED)
		self.lineCanvas.config(state = DISABLED)
		return
	def initialize_vars(self):
		self.prevX = 0
		self.prevY = 0
		self.currentX = 0
		self.currentY = 0
		self.startPos = 0
		self.endPos = 0
		self.layerSelect = 0
		
		self.xStart = 0
		self.yStart = 0
		self.zoomScale = self.height / (HEIGHT/2)
		self.xOffset = 0
		self.yOffset = 0
		
		self.colors = False
		self.fileOpened = True
		self.arrowSelect = NONE
		self.showMaxV = False
		self.showStopV = False
		self.showDensity = False
		return
	def read_file_until(self, endChar):
		# endChar: the character to read up to
		# returns a string containing all data up to (but not containing) endChar
		# returns an empty string if nothing is found in the file
		# the cursor will be immediately following endChar once the function has completed its search
		inChar = ''
		inStr = ''
		for i in range(self.inFile.tell(),self.fileSize):
			inChar = self.inFile.read(1)
			if inChar != endChar:
				inStr += inChar
			else:
				break   
		return inStr                    
	def open_files(self):
		root.withdraw()
		
		self.create_output()
		self.inFile = open('output.txt', 'r')
		# get file size
		data = self.inFile.read()
		self.fileSize = self.inFile.tell()
		self.inFile.seek(0,0)
		print('File Size: ' + str(self.fileSize))
		
		# re-initialize global variables
		self.initialize_vars()
		print('Reading File..')
		
		self.create_layers()
		self.get_line_data()
		self.inFile.close()
		root.deiconify()

		print('Reading Complete.')
		#os.remove('output.txt')
		
		self.enable_buttons()
		self.actionScale.set(len(self.layers[0].xMoves))
		return  
	def write_layer_to_terminal(self):
		if self.showTextWindow == True:
			self.text_window.config(state=NORMAL)
			self.text_window.delete(1.0, END)
			
			for i in range(0,len(self.layers[self.layerSelect].xMoves)+1):
				# designate the highlight tag
				self.text_window.tag_config("selected_layer", background = "yellow")                    
			
				if i == self.endPos:
					self.text_window.tag_add("selected_layer", str(int(self.text_window.index(END)[:self.text_window.index(END).index(".")])-2) + ".0", str(int(self.text_window.index(END)[:self.text_window.index(END).index(".")])-1) + ".0")
					self.text_window.see(self.text_window.index(END))
				if i < len(self.layers[self.layerSelect].xMoves):
					self.text_window.insert(END, str(self.layers[self.layerSelect].lineTypes[i]) + ' ' + 
						str(self.layers[self.layerSelect].xMoves[i]) + ' ' + 
						str(self.layers[self.layerSelect].yMoves[i]) + ' ' + 
						str(self.layers[self.layerSelect].stopV[i]) + ' ' + 
						str(self.layers[self.layerSelect].maxV[i]) + ' ' +
						str(self.layers[self.layerSelect].density[i]) + '\n')
			self.text_window.config(state=DISABLED)
		return
	# CONVERSION TOOLS
	def create_layers(self):
		# creates each layer and assigns a layer number and zHeight
		# this creates two layers 
		self.inFile.seek(0,0)
		
		self.layers = []
		self.layers.append(Layer(0))
		layerNum = 0
		data = None
		joinNextLayer = False
		prevHeight = 0
		height = 0
		
		while data != '':
			# 'data' will read as '' when self.read_file_until reaches the end of the file
			data = self.read_file_until('Z')
			if self.inFile.tell() == self.fileSize:
				# escape the loop
				data = ''
			else:
				# if a new z move is detected
				# back up the cursor to read the data size
				self.inFile.seek(self.inFile.tell()-10, 0)
				nullData = self.read_file_until(':')
				moveData = int(self.read_file_until(':'))
				for i in range(0, int(moveData/2)):
					nullData = self.read_file_until(':')
					data = self.read_file_until(',')
				
				nullData = self.read_file_until(';')
				nullData = self.inFile.read(1)
				height = float(data)
				
				# if height - prevHeight == self.layerThickness/2:
				#       joinNextLayer = not joinNextLayer
				# else:
				#       joinNextLayer = False
				
				if joinNextLayer == True:
					self.layers[layerNum].zHeight += ' + ' + str(data)
					print('Layer: ' + str(self.layers[layerNum].layerNumber) + ' @ ' + str(self.layers[layerNum].zHeight) + ' Pos: ' + str(self.layers[layerNum].layerPosition))
				else:
					layerNum += 1                           
					self.layers.append(Layer(layerNum))                             
					self.layers[layerNum].zHeight = str(data)
					self.layers[layerNum].layerPosition = self.inFile.tell()
					print('Layer: ' + str(self.layers[layerNum].layerNumber) + ' @ ' + str(self.layers[layerNum].zHeight) + ' Pos: ' + str(self.layers[layerNum].layerPosition))
					
				prevHeight = height
		print('Created layers successfully')
		return
	def get_line_data(self):
		print('Reading line data')
		self.inFile.seek(0,0)
		# loop for each layer
		for i in range(1,len(self.layers)):
			print('Layer ' + str(i), end='\r')
			#print('Layer ' + str(i))
			self.inFile.seek(self.layers[i].layerPosition, 0)

			# loop to read commands
			data = self.read_file_until(':')
			
			# establish the end of each layer
			if i == len(self.layers)-1:
				end = self.fileSize
			else:
				end = self.layers[i+1].layerPosition
				
			while self.inFile.tell() < end:
			
				if data == 'setPosition':
					# ignore this move
					nullData = self.read_file_until(';')
					nullData = self.inFile.read(1)
					
				elif data == 'setTrajectory':
					size = float(self.read_file_until(':'))
					size /= 3
					for dataCounter in range(0,int(size)):
						self.layers[i].xMoves.append(float(self.read_file_until(',')))
						self.layers[i].yMoves.append(float(self.read_file_until(',')))
						self.layers[i].lineTypes.append(self.read_file_until(','))
						self.layers[i].supportFlags.append(self.read_file_until(','))
						self.layers[i].stopV.append(float(self.read_file_until(',')))
						self.layers[i].maxV.append(float(self.read_file_until(',')))
						self.layers[i].density.append(float(self.read_file_until(',')))
					nullData = self.read_file_until(';')
					nullData = self.inFile.read(1)
				elif data == 'setTravel':
					size = float(self.read_file_until(':'))
					size /= 2
					for dataCounter in range(0,int(size)):
						self.layers[i].xMoves.append(float(self.read_file_until(',')))
						self.layers[i].yMoves.append(float(self.read_file_until(',')))
						self.layers[i].lineTypes.append('setTravel')
						self.layers[i].supportFlags.append('travel')
						self.layers[i].stopV.append(0)
						self.layers[i].maxV.append(255)
						self.layers[i].density.append(1)
					nullData = self.read_file_until(';')
					nullData = self.inFile.read(1)
				else:
					print('Unrecognized line type:' + str(data))
				
				data = self.read_file_until(':')
			# print(self.layers[i].xMoves)
			# print(self.layers[i].yMoves)
			# print(self.layers[i].lineTypes)
			# print(self.layers[i].stopV)
			# print(self.layers[i].maxV)
			# print(self.layers[i].density)
			# input()
		return
	def draw_moves(self):
		self.lineCanvas.delete(ALL)
		
		layer = self.layerSelect
		start = 0
		end = self.endPos
		zoomScale = self.zoomScale
		xOffset = (-1*(self.zoomScale - (self.height/(HEIGHT/2)))*(self.width/4)) + self.xOffset
		yOffset = (-1*(self.zoomScale - (self.height/(HEIGHT/2)))*(self.height/4)) + self.yOffset
	
		if self.colors == True:
			self.list_colors()
		if start == 0 and layer == 1:
			startPosX = 0
			startPosY = 0
		elif start == 0:
			startPosX = self.layers[layer-1].xMoves[len(self.layers[layer-1].xMoves)-1]
			startPosY = self.layers[layer-1].yMoves[len(self.layers[layer-1].yMoves)-1]
		else:
			startPosX = self.layers[layer].xMoves[start-1]
			startPosY = self.layers[layer].xMoves[start-1]
		if end > len(self.layers[layer].lineTypes):
			end = len(self.layers[layer].lineTypes)
		if end < start:
			end = start
		# draw z height and layer number
		self.lineCanvas.create_text(150,60, text='Z Height: ' + str(self.layers[layer].zHeight), fill='Black', font=('TkDefaultFont',14, 'bold'))
		self.lineCanvas.create_text(150,80, text='Layer Number: ' + str(self.layers[layer].layerNumber), fill='Black', font=('TkDefaultFont',14,'bold'))
		# draw grid
		for i in range(0,int(self.width),10):
			self.lineCanvas.create_line((i*zoomScale), 0, (i*zoomScale), self.height, fill = 'gray')
		for j in range(0,int(self.height),10):
			self.lineCanvas.create_line(0, (j*zoomScale), self.width, (j*zoomScale), fill = 'gray')

		# draw cross hairs
		self.lineCanvas.create_line(self.width/2, 0, self.width/2, self.height, fill = 'red', dash  = 1)
		self.lineCanvas.create_line(0, self.height/2, self.width, self.height/2, fill = 'red', dash = 2)
		# draw given range of layer
		for i in range(start,end):
			endPosX = self.layers[layer].xMoves[i]
			endPosY = self.layers[layer].yMoves[i]
			XStartScreen = (startPosX*zoomScale) + xOffset;
			XEndScreen   = (endPosX*zoomScale) + xOffset;
			YStartScreen = self.height - ((startPosY*zoomScale) + yOffset);
			YEndScreen   = self.height - ((endPosY*zoomScale) + yOffset);
			if self.showMaxV == True:
				self.lineCanvas.create_text(XStartScreen + (XEndScreen - XStartScreen) / 2, YStartScreen + (YEndScreen - YStartScreen) / 2 + 10, text = int(self.layers[layer].maxV[i]), fill='Black', font=('TkDefaultFont',10, 'bold'))
			if self.showDensity == True:
				self.lineCanvas.create_text(XStartScreen + (XEndScreen - XStartScreen) / 2, YStartScreen + (YEndScreen - YStartScreen) / 2 - 10, text = float(self.layers[layer].density[i]), fill='Grey', font=('TkDefaultFont',10, 'bold'))
			if self.showStopV == True:
				self.lineCanvas.create_text(XEndScreen, YEndScreen + 10, text = int(self.layers[layer].stopV[i]), fill='Blue', font=('TkDefaultFont',10, 'bold'))
			lineType = self.layers[layer].lineTypes[i]
			w = 1;
			supportFlag = self.layers[layer].supportFlags[i]
			if supportFlag == 'part':
				w = 2;
			self.lineCanvas.create_line(XStartScreen, YStartScreen, XEndScreen, YEndScreen, fill = colorCodeDict[lineType], width  = w, arrow = self.arrowSelect)
			startPosX = endPosX
			startPosY = endPosY
	
		self.write_layer_to_terminal()
		return
	def list_colors(self):
		for colorCount in range(0,len(colorCodeDict)):
			actionType = list(colorCodeDict.keys())
			colorCode = list(colorCodeDict.values())
			#self.lineCanvas.create_text(self.width - 80,(colorCount*20) + 25, text=actionType[colorCount], fill=colorCode[colorCount], font=('TkDefaultFont',14, 'bold'))
			self.lineCanvas.create_text(self.width - 3,(colorCount*17) + 20, text=actionType[colorCount], fill=colorCode[colorCount], font=('TkDefaultFont',10, 'normal'), anchor='e')
		return
	def create_output(self):
		# create the output file
		#TODO: check how many files are in the directory and make that the loop condition
		outFile = open('output.txt', 'w')
		print( 'Converting file..' )
		# find the next valid vector file and begin conversion
		# exit if there are no more vector file in the folder
		fileIndex = 0
		inputFile = 'layer0000.vec'
		while True:     
			while os.path.isfile(inputFile) == False:
				#print(inputFile)
				#print(' does not exist.\n')
				fileIndex = fileIndex + 1
				inputFile = str(fileIndex).rjust(4,'0')
				inputFile = 'layer' + inputFile + '.vec'
				#print(inputFile)
				# stop checking if more than 600 layers
				if fileIndex > 600:
					#print('Max number of layers exceeded\n')
					print( "File conversion complete" )
					print( "File saved in:", os.getcwd())
					inFile.close()
					outFile.close()
					return
			inFile = open(inputFile, 'rb')          


			# validate the file and read the API version
			text = inFile.read(4)

			if text != b'ezir':
				print('File is not of RIZE3D type.')
				print('Fatal read error - Exiting program')
				sys.exit()

			# determine the API version and write to console
			#print("API Version: ", end="")
			version = inFile.read(4)
			versionNumber = struct.unpack('<L', version)
			# print(versionNumber)
			# read the rest of the header (18 dwords reserved space).
			header = inFile.read(72);
			reading = True
			# conversion loop for a given file
			while reading == True:
				# read the command
				opCode = inFile.read(2)

				#check if it has read to the end of the file
				if opCode == b'':
					# end the read cycle if file is at the end
					#print("Layer Complete")
					reading = False
					
				else:
					opCode = opCode[0]
					#print('Opcode: ' + str(opCode))
					outFile.write(opCodeDict[opCode])       
					outFile.write(':')
					if opCodeDict[opCode] == 'setPosition':
						
						data = inFile.read(2)
						dataSizedwords = 256*data[1] + data[0]
						#print('Size: ' + str(dataSizedwords))
						
						outFile.write(str(dataSizedwords))
						outFile.write(':')
						
						for dataCounter in range(0,int(dataSizedwords/2)):
							#outFile.write('\n')
							motor = struct.unpack('<L', inFile.read(4))[0]
							#print('Motor: ' + motorDict[motor])
							outFile.write(motorDict[motor])
							outFile.write(':')
							
							position = struct.unpack('<L', inFile.read(4))[0]
							#print('Position: ' + str(position))
							
							# divide by 1000 to display in mm instead of um
							outFile.write(str(position/1000))
							outFile.write(',')
							
					elif opCodeDict[opCode] == 'setTrajectory':
						
						data = inFile.read(2)
						dataSizedwords = 256*data[1] + data[0]
						#print('Size: ' + str(dataSizedwords))  
						
						outFile.write( str(dataSizedwords) )
						outFile.write(':')              
						
						for dataCounter in range(0,int(dataSizedwords/3) ):
							#outFile.write('\n')
							# X coordinate
							currentData = inFile.read(4)                                            
							dataValue = 16777216 * currentData[3] + 65536 * currentData[2] + 256 * currentData[1] + currentData[0]
							# divide by 1000 to display in mm instead of um
							outFile.write( str(dataValue/1000) )
							outFile.write(',')
							#print('X: ' + str(dataValue/1000))
							# Y coordinate
							currentData = inFile.read(4)                                            
							dataValue = 16777216 * currentData[3] + 65536 * currentData[2] + 256 * currentData[1] + currentData[0]
							# divide by 1000 to display in mm instead of um
							outFile.write( str(dataValue/1000) )
							outFile.write(',')      
							#print('Y: ' + str(dataValue/1000))
							
							# read exit angle, entry angle, line type, null
							currentData = inFile.read(4)
							data = struct.unpack('<L', currentData)[0]
							# line type
							linetype = (data >> 16) & 0x7F
							outFile.write(lineTypeDict[linetype])
							outFile.write(',')
							# part/support
							if linetype == 0:
								outFile.write("travel")
							elif ( data >> 16 ) & 0x80 == 0:
								outFile.write("part")
							else:                                                        
								outFile.write("support")
							outFile.write(',')
							# stop velocity
							stopV = (data >> 8) & 0xFF
							outFile.write(str(stopV))
							outFile.write(',')
							# max velocity
							maxV = (data >> 0) & 0xFF
							outFile.write(str(maxV))
							outFile.write(',')
							# density
							density = ((data >> 24) & 0xFF) * 12.75 / 255
							outFile.write(str(density))
							outFile.write(',')
							#print(str(data) + ' ' + str(linetype) + ' ' + str(stopV) + ' ' + str(maxV) + ' ' + str(density))
							
					elif opCodeDict[opCode] == 'setTravel':
						data = inFile.read(2)
						dataSizedwords = 256*data[1] + data[0]
						#print('Size: ' + str(dataSizedwords))  
						
						outFile.write( str(dataSizedwords) )
						outFile.write(':')              
						
						for dataCounter in range(0,int(dataSizedwords/2) ):
							#outFile.write('\n')
							# X coordinate
							currentData = inFile.read(4)                                            
							dataValue = 16777216 * currentData[3] + 65536 * currentData[2] + 256 * currentData[1] + currentData[0]
							# divide by 1000 to display in mm instead of um
							outFile.write( str(dataValue/1000) )
							outFile.write(',')
							#print('X: ' + str(dataValue/1000))
							# Y coordinate
							currentData = inFile.read(4)                                            
							dataValue = 16777216 * currentData[3] + 65536 * currentData[2] + 256 * currentData[1] + currentData[0]
							# divide by 1000 to display in mm instead of um
							outFile.write( str(dataValue/1000) )
							outFile.write(',')      
							#print('Y: ' + str(dataValue/1000))


					outFile.write( ';\n' )
							
			fileIndex = fileIndex + 1       
			inputFile = str(fileIndex).rjust(4,'0')
			inputFile = 'layer' + inputFile + '.vec'
			print('Reading File: ' + inputFile, end = '\r')
		return
		# BUTTON FUNCTIONS
	def open_files_to_default(self, event = None):
		# get the print data location
		outputdir = filedialog.askdirectory(title = 'Please select the directory containing the .vec files to convert')
		os.chdir(outputdir)
		self.open_files()
		return
	def open_files_to_AppData(self, event = None):
		# get the print directory location
		username = getpass.getuser()
		defaultpath = 'C:/Users/' + username + '/AppData/Local/File2Part/'
		outputdir = filedialog.askdirectory(initialdir = defaultpath, title = 'Please select a .vec file in the directory you wish to view from')
		os.chdir(outputdir)

		self.open_files()
		return
	def reset_view(self, event = None):
		if self.fileOpened == True:
			self.xOffsetDrag = 0
			self.yOffsetDrag = 0
			self.xOffset = 0
			self.yOffset = 0
			self.zoomScale = 2
			self.draw_moves()
		return
	def arrows_toggle(self, event = None):
		if self.fileOpened == True:
			if self.arrowSelect == NONE:
				self.arrowSelect = LAST
			else:
				self.arrowSelect = NONE
			self.draw_moves()
		return
	def maxv_toggle(self, event = None):
		if self.fileOpened == True:
			self.showMaxV = not self.showMaxV
			self.draw_moves()
		return
	def stopV_toggle(self, event = None):
		if self.fileOpened == True:
			self.showStopV = not self.showStopV
			self.draw_moves()
		return
	def density_toggle(self, event = None):
		if self.fileOpened == True:
			self.showDensity = not self.showDensity
			self.draw_moves()
	def colors_toggle(self, event = None):
		if self.fileOpened == True:
			self.colors = not self.colors
			self.draw_moves()
		return          
	def close_textWindow(self, event = None):
		self.showTextWindow = False
		self.textWindow.destroy()
		return
	def textWindow_toggle(self, event = None):
		if self.fileOpened == True:
			if self.showTextWindow == False:
				self.showTextWindow = True
				self.textWindow = Toplevel()
				self.textWindow.grid()
				self.textWindow.wm_protocol("WM_DELETE_WINDOW", self.close_textWindow)
				self.textWindow.title('.vec File Text')
				self.y_text_scrollbar = Scrollbar(self.textWindow, orient=VERTICAL)
				self.text_window = Text(self.textWindow, bg = 'white', yscrollcommand=self.y_text_scrollbar.set, width = 40, height = 16)
				self.text_window.grid(column = 0, columnspan = 1, row = 0, sticky=N+S+E+W)
				self.y_text_scrollbar.grid(column = 1, row = 0, sticky=N+S+E+W)         
				self.y_text_scrollbar.config(command=self.text_window.yview)
				
				self.textWindow.columnconfigure(0, weight = 1)
				self.textWindow.columnconfigure(1, weight = 0)
				self.textWindow.rowconfigure('all', weight = 1)
				
				if self.fileOpened == True:
					self.draw_moves()
			else:
				self.close_textWindow()
		return
root = Tk()
root.title('Vector File Viewer')
root.resizable(height=FALSE, width=FALSE)
root.columnconfigure(0, weight = 1)
root.rowconfigure(0, weight = 1)
#root.state("zoomed")
root.grid()

app = App(root)
# disable buttons on startup before opening a file
app.disable_buttons()

root.mainloop()
