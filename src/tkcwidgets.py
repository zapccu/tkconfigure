import tkinter as tk
import tkinter.ttk as ttk
import re

from tkinter.colorchooser import askcolor
from typing import Literal

from . import coloreditor as ce


class Tooltip(object):

	def __init__(self, widget, text: str,
			showtimeout: int = 500,	# Time in milliseconds before showing the tooltip
			hidetimeout: int = 0,	# Time in milliseconds before hiding the tooltip, default = 0 = show endlessly
			wrap: int = 180,		# Textwrapping in pixels
			fg: str = '#000000',	# Text color, default = Black
			bg: str = '#ffff00'		# Background color, default = Yellow
		):

		self.widget      = widget
		self.text        = text
		self.showtimeout = showtimeout
		self.hidetimeout = hidetimeout
		self.wrap        = wrap
		self.fg          = fg
		self.bg          = bg

		self.widget.bind("<Enter>", self.enter)
		self.widget.bind("<Leave>", self.leave)
		self.widget.bind("<ButtonPress>", self.leave)

		self.timerShow = None
		self.timerHide = None
		self.win       = None

	def enter(self, event=None):
		self.unschedule()
		self.timerShow = self.widget.after(self.showtimeout, self.show)

	def leave(self, event=None):
		self.unschedule()
		self.hide()

	def unschedule(self):
		timerShow = self.timerShow
		self.timerShow = None
		if timerShow:
			self.widget.after_cancel(timerShow)

	def show(self, event=None):
		x = y = 0
		x, y, cx, cy = self.widget.bbox("insert")
		x += self.widget.winfo_rootx() + 25
		y += self.widget.winfo_rooty() + 20

		# creates a toplevel window
		self.win = tk.Toplevel(self.widget)
		
		# Leaves only the label and removes the app window
		self.win.wm_overrideredirect(True)
		self.win.wm_geometry("+%d+%d" % (x, y))
		label = tk.Label(self.win, text=self.text, justify='left',
					bg=self.bg, fg=self.fg, relief='solid', borderwidth=0,
					wraplength = self.wrap, padx=5, pady=5)
		label.pack()
		if self.hidetimeout > 0:
			self.timerHide = self.widget.after(self.hidetimeout, self.hide)

	def hide(self):
		win = self.win
		self.win = None
		if win:
			win.destroy()


###############################################################################
# Base class for all TKC widgets
#
# Configuration update mechanism:
#
# - When widget value has changed, call _TKCWidget._update()
# - If onChange callback function is defined for widget, _update is calling
#   onChange. Usually onChange = TKConfigure._onChange
# - TKConfigure._onChange is storing the new value in the current configuration
#   If customer app defined a notification callback, this function is called
#   with old and new value as parameter.
###############################################################################

