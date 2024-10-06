
from tkinter import *
from tkinter import colorchooser
from tkinter.scrolledtext import ScrolledText
from tkconfigure import TKConfigure
import math
# import tkconfigure as tkc

defaultPaletteDef = {
	"Linear": {
		"name": "Grey",
		"type": "Linear",
		"size": 4096,
		"par": {
			"colorPoints": [(80/255, 80/255, 80/255), (1., 1., 1.)]
		}
	},
	"Sinus": {
		"name": "Sinus",
		"type": "Sinus",
		"size": 4096,
		"par": {
			"thetas": [.85, .0, .15]
		}
	}
}

class ColorEditor:

	def __init__(self, mainWindow, width: int = 400, height: int = 600, palettedef: dict = defaultPaletteDef['Linear']):
		self.paletteDef = palettedef
		self.orgPaletteDef = palettedef

		self.masterSettings = TKConfigure({
			"Palette": {
				'paletteName': {
					'inputtype': 'str',
					'initvalue': palettedef['name'],
					'widget':    'TKCEntry',
					'label':     'Palette name',
					'width':     15
				},
				'paletteType': {
					'inputtype': 'str',
					'valrange':  ['Linear', 'Sinus'],
					'initvalue': palettedef['type'],
					'widget':    'TKCListbox',
					'label':     'Palette type',
					'width':     20,
					'notify':    self.onPaletteTypeChanged
				},
				'paletteSize': {
					'inputtype': 'int',
					'valrange':  (1, 4096),
					'initvalue': palettedef['size'],
					'label':     'Entries',
					'widget':    'TKCSpinbox',
					'width':     8
				},
				'colorTable': {
					'inputtype': 'list',
					'initvalue': self.createPaletteFromDef(palettedef),
					'widget':    'TKCColortable',
					'width':     width-20,
					'readonly':  True
				}
			}
		})

		self.typeSettings = self.paletteTypeSettings(palettedef)

		self.width      = width
		self.height     = height
		self.mainWindow = mainWindow
		self.apply      = False

	# Show color editor
	def show(self, palettedef: dict | None = None) -> bool:
		# Create the window
		self.dlg = Toplevel(self.mainWindow)
		self.dlg.geometry(f"{self.width}x{self.height}")
		self.dlg.title("Color Editor")

		if palettedef is not None:
			self.paletteDef = palettedef
			self.orgPaletteDef = palettedef
			colorTable = self.createPaletteFromDef(palettedef)
			self.masterSettings.setValues(
				paletteName=palettedef['name'],
				paletteType=palettedef['type'],
				paletteSize=palettedef['size'],
				colorTable=colorTable
			)
			self.typeSettings = self.paletteTypeSettings(palettedef)

		# Create widgets
		self.tsrow = self.masterSettings.createMask(self.dlg, padx=3, pady=5)
		self.btnrow = self.typeSettings.createMask(self.dlg, startrow=self.tsrow, padx=3, pady=5)

		# Buttons
		self.btnOk     = Button(self.dlg, text="Ok", command=lambda: self.setApply(True))
		self.btnCancel = Button(self.dlg, text="Cancel", command=lambda: self.setApply(False))
		self.btnReset  = Button(self.dlg, text="Reset", command=lambda: self.onReset())
		self.btnOk.grid(column=0, row=self.btnrow)
		self.btnCancel.grid(column=1, row=self.btnrow)
		self.btnReset.grid(column=3, row=self.btnrow)

		self.dlg.wait_window()

		return self.apply

		"""
		self.colorPoints = Frame(self.dlg, width=500, height=50)
		self.colorPoints.place(x=10, y=20)

		# Scrollbars
		self.hScroll = Scrollbar(self.colorPoints, orient='horizontal')
		self.hScroll.pack(fill=X, side=BOTTOM)

		# Create drawing canvas and link with scrollbars
		self.canvas = Canvas(self.colorPoints, width=600, height=50, bg='black', bd=0, highlightthickness=0, scrollregion=(0, 0, 600, 50))
		self.hScroll.config(command=self.canvas.xview)
		self.canvas.config(xscrollcommand=self.hScroll.set)
		self.canvas.pack(side=LEFT, expand=False, fill=NONE, anchor='nw')
		"""

	# Create palette type specific settings
	def paletteTypeSettings(self, palettedef: dict):
		if palettedef['type'] == 'Linear':
			colorSettings = { 'Color points': {} }
			for n, cp in enumerate(palettedef['par']['colorPoints'], start=0):
				colorSettings['Color points']['point' + str(n)] = {
					'inputtype': 'str',
					'initvalue': '#{:02X}{:02X}{:02X}'.format(int(cp[0]*255), int(cp[1]*255), int(cp[2]*255)),
					'label':     'point ' + str(n),
					'widget':    'TKCColor',
					'width':     80,
					'notify':    self.onPointChanged
				}
			return TKConfigure(colorSettings)
		
		elif palettedef['type'] == 'Sinus':
			colorSettings = { 'Thetas': {} }
			for n, t in enumerate(palettedef['par']['thetas'], start=1):
				colorSettings['Thetas']['theta' + str(n)] = {
					'inputtype': 'float',
					'valrange':  (0, 1, 0.01),
					'initvalue': t,
					'label':     'theta ' + str(n),
					'widget':    'TKCSlider',
					'width':     120,
					'notify':    self.onThetaChanged
				}
			return TKConfigure(colorSettings)
	
	def _str2rgb(self, html: str, f = 1) -> tuple:
		return [int(html[i:i+2], 16) / f for i in (1, 3, 5)]
	
	def _linspace(self, start, end, count) -> list:
		if type(start) is tuple and type(end) is tuple:
			if len(start) != len(end):
				raise ValueError("tuples start and end must have the same size")
			d = [ (end[i]-start[i]) / (count-1) for i in range(3) ]
			return [ [start[i]+d[i]*n for i in range(3)] for n in range(count) ]
		else:
			d = (end-start)/(count-1)
			return [ start+d*i for i in range(count) ]

	def createLinearPalette(self, numColors: int, colorPoints: list = [(1., 1., 1.)]) -> list:
		if len(colorPoints) == 0:
			# Greyscale palette
			palette = self._linspace((0., 0., 0.), (1., 1., 1.), max(numColors, 2))
		elif (len(colorPoints) == 1):
			# Monochrome palette
			palette = [colorPoints[0] for i in range(numColors) ]
		else:
			numColors = max(numColors,len(colorPoints))
			secSize = int(numColors/(len(colorPoints)-1))
			palette = [list(colorPoints[0])]
			for i in range(len(colorPoints)-1):
				if secSize + len(palette)-1 > numColors: secSize = numColors - len(palette)
				palette.pop()
				palette += (self._linspace(colorPoints[i], colorPoints[i+1], secSize))

		return palette
	
	def createSinusPalette(self, numColors: int, thetas: list = [.85, .0, .15]) -> list:
		numColors = max(numColors, 2)
		ct = self._linspace((0, 0, 0), (1, 1, 1), numColors)
		for i in range(numColors):
			for n in range(3):
				ct[i][n] = 0.5 + 0.5 * math.sin((ct[i][n] + thetas[n]) * 2 * math.pi)

		return ct
	
	def createPaletteFromDef(self, paletteDef: dict, size: int = -1) -> list:
		entries = size if size != -1 else paletteDef['size']
		if paletteDef['type'] == 'Linear':
			return self.createLinearPalette(entries, **paletteDef['par'])
		elif paletteDef['type'] == 'Sinus':
			return self.createSinusPalette(entries, **paletteDef['par'])
		else:
			raise ValueError("Illegal palette type")

	def onPaletteTypeChanged(self, oldValue, newValue):
		paletteDef = defaultPaletteDef[newValue]
		colortable = self.createPaletteFromDef(paletteDef)
		self.typeSettings.deleteMask()
		self.typeSettings = self.paletteTypeSettings(paletteDef)
		self.masterSettings.setValues(colorTable=colortable, sync=True)
		self.btnrow = self.typeSettings.createMask(self.dlg, startrow=self.tsrow, padx=3, pady=5)

	def onPointChanged(self, oldValue, newValue):
		nPoints = len(self.paletteDef['par']['colorPoints'])
		pList = [ 'point' + str(i) for i in range(nPoints) ]
		colorPoints = self.typeSettings.getValues(pList)
		rgbPoints = [ self._str2rgb(cp, f=255) for cp in colorPoints ]
		colorTable = self.createPaletteFromDef({
			"type": self.paletteDef['type'],
			"size": self.masterSettings['paletteSize'],
			"par": {
				"colorPoints": rgbPoints
			}
		})
		self.masterSettings.set('colorTable', colorTable, sync=True)

	def onThetaChanged(self, oldValue, newValue):
		thetas = [ self.typeSettings['theta1'], self.typeSettings['theta2'], self.typeSettings['theta3'] ]
		colorTable = self.createPaletteFromDef({
			"type": "Sinus",
			"size": self.masterSettings['paletteSize'],
			"par": {
				"thetas": thetas
			}
		})
		self.masterSettings.set('colorTable', colorTable, sync=True)

	def setApply(self, apply: bool):
		self.apply = apply
		if apply:
			self.paletteDef = {
				'name': self.masterSettings['paletteNamw'],
				'type': self.masterSettings['paletteType'],
				'size': self.masterSettings['size'],
				'par':  { }
			}
			if self.masterSettings['type'] == 'Linear':
				self.paletteDef['par']['colorPoints'] = [ self._str2rgb(cp, f=255) for cp in self.typeSettings['Color points'] ]
			elif self.masterSettings['type'] == 'Sinus':
				self.paletteDef['par']['thetas'] = [ self._str2rgb(cp, f=255) for cp in self.typeSettings['Thetas'] ]
		self.dlg.destroy()

	def onReset(self):
		self.paletteDef = self.orgPaletteDef
		colortable = self.createPaletteFromDef(self.paletteDef)
		self.typeSettings.deleteMask()
		self.typeSettings = self.paletteTypeSettings(self.paletteDef)
		self.masterSettings.setValues(paletteName=self.paletteDef['name'], paletteSize=self.paletteDef['size'], colorTable=colortable, sync=True)
		self.btnrow = self.typeSettings.createMask(self.dlg, startrow=self.tsrow, padx=3, pady=5)
