import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal


###############################################################################
# Base class for all TKC widgets
###############################################################################

class _TKCWidget:

	_WIDGETS_ = [ 'TKCSpinbox', 'TKCEntry', 'TKCListbox', 'TKCCheckbox' ]

	def __init__(self, parent, id: str, inputType: Literal['int','float','str'] = 'str', valRange: tuple = None, initValue = None, onChange = None):
		self.parent    = parent
		self.id        = id
		self.inputType = inputType
		self.onChange  = onChange
		self.valRange  = valRange
		self.textVar   = tk.StringVar()

		# All child widget must support 'textvariable=' attribute
		self.config(
			textvariable=self.textVar
		)

		# Set var and textVar to initial value
		if not self._validate(initValue): raise ValueError(initValue)
		self.initValue = initValue
		self.set(initValue)

		if onChange is not None:
			self.bind('<FocusOut>', self._update)
			self.bind('<Return>', self._update)

	@staticmethod
	def _checkParameters(inputType: str, valRange: list | tuple, vrMandatory: bool = False):
		if inputType is None: raise ValueError('inputType == None')
		if inputType not in ['int', 'float', 'str']: raise ValueError(inputType)
		
		if valRange is None:
			if vrMandatory: raise ValueError('valRange == None')
			return
		
		if inputType == 'str':
			if type(valRange) != 'list': raise TypeError('valRange')
			if len(valRange) == 0: raise ValueError('valRange == []')
		elif type(valRange) == 'tuple' and (len(valRange) < 2 or len(valRange) > 3):
			raise ValueError(valRange)
		elif type(valRange) == 'list' and len(valRange) == 0:
			raise ValueError('valRange == []')
		elif type(valRange) != 'tuple' and type(valRange) != 'list':
			raise TypeError('valRange', valRange, type(valRange))

	def _validate(self, value) -> bool:
		return True
	
	def _checkRange(self, value) -> bool:
		if self.valRange is None or len(self.valRange) < 2: return True
		if type(self.valRange) == 'tuple':
			if self.inputType == 'int':
				return self.valRange[0] <= int(value) <= self.valRange[1]
			elif self.inputType == 'float':
				return self.valRange[0] <= float(value) <= self.valRange[1]
			else:
				return False
		elif type(self.valRange) == 'list':
			return value in self.valRange

	def _validate(self, value) -> bool:
		try:
			if self.inputType == 'int':
				v = int(value)
			elif self.inputType == 'float':
				v = float(value)
			return True
		except ValueError:
			return False
		
	def _update(self, event = None):
		value = self._getWidgetValue()
		if self._checkRange(value):
			# Inform app about new widget value
			if value != self.var:
				self.var = value
				self.onChange(self.id, value)
		elif self.initValue is not None:
			self.set(self.initValue)

	# Return the current value of a widget. By default this is the value of textVar.
	# Can be overwritten in child classes to return a different value, i.e. the index
	# of the selected entry of a TKCListbox.
	# This function is called by _update() to retrieve the new widget value.
	def _getWidgetValue(self):
		if self.inputType == 'int':
			return int(self.textVar.get())
		elif self.inputType == 'float':
			return float(self.textVar.get())
		else:
			return self.textVar.get()
	
	def _getWidgetString(self):
		return self.textVar.get()

	def get(self):
		return self.var
	
	def getStr(self) -> str:
		return str(self.var)
	
	def set(self, value):
		if self._validate(value) and self._checkRange(value):
			self.var = value
			self.textVar.set(str(value))
		else:
			raise ValueError(value)

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
		_TKCWidget._checkParameters(inputType, valRange, vrMandatory=True)

		if type(valRange) == 'tuple':
			if inputType == 'str': raise TypeError(valRange)
			self.increment = valRange[2] if len(valRange) == 3 else 1
			tk.Spinbox.__init__(self, parent, from_=valRange[0], to=valRange[1], increment=self.increment, *args, **kwargs)
		elif type(valRange) == 'list':
			tk.Spinbox.__init__(self, parent, values=valRange, *args, **kwargs)

		_TKCWidget.__init__(self, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(
			command=self._update,	# Spinner control pressed
		)


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
		_TKCWidget._checkParameters(inputType, valRange)

		tk.Entry.__init__(self, parent, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)


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
#   master - the parent window
#
#   valRange - List of list entries
#
#   options - key-value pairs:
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
		_TKCWidget._checkParameters(inputType, valRange, vrMandatory=True)

		ttk.Combobox.__init__(self, parent, state='readonly', values=valRange, *args, **kwargs)
		_TKCWidget.__init__(self, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.bind("<ComboboxSelected>", self._update)

	def _getWidgetValue(self):
		return self.current()
	
	def _checkRange(self, value):
		if type(value) == int:
			return value >= 0 and value < len(self.valRange)
		elif type(value) == float:
			return int(value) >= 0 and int(value) < len(self.valRange)
		elif type(value) == str:
			idx = self.valRange.index(value)	# Raise ValueError if value is not in valRange
			return True
		else:
			raise ValueError(value)


class TKCCheckbox(_TKCWidget, tk.Checkbutton):
		
	def __init__(self, parent, id: str, inputType: Literal['int','float','str'] = 'str',
				valRange = None, initValue = False, onChange = None, *args, **kwargs):
		# Check parameters
		_TKCWidget._checkParameters(inputType, valRange)

		tk.Checkbutton.__init__(self, parent, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(
			command=self._update
		)

