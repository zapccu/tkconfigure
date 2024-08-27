import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal


###############################################################################
# Base class for all TKC widgets
###############################################################################

class _TKCWidget:

	_WIDGETS_ = [ 'TKCSpinbox', 'TKCEntry', 'TKCListbox', 'TKCCheckbox', 'TKCRadiobuttons', 'TKCFlags' ]

	def __init__(self, parent, id: str, inputType: Literal['int','float','str','bits'] = 'str',
			  valRange: tuple = None, initValue = None, onChange = None):
		self.parent    = parent
		self.id        = id
		self.inputType = inputType
		self.onChange  = onChange
		self.valRange  = valRange

		# Set widget to initial value
		if not self._validate(initValue):
			raise ValueError(f"{id}: inputType={inputType}, initValue={initValue}, valRange={valRange}")
		self.initValue = initValue
		self.set(initValue)

		if onChange is not None:
			self.bind('<FocusOut>', self._update)
			self.bind('<Return>', self._update)

	@staticmethod
	def _checkParameters(inputType: str, valRange: list | tuple, vrMandatory: bool = False):
		if inputType is None: raise ValueError('inputType == None')
		if inputType not in ['int', 'float', 'str', 'bits']: raise ValueError(inputType)
		
		if valRange is None:
			if vrMandatory: raise ValueError('valRange == None')
			return
		
		if inputType == 'str':
			if type(valRange) is not list: raise TypeError('valRange')
			if len(valRange) == 0: raise ValueError('valRange == []')
		elif type(valRange) is tuple and (len(valRange) < 2 or len(valRange) > 3):
			raise ValueError(valRange)
		elif type(valRange) is list and len(valRange) == 0:
			raise ValueError('valRange == []')
		elif type(valRange) is not tuple and type(valRange) is not list:
			raise TypeError('valRange', valRange, type(valRange))

	def _checkRange(self, value) -> bool:
		if self.valRange is None or len(self.valRange) < 2: return True
		if type(self.valRange) is tuple:
			if self.inputType == 'int':
				return self.valRange[0] <= int(value) <= self.valRange[1]
			elif self.inputType == 'float':
				return self.valRange[0] <= float(value) <= self.valRange[1]
			else:
				return False
		elif type(self.valRange) is list:
			if self.inputType == 'str':
				return value in self.valRange
			elif self.inputType == 'bits':
				return 0 <= int(value) < 2**len(self.valRange)
			else:
				return 0 <= int(value) < len(self.valRange)

	def _validate(self, value) -> bool:
		if self.inputType == 'str' and type(self.valRange) is list:
			return value in self.valRange		
		try:
			if self.inputType == 'int' or self.inputType == 'bits':
				v = int(value)
			elif self.inputType == 'float':
				v = float(value)
			return True
		except ValueError:
			return False
		
	def _update(self, event = None):
		value = self._getWidgetValue()
		if self._validate(value) and self._checkRange(value):
			if value != self.var:
				# Inform app about new widget value
				self.var = value
				self.onChange(self.id, value)
			return

		# on error set widget value to initValue
		if self.initValue is not None:
			self.set(self.initValue)

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
#   Spinbox = TKCSpinbox(master, valRange=<list>|<tuple>, options,
#                        tkinter-Spinbox-options)
#
# Parameters:
#
#   master - the parent window
#
#   valRange - List with valid values or tuple with range of values.
#              Tuple with range is only allowed for inputType 'int'
#              or 'float'. Format of tuple: (from, to [,increment])
#
#   options - key-value pairs:
#
#     inputType: Either 'int', 'float' or 'str', default = 'int'
#     initValue: Initial value
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

	def __init__(self, parent, id: str, inputType: Literal['int','float','str'] = 'int',
				valRange: tuple = (0, 0, 1), initValue = None, onChange = None, *args, **kwargs):
		# Check parameters
		if inputType not in ['int','float','str']:
			raise ValueError(f"{id}: Invalid inputType {inputType}")
		_TKCWidget._checkParameters(inputType, valRange, vrMandatory=True)

		# Spinbox value is stored in a text variable and casted to input type by function _getWidgetValue()
		self.sbVar = tk.StringVar()

		if type(valRange) is tuple:
			if inputType == 'str': raise TypeError(valRange)
			self.increment = valRange[2] if len(valRange) == 3 else 1
			tk.Spinbox.__init__(self, parent, from_=valRange[0], to=valRange[1], increment=self.increment, *args, **kwargs)
		elif type(valRange) is list:
			tk.Spinbox.__init__(self, parent, values=valRange, *args, **kwargs)

		_TKCWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(
			textvariable=self.sbVar,
			command=self._update,	# Spinner control pressed
		)

	def _getWidgetValue(self):
		if self.inputType == 'int':
			return int(self.sbVar.get())
		elif self.inputType == 'float':
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
#     inputType: Either 'int', 'float' or 'str', default = 'str'
#     valRange:  Tuple with range of valid values. Format is (from, to)
#     initValue: Initial value
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

	def __init__(self, parent, id: str, inputType: Literal['int','float','str'] = 'str',
				valRange: tuple = None, initValue = None, onChange = None, *args, **kwargs):
		# Check parameters
		if inputType not in ['int','float','str']:
			raise ValueError(f"{id}: Invalid inputType {inputType}")
		_TKCWidget._checkParameters(inputType, valRange)

		self.enVar = tk.StringVar()

		tk.Entry.__init__(self, parent, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(
			textvariable=self.enVar
		)
	
	def _getWidgetValue(self):
		if self.inputType == 'int':
			return int(self.enVar.get())
		elif self.inputType == 'float':
			return float(self.enVar.get())
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
#   valRange - List of list entries
#   options  - key-value pairs:
#
#     initValue: Index of initial value, default = 0
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

	def __init__(self, parent, id: str, inputType: Literal['int','float','str'] = 'str',
				valRange = None, initValue = 0, onChange = None, *args, **kwargs):
		# Check parameters
		if inputType not in ['int','float','str']:
			raise ValueError(f"{id}: Invalid inputType {inputType}")
		_TKCWidget._checkParameters(inputType, valRange, vrMandatory=True)

		self.lbVar = tk.StringVar()

		ttk.Combobox.__init__(self, parent, state='readonly', values=valRange, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(textvariable=self.lbVar)
		self.bind("<<ComboboxSelected>>", self._update)

	def _getWidgetValue(self):
		if self.inputType == 'int':
			return int(self.current())
		elif self.inputType == 'float':
			return float(self.current())
		else:
			return self.lbVar.get()
	
	def _setWidgetValue(self, value):
		if type(value) is int or type(value) is float:
			self.lbVar.set(self.valRange[value])
		else:
			self.lbVar.set(str(value))

class TKCCheckbox(_TKCWidget, tk.Checkbutton):
		
	def __init__(self, parent, id: str, inputType: Literal['int'] = 'int',
				valRange = None, initValue = 0, onChange = None, *args, **kwargs):
		# Check parameters
		if inputType != 'int':
			raise ValueError(f"{id}: Invalid inputType {inputType}. Only 'int' supported by TKCCheckbox")
		_TKCWidget._checkParameters(inputType, valRange)

		self.intVar = tk.IntVar()

		tk.Checkbutton.__init__(self, parent, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(
			text=id,
			anchor='w',
			command=self._update,
			variable=self.intVar,
			onvalue=valRange[1],
			offvalue=valRange[0]
		)

	def _getWidgetValue(self):
		return self.intVar.get()
	
	def _setWidgetValue(self, value):
		if type(value) is float or type(value) is int:
			self.intVar.set(int(value))
		else:
			raise TypeError(f"{id}: inputType={self.inputType}, value={value}")

class TKCRadiobuttons(_TKCWidget, tk.LabelFrame):

	def __init__(self, parent, id: str, inputType: Literal['int'] = 'int',
				valRange = None, initValue = 0, onChange = None, *args, **kwargs):
		# Check parameters
		if inputType != 'int':
			raise ValueError(f"{id}: Invalid inputType {inputType}. Only 'int' supported by TKCRadiobuttons")
		if type(valRange) is not list or len(valRange) == 0:
			raise TypeError("valRange is not a list or list is empty")
		_TKCWidget._checkParameters(inputType, valRange)

		self.rbVar = tk.IntVar()

		tk.LabelFrame.__init__(self, parent)
		_TKCWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(text=id)
		self.rButtons = []

		r = 0
		for rb in valRange:
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
			raise TypeError(f"{id}: inputType={self.inputType}, value={value}")

class TKCFlags(_TKCWidget, tk.LabelFrame):

	def __init__(self, parent, id: str, inputType: Literal['bits'] = 'bits',
				valRange = None, initValue = 0, onChange = None, *args, **kwargs):
		# Check parameters
		if inputType != 'bits':
			raise ValueError(f"{id}: Invalid inputType {inputType}. Only 'bits' supported by TKCFlags")
		if type(valRange) is not list or len(valRange) == 0:
			raise TypeError("valRange is not a list or list is empty")
		_TKCWidget._checkParameters(inputType, valRange)

		self.cVars = []
		self.cButtons = []

		# Create and initialize widgets
		tk.LabelFrame.__init__(self, parent)
		_TKCWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)
		self.config(text=id)

		f = 1
		for c, cb in enumerate(valRange):
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
			raise TypeError(f"{id}: inputType={self.inputType}, value={value}")
		v = int(value)
		m = 2**len(self.valRange)
		if v < 0 or v >= m:
			raise ValueError(f"Value {v} out of range (0, {m})")
		f = 1
		for c,var in enumerate(self.cVars):
			if v & f: var.set(f)
			f *= 2
