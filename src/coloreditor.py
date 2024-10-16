
from tkinter import *
from tkinter import colorchooser
from tkinter.scrolledtext import ScrolledText
import math
import tkconfigure as tkc


# Default palette definitions, key = palette type
defaultPaletteDef = {
	"Linear": {
		"type": "Linear",
		"size": 4096,
		"par": {
			"colorPoints": [(80/255, 80/255, 80/255), (1., 1., 1.)]
		}
	},
	"Sinus": {
		"type": "Sinus",
		"size": 4096,
		"par": {
			"thetas": [.85, .0, .15]
		}
	}
}

class ColorEditor:

	def __init__(self, mainWindow, width: int = 400, height: int = 600, palettename: str = 'Grey', palettedef: dict = defaultPaletteDef['Linear']):
		self.orgPaletteDef  = palettedef
		self.orgPaletteName = palettename

		self.masterSettings = tkc.TKConfigure({
			"Palette": {
				'paletteName': {
					'inputtype': 'str',
					'initvalue': palettename,
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
					'initvalue': [ palettedef, self.createPaletteFromDef(palettedef), palettename ],
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
	def show(self, title: str = "Color Editor", colorTable: list | None = None, palettename: str | None = None, palettedef: dict | None = None) -> bool:
		# Create the window
		self.dlg = Toplevel(self.mainWindow)
		self.dlg.geometry(f"{self.width}x{self.height}")
		self.dlg.grab_set()
		self.dlg.title(title)

		if colorTable is not None:
			self.orgPaletteDef = colorTable[0]
			self.orgPaletteName = colorTable[2]
			self.masterSettings.setValues(
				paletteName=colorTable[2],
				paletteType=colorTable[0]['type'],
				paletteSize=colorTable[0]['size'],
				colorTable=colorTable
			)
			self.typeSettings = self.paletteTypeSettings(colorTable[0])
		elif palettename is not None and palettedef is not None:
			self.orgPaletteDef  = palettedef
			self.orgPaletteName = palettename

			self.masterSettings.setValues(
				paletteName=palettename,
				paletteType=palettedef['type'],
				paletteSize=palettedef['size'],
				colorTable=[palettedef, self.createPaletteFromDef(palettedef), palettename]
			)
			self.typeSettings = self.paletteTypeSettings(palettedef)

		# Create widgets
		self.tsrow  = self.masterSettings.createMask(self.dlg, padx=3, pady=5)
		self.btnrow = self.typeSettings.createMask(self.dlg, startrow=self.tsrow, padx=3, pady=5)

		# Create buttons
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
			return tkc.TKConfigure(colorSettings)
		
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
			return tkc.TKConfigure(colorSettings)
	
	# Convert html color string to rgb 0..1 (f=255) or rgbi 0..255 (f=1)
	def _str2rgb(self, html: str, f = 1) -> tuple:
		return tuple([int(html[i:i+2], 16) / f for i in (1, 3, 5)])
	
	# Create list of count values with linear distribution between start and end
	def _linspace(self, start, end, count) -> list:
		if type(start) is tuple and type(end) is tuple:
			if len(start) != len(end):
				raise ValueError("tuples start and end must have the same size")
			d = [ (end[i] - start[i]) / (count-1) for i in range(3) ]
			return [ [start[i] + d[i] * n for i in range(3)] for n in range(count) ]
		else:
			d = (end-start)/(count-1)
			return [ start + d * i for i in range(count) ]

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

	def updateColorTable(self, palettedef: dict):
		colortable = self.createPaletteFromDef(palettedef)
		self.masterSettings.set('colorTable', [palettedef, colortable, self.masterSettings['paletteName']], sync=True)

	# Palette type changed
	def onPaletteTypeChanged(self, oldValue, newValue):
		paletteDef = defaultPaletteDef[newValue]

		# Update color table
		self.updateColorTable(paletteDef)

		# Recreate type specific part of the input mask
		self.typeSettings.deleteMask()
		self.typeSettings = self.paletteTypeSettings(paletteDef)
		self.btnrow = self.typeSettings.createMask(self.dlg, startrow=self.tsrow, padx=3, pady=5)

	# Linear palette: Color point changed
	def onPointChanged(self, oldValue, newValue):
		colorPoints = self.typeSettings.getIds(group='Color points')
		rgbPoints = [ self._str2rgb(self.typeSettings[cp], f=255) for cp in colorPoints ]
		self.updateColorTable({
			"type": self.masterSettings['paletteType'],
			"size": self.masterSettings['paletteSize'],
			"par": {
				"colorPoints": rgbPoints
			}
		})

	# Sinus palette: One of the theta values changed
	def onThetaChanged(self, oldValue, newValue):
		thetas = [ self.typeSettings['theta1'], self.typeSettings['theta2'], self.typeSettings['theta3'] ]
		self.updateColorTable({
			"type": "Sinus",
			"size": self.masterSettings['paletteSize'],
			"par": {
				"thetas": thetas
			}
		})

	# Button OK or CANCEL pressed
	def setApply(self, apply: bool):
		self.apply = apply

		# Close dialog window
		self.dlg.destroy()

	# Button RESET pressed
	def onReset(self):
		self.typeSettings.deleteMask()
		self.typeSettings = self.paletteTypeSettings(self.orgPaletteDef)
		self.masterSettings.setValues(
			paletteName=self.orgPaletteName,
			paletteSize=self.orgPaletteDef['size'],
			colorTable=[self.orgPaletteDef, self.createPaletteFromDef(self.orgPaletteDef), self.orgPaletteName],
			sync=True)
		self.btnrow = self.typeSettings.createMask(self.dlg, startrow=self.tsrow, padx=3, pady=5)
