import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal


###############################################################################
# Base class for all TKC widgets
###############################################################################

class _TKCWidget:

	_WIDGETS_ = [ 'TKCSpinbox', 'TKCEntry', 'TKCListbox', 'TKCCheckbox', 'TKCRadiobuttons', 'TKCFlags' ]

	def __init__(self, parent, id: str, inputtype: Literal['int','float','str','bits','complex'] = 'str',
			  valrange: tuple = None, initvalue = None, onChange = None):
		self.parent    = parent
		self.id        = id
		self.inputtype = inputtype
		self.onChange  = onChange
		self.valrange  = valrange

		# Set widget to initial value
		if not self._validate(initvalue):
			raise ValueError(f"{id}: inputtype={inputtype}, initvalue={initvalue}, valrange={valrange}")
		self.initvalue = initvalue
		self.set(initvalue)

		if onChange is not None:
			self.bind('<FocusOut>', self._update)
			self.bind('<Return>', self._update)

	@staticmethod
	def _checkParameters(inputtype: str, valrange: list | tuple, vrMandatory: bool = False):
		if inputtype is None: raise ValueError('inputtype == None')
		if inputtype not in ['int', 'float', 'str', 'bits', 'complex']:
			raise ValueError(f"Invalid inputtype {inputtype}")
		
		if valrange is None:
			if vrMandatory: raise ValueError('valrange == None')
			return
		
		if inputtype == 'str':
			if type(valrange) is not list: raise TypeError('valrange')
			if len(valrange) == 0: raise ValueError('valrange == []')
		elif type(valrange) is tuple and (len(valrange) < 2 or len(valrange) > 3):
			raise ValueError(valrange)
		elif type(valrange) is list and len(valrange) == 0:
			raise ValueError('valrange == []')
		elif type(valrange) is not tuple and type(valrange) is not list:
			raise TypeError('valrange', valrange, type(valrange))

	# Check if value is in valrange
	def _checkRange(self, value) -> bool:
		if self.valrange is None or len(self.valrange) < 2: return True
		if type(self.valrange) is tuple:
			if self.inputtype in ['int','float','complex']:
				return self.valrange[0] <= value <= self.valrange[1]
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
	
	# Called when widget value has been changed
	def _update(self, event = None):
		value = self._getWidgetValue()
		if self._validate(value) and self._checkRange(value):
			if value != self.var:
				# Inform app about new widget value
				self.var = value
				self.onChange(self.id, value)
			return

		# on error set widget value to initvalue
		if self.initvalue is not None:
			self.set(self.initvalue)

	# Return the current value of a widget. By default this function has no implementation.
	# Function must be overwritten in child classes to return a valid value with the
	# appropriate type, i.e. the index of the selected entry of a TKCListbox.
	# This function is called by _update() to retrieve the current widget value.
	def _getWidgetValue(self):
		pass
	
	# Set the widget value. By default this function has no implementation.
	# Function must be overwritten in child classed to set a widget to the specified value.
	# This function is called by set() to update a widget value.
	def _setWidgetValue(self, value):
		pass

	def get(self):
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
				valrange: tuple = (0, 0, 1), initvalue = None, onChange = None, *args, **kwargs):
		# Check parameters
		if inputtype not in ['int','float','str']:
			raise ValueError(f"{id}: Invalid inputtype {inputtype}")
		_TKCWidget._checkParameters(inputtype, valrange, vrMandatory=True)

		# Spinbox value is stored in a text variable and casted to input type by function _getWidgetValue()
		self.sbVar = tk.StringVar()

		if type(valrange) is tuple:
			if inputtype == 'str': raise TypeError(valrange)
			self.increment = valrange[2] if len(valrange) == 3 else 1
			tk.Spinbox.__init__(self, parent, from_=valrange[0], to=valrange[1], increment=self.increment, *args, **kwargs)
		elif type(valrange) is list:
			tk.Spinbox.__init__(self, parent, values=valrange, *args, **kwargs)

		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange)

		self.config(
			textvariable=self.sbVar,
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
				valrange: tuple = None, initvalue = None, onChange = None, *args, **kwargs):
		# Check parameters
		if inputtype not in ['int','float','str','complex']:
			raise ValueError(f"{id}: Invalid inputtype {inputtype}")
		_TKCWidget._checkParameters(inputtype, valrange)

		self.enVar = tk.StringVar()

		tk.Entry.__init__(self, parent, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange)

		self.config(
			textvariable=self.enVar
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
				valrange = None, initvalue = 0, onChange = None, *args, **kwargs):
		# Check parameters
		if inputtype not in ['int','float','str']:
			raise ValueError(f"{id}: Invalid inputtype {inputtype}")
		_TKCWidget._checkParameters(inputtype, valrange, vrMandatory=True)

		self.lbVar = tk.StringVar()

		ttk.Combobox.__init__(self, parent, state='readonly', values=valrange, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange)

		self.config(textvariable=self.lbVar)
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
				valrange = None, initvalue = 0, onChange = None, *args, **kwargs):
		# Check parameters
		if inputtype != 'int':
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'int' supported by TKCCheckbox")
		_TKCWidget._checkParameters(inputtype, valrange)

		self.intVar = tk.IntVar()

		tk.Checkbutton.__init__(self, parent, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange)

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
				valrange = None, initvalue = 0, onChange = None, *args, **kwargs):
		# Check parameters
		if inputtype != 'int':
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'int' supported by TKCRadiobuttons")
		if type(valrange) is not list or len(valrange) == 0:
			raise TypeError("valrange is not a list or list is empty")
		_TKCWidget._checkParameters(inputtype, valrange)

		self.rbVar = tk.IntVar()

		tk.LabelFrame.__init__(self, parent)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange)

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
				valrange = None, initvalue = 0, onChange = None, *args, **kwargs):
		# Check parameters
		if inputtype != 'bits':
			raise ValueError(f"{id}: Invalid inputtype {inputtype}. Only 'bits' supported by TKCFlags")
		if type(valrange) is not list or len(valrange) == 0:
			raise TypeError("valrange is not a list or list is empty")
		_TKCWidget._checkParameters(inputtype, valrange)

		self.cVars = []
		self.cButtons = []

		# Create and initialize widgets
		tk.LabelFrame.__init__(self, parent)
		_TKCWidget.__init__(self, parent, id, inputtype=inputtype, valrange=valrange, initvalue=initvalue, onChange=onChange)
		self.config(text=id)

		f = 1
		for c, cb in enumerate(valrange):
			self.cVars.append(tk.IntVar())
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
		print(f"_getWidgetValue = {value}")
		return value
	
	def _setWidgetValue(self, value):
		if type(value) is not float and type(value) is not int:
			raise TypeError(f"{id}: inputtype={self.inputtype}, value={value}")
		v = int(value)
		m = 2**len(self.valrange)
		if v < 0 or v >= m:
			raise ValueError(f"Value {v} out of range (0, {m})")
		f = 1
		for c,var in enumerate(self.cVars):
			if v & f: var.set(f)
			f *= 2
