
from tkinter import *
import tkconfigure as tkc



# An application class
class App:

	def __init__(self, fl: int, mi: int, ba: float):

		# Create a window
		self.master = Tk()
		self.master.geometry("600x600")
		self.master.title("TKConfigure Sample App")

		# TKC configuration
		self.appConfig = tkc.TKConfigure({
			# Parameters with no group (group name is empty string)
			'': {
				# Leaving most of the attributes empty will create a TKCEntry widget
				'filename': {
					'label': 'File name'
				}
			},
			# First group 'Calculation settings'
			'Calculation settings': {
				# Integer parameter represented by a TKCSpinbox widget
				'maxIter': {
					'inputType': 'int',               # Input type ('int', 'float' or 'str')
					'valRange':  (100, 4000, 10),     # Value range 100-4000 and increment
					'initValue': mi,                  # Initial / default value for the parameter
					'widget':    'TKCSpinbox',        # The widget type
					'label':     'Max. iterations',   # Label shown in front or top of the widget
					'width':     10                   # Width of the widget in characters
				},
				# Float parameter represented by a TKCEntry widget with numeric input only
				'bailout': {
					'inputType': 'float',
					'valRange':  (4.0, 10000.0),
					'initValue': ba,
					'widget':    'TKCEntry',
					'label':     'Bailout radius',
					'width':     10
				}
			},
			# Second group 'Modes'
			'Modes': {
				# This parameter is represented by a TKCListbox widget (a readonly Combobox)
				'sDrawMode': {
					'inputType': 'str',            # Widget should return the selected string instead of the list index
					'valRange':  [                 # Value list required because of input type 'str'
						'Line-by-Line',
						'SQEM recursive',
						'SQEM iterative'
					],
					'initValue': 'Line-by-Line',   # If inputType is 'str', the initial value must be part of valRange list
					'widget':    'TKCListbox',
					'label':     'Drawing mode str',
					'width':     15
				},
				'iDrawMode': {
					'inputType': 'int',            # Widget should return index of the selected string
					'valRange':  [                 # Value list required because of input type 'str'
						'Line-by-Line',
						'SQEM recursive',
						'SQEM iterative'
					],
					'initValue': 0,                # if inputType is numeric, the initial value is a valid index for valRange list
					'widget':    'TKCListbox',
					'label':     'Drawing mode int',
					'width':     15,
					'widgetAttr': {
						'justify': 'left'          # Widget attribute for this parameter only	
					}
				}
			},
			"Flags": {
				'distance': {
					'inputType': 'int',
					'initValue': 0,
					'widget':    'TKCCheckbox',
				},
				'potential': {
					'inputType': 'int',
					'initValue': 0,
					'widget':    'TKCCheckbox'
				}
			}
		})

	def run(self):
		self.master.mainloop()

	# This function creates the widgets
	def showMask(self):
		# Create the widgets with the specified groups. The width of the Labelframe for the groups is 380 pixels
		row = self.appConfig.createMask(self.master, startrow=0, groups=['', 'Calculation settings', 'Modes', 'Flags'], groupwidth=400, padx=10, pady=5)

		# Add a button to show the current configuration
		btn1 = Button(self.master, text="Print", command=self.onPrint)
		btn2 = Button(self.master, text="Configure", command=self.onConfigure)
		btn3 = Button(self.master, text="Undo", command=self.onUndo)
		btn2.grid(row=row, column=0, pady=10)
		btn3.grid(row=row, column=1, pady=10)
		btn1.grid(row=row+1, column=0, pady=10)

	# Function is called when button is pressed. Shows the current configuration
	def onPrint(self):
		for id in self.appConfig.getIds():
			print(id, "=", self.appConfig[id])
		print(self.appConfig.config)

	def onConfigure(self):
		status = self.appConfig.showDialog(self.master, width=500, height=0, title="Change configuration", groupwidth=400, padx=5, pady=5)
		if status:
			print("Config changed")
			self.appConfig.syncWidget()
		else:
			print("Config not changed")

	def onUndo(self):
		self.appConfig.undo()
		self.appConfig.syncWidget()

##########################
#  Main program
##########################

# Create the app
myApp = App(0, 256, 4.0)

# Show parameter configuration widgets
myApp.showMask()

myApp.run()