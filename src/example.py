
from tkinter import *
import tkconfigure as tkc



# An application class
class App:

	def __init__(self, fl: int, mi: int, ba: float):

		# Create a window
		self.master = Tk()
		self.master.geometry("600x800")
		self.master.title("TKConfigure Sample App")

		# TKC configuration
		self.appConfig = tkc.TKConfigure({
			# Parameters with no group (group name is empty string)
			'': {
				# Leaving most of the attributes empty will create a TKCEntry widget
				'filename': {
					'valrange':  (1, 10),              # Enter min 1, max 10 characters
					'initvalue': 'myfractal',
					'label':     'File name'
				}
			},
			# First group 'Calculation settings'
			'Calculation settings': {
				# Complex parameter represented by a TKCEntry widget
				'corner': {
					'inputtype': 'complex',
					'initvalue': complex(-2.25, -1.5),
					'widget':    'TKCEntry',
					'label':     'Complex corner',
					'width':     10
				},
				# Integer parameter represented by a TKCSpinbox widget
				'maxIter': {
					'inputtype': 'int',               # Input type ('int', 'float' or 'str')
					'valrange':  (100, 4000, 10),     # Value range 100-4000 and increment
					'initvalue': mi,                  # Initial / default value for the parameter
					'widget':    'TKCSpinbox',        # The widget type
					'label':     'Max. iterations',   # Label shown in front or top of the widget
					'width':     10                   # Width of the widget in characters
				},
				# Float parameter represented by a TKCEntry widget with numeric input only
				'bailout': {
					'inputtype': 'float',
					'valrange':  (4.0, 10000.0),
					'initvalue': ba,
					'widget':    'TKCEntry',
					'label':     'Bailout radius',
					'width':     10
				}
			},
			# Second group 'Modes'
			'Modes': {
				# This parameter is represented by a TKCListbox widget (a readonly Combobox)
				'sDrawMode': {
					'inputtype': 'str',            # Widget should return the selected string instead of the list index
					'valrange':  [                 # Listbox entries
						'Line-by-Line',
						'SQEM recursive',
						'SQEM iterative'
					],
					'initvalue': 'Line-by-Line',   # If inputtype is 'str', the initial value must be part of valrange list
					'widget':    'TKCListbox',
					'label':     'Drawing mode str',
					'width':     15
				},
				'iDrawMode': {
					'inputtype': 'int',            # Widget should return the index of the selected string
					'valrange':  [                 # Listbox entries
						'Line-by-Line',
						'SQEM recursive',
						'SQEM iterative'
					],
					'initvalue': 0,                # If inputtype is numeric, the initial value must be an index for valrange list
					'widget':    'TKCListbox',
					'label':     'Drawing mode int',
					'width':     15,
					'widgetattr': {
						'justify': 'left'          # Widget attribute for this parameter only	
					}
				}
			},
			"Flags": {
				'distance': {
					'inputtype': 'int',
					'valrange':  (0, 1),           # For checkbuttons: tuple(offvalue, onvalue)
					'initvalue': 0,
					'widget':    'TKCCheckbox',
				},
				'potential': {
					'inputtype': 'int',
					'valrange':  (10, 11),         # 10 = on, 11 = off
					'initvalue': 11,
					'widget':    'TKCCheckbox'
				},
				# Combined flags, stored as bits, represented by a TKCFlags widget
				# A TKCWidget contains a checkbox for each flag (bit). The checkboxes are
				# surrounded by a Labelframe.
				'calcOptions': {
					'inputtype': 'bits',
					'valrange':  [ 'Interations', 'Potential', 'Distance' ],
					'initvalue': 5,
					'widget':    'TKCFlags',
					'widgetattr': {                # Attributes of the Labelframe
						'text': 'Calculation flags'
					}
				},
				'colorMapping': {
					'inputtype': 'int',
					'valrange':  [ 'Modulo', 'Linear' ],
					'initvalue': 0,
					'widget':    'TKCRadiobuttons',
					'widgetattr': {
						'text': 'Color mapping'
					}
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
		self.appConfig.syncConfig()
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