class _TKCWidget:

	# Widget class names
	_WIDGETS_ = [
		'TKCSpinbox',         # Numeric entry field with spinner
		'TKCEntry',           # Entry field
		'TKCListbox',         # Dopdown list
		'TKCCheckbox',        # A single checkbox
		'TKCRadiobuttons',    # Multiple radio buttons
		'TKCFlags',           # Multiple checkboxes representing single bits
		'TKCSlider',          # Horizontal slider
		'TKCColor',           # Rectangle with color => click opens color chooser
		'TKCColortable',      # Rectangle with color table => click opens color editor,
		'TKCList',            # Read-only entry field with list values => click opens list editor,
		'TKCDialog',          # A top level dialog window to enter values of a TKConfigure object
		'TKCMask'             # Submask with widgets, used for inputtype 'tkc'
	]

	_INPUTTYPES = ['int', 'float', 'str', 'bits', 'complex', 'list', 'tkc']

	def __init__(self, parent, id: str, inputtype: Literal['int','float','str','bits','complex','list','tkc'] = 'str',
			  valrange = None, initvalue = None, onChange = None, readonly: bool = False):
		self.parent    = parent
		self.id        = id
		self.inputtype = inputtype
		self.onChange  = onChange
		self.valrange  = valrange
		self.readonly  = readonly

		# Set widget to initial value
		if not self._validate(initvalue):
			raise ValueError(f"{id}: inputtype={inputtype}, initvalue={initvalue}, valrange={valrange}")
		self.initvalue = initvalue
		self.set(initvalue)

		if not readonly and onChange is not None:
			self.bind('<FocusOut>', self._update)
			self.bind('<Return>', self._update)

	@staticmethod
	def _checkParameters(inputtype: str, valrange: list | tuple | None, vrMandatory: bool = False):
		if inputtype is None:
			raise ValueError('inputtype == None')
		if inputtype not in _TKCWidget._INPUTTYPES:
			raise ValueError(f"Invalid inputtype {inputtype}. Supported inputtypes: {_TKCWidget._INPUTTYPES}")

		if valrange is None and vrMandatory:
			raise ValueError('Missing mandatory valrange')
		elif type(valrange) is tuple:
			if inputtype != 'str' and (len(valrange) < 2 or len(valrange) > 3):
				raise ValueError("valrange must contain 2 or 3 values")
		elif type(valrange) is list and len(valrange) == 0:
			raise ValueError('valrange == []')
		elif valrange is not None and type(valrange) not in [list, tuple]:
			raise TypeError("valrange must be None or list or tuple")

	# Check if value is in valrange
	def _checkRange(self, value) -> bool:
		if self.valrange is None or len(self.valrange) == 0:
			return True
		try:
			if type(self.valrange) is tuple:
				if self.inputtype in ['int','float','complex']:
					return self.valrange[0] <= value <= self.valrange[1]
				elif self.inputtype == 'str':
					if len(self.valrange) == 2:
						return self.valrange[0] <= len(str(value)) <= self.valrange[1]
					elif len(self.valrange) == 1:
						return True if re.match(self.valrange[0], value) else False
					else:
						return True
				elif self.inputtype == 'list':
					if len(self.valrange) == 2:
						return self.valrange[0] <= len(value) <= self.valrange[1]
					else:
						return True
				else:
					return False
			elif type(self.valrange) is list:
				if self.inputtype == 'str':
					return value in self.valrange
				elif self.inputtype == 'bits':
					return 0 <= int(value) < 2**len(self.valrange)
				elif self.inputtype in ['int','float']:
					return 0 <= int(value) < len(self.valrange)
				else:
					return False
		except:
			print(f"_checkRange exception: inputtype={self.inputtype}, valrange={self.valrange}, value={value}")
			return False

	# Validate value
	def _validate(self, value) -> bool:
		if self.inputtype == 'str' and type(self.valrange) is list:
			return value in self.valrange		
		try:
			if self.inputtype == 'int' or self.inputtype == 'bits':
				v = int(value)
			elif self.inputtype == 'float':
				v = float(value)
			elif self.inputtype == 'complex':
				v = complex(value)
			return True
		except ValueError:
			return False
	
	# Called when widget value has changed
	def _update(self, event = None):
		if self.readonly: return

		value = self._getWidgetValue()
		if value is None:
			if self.onChange is not None:
				self.onChange(self.id, None)
		else:
			if self._validate(value) and self._checkRange(value):
				if value != self.var:
					self.var = value
					# Inform app (TKConfigure) about new widget value
					if self.onChange is not None:
						self.onChange(self.id, value)
				return

			# on error set widget value to initvalue
			if self.initvalue is not None:
				self.set(self.initvalue)

	# Return the current value of a widget. By default this function returns None.
	# Function must be overwritten in child classes to return a valid value with the
	# appropriate type, i.e. the index of the selected entry of a TKCListbox.
	# This function is called by _update() to retrieve the current widget value.
	def _getWidgetValue(self):
		return None
	
	# Set the widget value. By default this function has no implementation.
	# Function must be overwritten in child classed to set a widget to the specified value.
	# This function is called by set() to update a widget value.
	def _setWidgetValue(self, value):
		pass

	# Return widget value casted to inputtype
	def get(self):
		if self.inputtype in ['int','bits'] and type(self.var) is not int:
			return int(self.var)
		elif self.inputtype == 'float' and type(self.var) is not float:
			return float(self.var)
		elif self.inputtype == 'complex' and type(self.var) is not complex:
			return complex(self.var)
		elif self.inputtype == 'str' and type(self.var) is not str:
			return str(self.var)
		else:
			return self.var
	
	def getStr(self) -> str:
		return str(self.var)
	
	def __str__(self):
		return str(self.var)
	
	def set(self, value):
		if self._validate(value) and self._checkRange(value):
			self.var = value
			self._setWidgetValue(value)
		else:
			raise ValueError(type(self).__name__, self.id, value)

