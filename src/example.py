
from tkinter import *
import tkconfigure as tkc

master = Tk()
master.geometry("400x600")


class A:

	def __init__(self, fl: int, mi: int, ba: float):

		self.appConfig = tkc.AppConfig({
			'': {
				'filename': {
					'label': 'File name'
				}
			},
			'Calculation settings': {
				'maxIter': {
					'inputType': 'int',
					'valRange':  (100, 4000, 10),
					'initValue': mi,
					'widget':    'TKCSpinbox',
					'label':     'Max. iterations',
					'width':     10
				},
				'bailout': {
					'inputType': 'float',
					'valRange':  (4.0, 10000.0),
					'initValue': ba,
					'widget':    'TKCEntry',
					'label':     'Bailout radius',
					'width':     10
				}
			},
			'Modes': {
				'drawMode': {
					'inputType': 'str',
					'valRange':  ['Line-by-Line', 'SQEM recursive', 'SQEM iterative'],
					'initValue': 'Line-by-Line',
					'widget':    'TKCListbox',
					'label':     'Drawing mode'
				}
			}
		})

	def configure(self, master):
		row = self.appConfig.createMask(master, groups = [''], padx=2, pady=4)
		row = self.appConfig.createMask(master, startRow=row, groups=['Calculation settings', 'Modes'], groupWidth=380, padx=2, pady=4)
		b = Button(master, text="Print", command=onPrint)
		b.grid(columnspan=2, row=row+1, column=0, pady=10)


def onPrint():
	print(m.appConfig.getConfig())

m = A(0, 256, 4.0)
m.configure(master)


mainloop()

