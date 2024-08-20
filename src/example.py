
from tkinter import *
import tkconfigure as tkc



# An application class
class App:

	def __init__(self, fl: int, mi: int, ba: float):

		# Create a window
		self.master = Tk()
		self.master.geometry("600x600")

		# TKC configuration
		self.appConfig = tkc.TKConfigure({
			# Parameters with no group (group name is '')
			'': {
				# Leaving most of the attributes empty will create a TKCEntry widget
				'filename': {
					'label': 'File name'
				}
			},
			# First group 'Calculation settings'
			'Calculation settings': {
				# Integer parameter shown as TKCSpinbox widget
				'maxIter': {
					'inputType': 'int',               # Input type ('int', 'float' or 'str')
					'valRange':  (100, 4000, 10),     # Value range 100-4000 and increment
					'initValue': mi,                  # Initial / default value for the parameter
					'widget':    'TKCSpinbox',        # The widget type
					'label':     'Max. iterations',   # Label shown in front or top of the widget
					'width':     10                   # Width of the widget in characters
				},
				# Float parameter shown as TKCEntry widget with numeric input only
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
					'initValue': 'Line-by-Line',   # Type of initial value must match the input type
					'widget':    'TKCListbox',
					'label':     'Drawing mode',
					'width':     15
				},
				'iDrawMode': {
					'inputType': 'int',            # Widget should return the selected string instead of the list index
					'valRange':  [                 # Value list required because of input type 'str'
						'Line-by-Line',
						'SQEM recursive',
						'SQEM iterative'
					],
					'initValue': 'Line-by-Line',   # Type of initial value must match the input type
					'widget':    'TKCListbox',
					'label':     'Drawing mode',
					'width':     15
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

	# This function creates the widgets
	def configure(self):
		# Create the widgets with the specified groups. The width of the Labelframe for the groups is 380 pixels
		row = self.appConfig.createMask(self.master, startrow=0, groups=['', 'Calculation settings', 'Modes', 'Flags'], groupwidth=400, padx=10, pady=5)

		# Add a button to show the current configuration
		btn1 = Button(self.master, text="Print", command=self.onPrint)
		btn1.grid(row=row, column=0, pady=10)
		btn2 = Button(self.master, text="Configure", command=self.onConfigure)
		btn2.grid(row=row, column=1)

	# Function is called when button is pressed. Shows the current configuration
	def onPrint(self):
		print(self.appConfig.getConfig())

	def onConfigure(self):
		self.appConfig.createDialog(self.master, 450, 700, title="Change configuration", padx=10, pady=5)


##########################
#  Main program
##########################

# Create the app
myApp = App(0, 256, 4.0)

# Show parameter configuration widgets
myApp.configure()


mainloop()