###############################################################################
#
# Create a Spinbox widget
#
# Usage:
#
#   Spinbox = TKCSpinbox(master, valrange=<list>|<tuple>, options,
#                        tkinter-Spinbox-options)
#
# Parameters:
#
#   master - the parent window
#
#   valrange - List with valid values or tuple with range of values.
#              Tuple with range is only allowed for inputtype 'int'
#              or 'float'. Format of tuple: (from, to [,increment])
#
#   options - key-value pairs:
#
#     inputtype: Either 'int', 'float' or 'str', default = 'int'
#     initvalue: Initial value
#     onChange:  A function which is called with the current widget value as
#                parameter when either spinner buttons were pressed or ENTER
#                key has been pressed or widget lost the focus.
#
# Methods:
#
#   get()      - Return the current value
#   getStr()   - Return the current value as string
#   set(value) - Set widget value
#
###############################################################################

class TKCSpinbox(_TKCWidget, tk.Spinbox):

	def __init__(self, parent, id: str, inputtype: Literal['int','float','str'] = 'int',
				valrange: tuple = (0, 0, 1), initvalue = None, onChange = None, readonly: bool = False,
				*args, **kwargs):
		# Check parameters
		if inputtype not in ['int','float','str']:
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'int', 'float', 'str' supported by TKCSpinbox")
		_TKCWidget._checkParameters(inputtype, valrange, vrMandatory=True)

		# Spinbox value is stored in a text variable and casted to input type by function _getWidgetValue()
		self.sbVar = tk.StringVar()

		if type(valrange) is tuple:
			if inputtype == 'str': raise TypeError(valrange)
			self.increment = valrange[2] if len(valrange) == 3 else 1
			tk.Spinbox.__init__(self, parent, from_=valrange[0], to=valrange[1], increment=self.increment, *args, **kwargs)
		elif type(valrange) is list:
			tk.Spinbox.__init__(self, parent, values=valrange, *args, **kwargs)

		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange, readonly=readonly)

		justify = 'left' if inputtype == 'str' else 'right'

		self.config(
			textvariable=self.sbVar,
			justify=justify,
			command=self._update,	# Spinner control pressed
		)

	def _getWidgetValue(self):
		if self.inputtype == 'int':
			return int(self.sbVar.get())
		elif self.inputtype == 'float':
			return float(self.sbVar.get())
		else:
			return self.sbVar.get()
		
	def _setWidgetValue(self, value):
		self.sbVar.set(str(value))


###############################################################################
#
# Create an entry widget
#
# Usage:
#
#   Entry = TKCEntry(master, options, tkinter-Entry-options)
#
# Parameters:
#
#   master - the parent window
#   options - key-value pairs:
#
#     inputtype: Either 'int', 'float' or 'str', default = 'str'
#     valrange:  Tuple with range of valid values. Format is (from, to)
#     initvalue: Initial value
#     onChange:  A function which is called with the current widget value as
#                parameter when either spinner buttons were pressed or ENTER
#                key has been pressed or widget lost the focus.
#
# Methods:
#
#   get()      - Return the current value
#   set(value) - Set widget value
#
###############################################################################

class TKCEntry(_TKCWidget, tk.Entry):

	def __init__(self, parent, id: str, inputtype: Literal['int','float','str','complex'] = 'str',
				valrange: tuple = None, initvalue = None, onChange = None, readonly: bool = False,
				*args, **kwargs):
		# Check parameters
		if inputtype not in ['int','float','str','complex']:
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'int', 'float', 'str', 'complex' supported by TKCEntry")
		_TKCWidget._checkParameters(inputtype, valrange)

		self.enVar = tk.StringVar()

		tk.Entry.__init__(self, parent, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange, readonly=readonly)

		justify = 'left' if inputtype == 'str' else 'right'

		self.config(
			textvariable=self.enVar,
			justify=justify
		)
	
	def _getWidgetValue(self):
		if self.inputtype == 'int':
			return int(self.enVar.get())
		elif self.inputtype == 'float':
			return float(self.enVar.get())
		elif self.inputtype == 'complex':
			return complex(self.enVar.get())
		else:
			return self.enVar.get()
	
	def _setWidgetValue(self, value):
		self.enVar.set(str(value))


