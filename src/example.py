
from tkinter import *
import tkconfigure as tkc

master = Tk()
master.geometry("400x600")


class A:

	def __init__(self, fl: int, mi: int, ba: float):

		self.appConfig = tkc.AppConfig({
			'maxIter': {
				'group':     'Calculation settings',
				'inputType': 'int',
				'valRange':  (100, 4000, 10),
				'initValue': mi,
				'widget':    'TKCNumSpinbox',
				'label':     'Max. iterations',
				'width':     10
			},
			'bailout': {
				'group':     'Calculation settings',
				'inputType': 'float',
				'valRange':  (4.0, 10000.0),
				'initValue': ba,
				'widget':    'TKCNumEntry',
				'label':     'Bailout radius',
				'width':     10
			},
			'drawMode': {
				'group':     'Modes',
				'inputType': 'int',
				'valRange':  ('Line-by-Line', 'SQEM recursive', 'SQEM iterative'),
				'initValue': 'Line-by-Line',
				'widget':    'TKCListbox',
				'label':     'Drawing mode',
				'width':     20
			}
		})

	def configure(self, master):
		row = self.appConfig.createMask(master, groups=['Calculation settings', 'Modes', 'none'], groupWidth=380, padx=2, pady=4)
		b = Button(master, text="Print", command=onPrint)
		b.grid(columnspan=2, row=row+1, column=0, pady=10)


def onPrint():
	print(m.appConfig.getConfig())

m = A(0, 256, 4.0)
m.configure(master)


mainloop()