###############################################################################
#
# Create read only combobox widget. Strings of selection list are mapped
# to integer numbers
#
# Usage:
#
#   Listbox = TKCListbox(master, options, tkinter-Combobox-options)
#
# Parameters:
#
#   master   - the parent window
#   valrange - List of list entries
#   options  - key-value pairs:
#
#     initvalue: Index of initial value, default = 0
#     onChange:  A function which is called with the current widget value as
#                parameter when either spinner buttons were pressed or ENTER
#                key has been pressed or widget lost the focus.
#
# Methods:
#
#   get()      - Return the current value
#   set(value) - Set widget value
#
###############################################################################

class TKCListbox(_TKCWidget, ttk.Combobox):

	def __init__(self, parent, id: str, inputtype: Literal['int','float','str'] = 'str',
				valrange = None, initvalue = 0, onChange = None, readonly: bool = False,
				*args, **kwargs):
		# Check parameters
		if inputtype not in ['int','float','str']:
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'int', 'float', 'str' supported by TKCListbox")
		_TKCWidget._checkParameters(inputtype, valrange, vrMandatory=True)

		self.lbVar = tk.StringVar()

		ttk.Combobox.__init__(self, parent, state='readonly', values=valrange, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange, readonly=readonly)

		self.config(textvariable=self.lbVar)
		if not self.readonly:
			self.bind("<<ComboboxSelected>>", self._update)

	def _getWidgetValue(self):
		if self.inputtype == 'int':
			return int(self.current())
		elif self.inputtype == 'float':
			return float(self.current())
		else:
			return self.lbVar.get()
	
	def _setWidgetValue(self, value):
		if type(value) is int or type(value) is float:
			self.lbVar.set(self.valrange[value])
		else:
			self.lbVar.set(str(value))

class TKCCheckbox(_TKCWidget, tk.Checkbutton):
		
	def __init__(self, parent, id: str, inputtype: Literal['int'] = 'int',
				valrange = None, initvalue = 0, onChange = None, readonly: bool = False,
				*args, **kwargs):
		# Check parameters
		if inputtype != 'int':
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'int' supported by TKCCheckbox")
		_TKCWidget._checkParameters(inputtype, valrange)

		self.intVar = tk.IntVar()

		tk.Checkbutton.__init__(self, parent, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange, readonly=readonly)

		self.config(
			text=id,
			anchor='w',
			command=self._update,
			variable=self.intVar,
			onvalue=valrange[1],
			offvalue=valrange[0]
		)

	def _getWidgetValue(self):
		return self.intVar.get()
	
	def _setWidgetValue(self, value):
		if type(value) is float or type(value) is int:
			self.intVar.set(int(value))
		else:
			raise TypeError(f"{id}: inputtype={self.inputtype}, value={value}")

class TKCRadiobuttons(_TKCWidget, tk.LabelFrame):

	def __init__(self, parent, id: str, inputtype: Literal['int'] = 'int',
				valrange = None, initvalue = 0, onChange = None, readonly: bool = False,
				*args, **kwargs):
		# Check parameters
		if inputtype != 'int':
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'int' supported by TKCRadiobuttons")
		if type(valrange) is not list or len(valrange) == 0:
			raise TypeError("valrange is not a list or list is empty")
		_TKCWidget._checkParameters(inputtype, valrange)

		self.rbVar = tk.IntVar()

		tk.LabelFrame.__init__(self, parent)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange, readonly=readonly)

		self.config(text=id)
		self.rButtons = []

		r = 0
		for rb in valrange:
			btn = tk.Radiobutton(self, *args, **kwargs)
			btn.config(
				text=rb,
				anchor='w',
				command=self._update,
				variable=self.rbVar,
				value=r
			)
			btn.grid(row=r, column=0)
			self.rButtons.append(btn)
			r += 1

	def _getWidgetValue(self):
		return self.rbVar.get()
	
	def _setWidgetValue(self, value):
		if type(value) is float or type(value) is int:
			self.rbVar.set(int(value))
		else:
			raise TypeError(f"{id}: inputtype={self.inputtype}, value={value}")

class TKCFlags(_TKCWidget, tk.LabelFrame):

	def __init__(self, parent, id: str, inputtype: Literal['bits'] = 'bits',
				valrange = None, initvalue = 0, onChange = None, readonly: bool = False,
				*args, **kwargs):
		# Check parameters
		if inputtype != 'bits':
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'bits' supported by TKCFlags")
		if type(valrange) is not list or len(valrange) == 0:
			raise TypeError("valrange is not a list or list is empty")
		_TKCWidget._checkParameters(inputtype, valrange)

		self.cButtons = []
		self.cVars = []
		for i in range(len(valrange)):
			self.cVars.append(tk.IntVar())

		# Create and initialize widgets
		tk.LabelFrame.__init__(self, parent)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange, readonly=readonly)
		self.config(text=id)

		f = 1
		for c, cb in enumerate(valrange):
			btn = tk.Checkbutton(self, *args, **kwargs)
			btn.config(
				text=cb,
				anchor='w',
				command=self._update,
				variable=self.cVars[c],
				onvalue=f,
				offvalue=0
			)
			btn.grid(row=c, column=0)
			self.cButtons.append(btn)
			f *= 2

	def _getWidgetValue(self):
		value = 0
		for var in self.cVars:
			value += var.get()
		return value
	
	def _setWidgetValue(self, value):
		if type(value) is not float and type(value) is not int:
			raise TypeError(f"{id}: inputtype={self.inputtype}, value={value}")
		v = int(value)
		m = 2**len(self.valrange)
		if v < 0 or v >= m:
			raise ValueError(f"Value {v} out of range (0, {m-1})")
		f = 1
		for var in self.cVars:
			if v & f:
				var.set(f)
			f *= 2

class TKCSlider(_TKCWidget, tk.Scale):
	def __init__(self, parent, id: str, inputtype: Literal['int','float'] = 'int',
				valrange: tuple = (0, 0, 1), initvalue = None, onChange = None, readonly: bool = False, width=50,
				*args, **kwargs):
		# Check parameters
		if inputtype not in ['int','float']:
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'int', 'float' supported by TKCSlider")
		_TKCWidget._checkParameters(inputtype, valrange, vrMandatory=True)

		# Slider value is stored in a text variable and casted to input type by function _getWidgetValue()
		self.slVar = tk.StringVar()

		if type(valrange) is tuple:
			if len(valrange) < 3:
				self.increment = 0.1 if valrange[1]-valrange[0] <= 1 else 1
			else:
				self.increment = valrange[2]
			tk.Scale.__init__(self, parent, orient='horizontal', from_=valrange[0], to=valrange[1], resolution=self.increment, *args, **kwargs)
		else:
			raise TypeError(valrange)

		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange, readonly=readonly)

		self.config(
			variable=self.slVar,
			length=width,
			command=self._update,	# Slider moved
		)

	def _getWidgetValue(self):
		if self.inputtype == 'int':
			return int(self.slVar.get())
		elif self.inputtype == 'float':
			return float(self.slVar.get())
		
	def _setWidgetValue(self, value):
		self.slVar.set(str(value))

class TKCColor(_TKCWidget, tk.Canvas):
	def __init__(self, parent, id: str, inputtype: Literal['str'] = 'str',
				valrange: tuple = ('^#([0-9a-fA-F]{2}){3}$',), initvalue = '#000000', onChange = None, readonly: bool = False,
				width = 50, height = 20, *args, **kwargs):
		# Check parameters
		if inputtype != 'str':
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'str' supported by TKCColortable")
		_TKCWidget._checkParameters(inputtype, valrange, vrMandatory=False)

		self.width = width
		self.height = height

		self.cVar = tk.StringVar()

		tk.Canvas.__init__(self, parent, width=width, height=height)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, initvalue=initvalue, onChange=onChange, readonly=readonly)

		if not self.readonly:
			self.bind("<Button-1>", self._askColor)

	def _str2rgb(self, color) -> tuple[int, int, int]:
		return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
	
	def _setWidgetValue(self, value):
		self.cVar.set(value)

		# Update color rectangle
		self.delete('all')
		self.create_rectangle(0, 0, self.winfo_reqwidth(), self.winfo_reqheight(), fill=value, width=0)
		rgb = self._str2rgb(value)
		txtColor = '#{:02X}{:02X}{:02X}'.format(255-rgb[0], 255-rgb[1], 255-rgb[2])
		self.create_text(5, int(self.winfo_reqheight()/2), text=value, fill=txtColor, anchor='w')

	def _getWidgetValue(self):
		return self.cVar.get()

	# Show color chooser
	def _askColor(self, event = None):
		colorBytes, colorStr = askcolor(color=self.cVar.get())
		if colorStr is not None:
			self._setWidgetValue(colorStr.upper())
			self._update()

		
class TKCColortable(_TKCWidget, tk.Canvas):
	def __init__(self, parent, id: str, inputtype: Literal['tkc'] = 'tkc',
				initvalue = None, onChange = None, readonly: bool = False, width = 50,
				*args, **kwargs):
		# Check parameters
		if inputtype != 'tkc':
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'tkc' supported by TKCColortable")

		self.parent = parent
		self.width  = width
		self.height = 15
		self.cVar   = initvalue
		self.cEdit  = ce.ColorEditor(parent, width=400, height=600)

		tk.Canvas.__init__(self, parent, width=width, height=15)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, initvalue=initvalue, onChange=onChange, readonly=readonly)

		if not self.readonly:
			self.bind("<Button-1>", self._showEditor)

	def _showEditor(self, event = None):
		if self.cEdit.show(self.cVar):
			self._setWidgetValue(self.cEdit.masterSettings['colorTable'])
			self._update()

	def _setWidgetValue(self, value):
		self.cVar = value

		#paletteDef, paletteName = value
		paletteDef = value.getConfig(simple=True)
		colorTable = ce.ColorEditor.createPaletteFromDef(paletteDef)
		width  = self.winfo_reqwidth()
		height = self.winfo_reqheight()

		# Delete all color rectangles
		self.delete('all')

		if paletteDef['size'] > width:
			d = paletteDef['size']/width
			t = 0
			for x in range(width):
				idx = int(t)
				color = '#{:02X}{:02X}{:02X}'.format(
					int(colorTable[idx][0]*255), int(colorTable[idx][1]*255), int(colorTable[idx][2]*255)
				)
				self.create_line(x, 0, x, height, fill=color)
				t += d
		else:
			d = int(width/paletteDef['size'])
			x = 0
			for i in range(paletteDef['size']):
				color = '#{:02X}{:02X}{:02X}'.format(
					int(colorTable[i][0]*255), int(colorTable[i][1]*255), int(colorTable[i][2]*255)
				)
				self.create_rectangle(int(x), 0, int(x+d), height, fill=color, width=0)
				x += d

	def _getWidgetValue(self):
		return self.cVar

class TKCList(_TKCWidget, tk.Entry):
	def __init__(self, parent, id: str, inputtype: Literal['list'] = 'list',
				initvalue = [], onChange = None, readonly: bool = False, width = 50,
				*args, **kwargs):
		# Check parameters
		if inputtype != 'list':
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'list' supported by TKCList")

		self.parent = parent
		self.lVar   = initvalue
		self.sVar   = tk.StringVar()

		# Initialize widget
		tk.Entry.__init__(self, parent, width=width, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, initvalue=initvalue, onChange=onChange, readonly=readonly)

		# Configure the widget
		state = 'readonly' if readonly else 'normal'
		self.config(
			textvariable=self.sVar,
			justify='left',
			state=state
		)

	def _setWidgetValue(self, value):
		self.lVar = value
		self.sVar.set(str(value))

	def _getWidgetValue(self):
		return self.lVar
	
class TKCDialog(_TKCWidget, tk.Entry):
	def __init__(self, parent, id: str, inputtype: Literal['tkc'] = 'tkc',
				initvalue = None, onChange = None, readonly: bool = True, width = 30,
				*args, **kwargs):
		# Check parameters
		if inputtype != 'tkc':
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'tkc' supported by TKCDialog")

		self.parent = parent
		self.dVar   = initvalue
		self.sVar   = tk.StringVar()

		tk.Entry.__init__(self, parent, width=width, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, initvalue=initvalue, onChange=onChange, readonly=readonly)

		state = 'readonly' if readonly else 'normal'
		self.config(
			textvariable=self.sVar,
			justify='left',
			state=state
		)

	# Set new TKConfigure object as value
	def _setWidgetValue(self, value):
		self.dVar = value
		valueList = value.getValues()
		self.sVar.set(str(valueList))

	def _getWidgetValue(self):
		return self.dVar