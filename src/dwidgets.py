import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal

###############################################################################
# Base class for numeric widgets
###############################################################################

class _NumWidget:

	def __init__(self, parent, id: str = '', inputType: Literal['int', 'float'] = 'int', valRange: tuple = None, initValue = None, onChange = None, *args, **kwargs):

		self.id        = id
		self.type      = inputType
		self.valRange  = valRange
		self.initValue = initValue
		self.onChange  = onChange

		if initValue is not None and not self._validate(initValue):
			initValue = None

		"""
		if inputType == 'int':
			self.bindVar = tk.IntVar()
		elif inputType == 'float':
			self.bindVar = tk.DoubleVar()
		"""
		self.bindVar = tk.StringVar()
		self.set(initValue)

		self.config(
			textvariable=self.bindVar
		)

		if onChange is not None:
			self.bind('<FocusOut>', self._onEvent)
			self.bind('<Return>', self._onEvent)

	def get(self):
		value = self.bindVar.get()
		if self.type == 'int':
			return int(value)
		elif self.type == 'float':
			return float(value)
		else:
			raise ValueError(value)
	
	def set(self, value: int | float) -> bool:
		if (type(value) == int or type(value) == float) and self._checkRange(value):
			self.bindVar.set(str(value))
			return True
		else:
			return False

	def _checkRange(self, value: int | float) -> bool:
		if self.valRange is None:
			return True
		else:
			return self.valRange[0] <= value <= self.valRange[1]

	def _validate(self, value: int | float | str) -> bool:
		if type(value) is not str: value = str(value)
		try:
			if self.type == 'int':
				v = int(value)
			elif self.type == 'float':
				v = float(value)
			else:
				return False
		except ValueError:
			return False
		
		return True
	
	# Called when either widget lost keyboard focus or ENTER key has been pressed
	def _onEvent(self, event = None):
		value = self.get()
		if self._checkRange(value)):
			self.onChange(self.id, value)
		elif self.initValue is not None:
			self.set(self.initValue)

###############################################################################
#
# Create numeric Spinbox widget
#
# Usage:
#
#   Spinbox = NumSpinbox(master, options, tkinter-Spinbox-options)
#
# Parameters:
#
#   master - the parent window
#   options - key-value pairs:
#
#     inputType: Either 'int' or 'float', default = 'int'
#     valRange:  Range of valid values. Format is (from, to [,increment])
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

class NumSpinbox(_NumWidget, tk.Spinbox):

	def __init__(self, parent, id: str ='', inputType: Literal['int', 'float'] = 'int', valRange: tuple = None, initValue = None, onChange = None, *args, **kwargs):
		tk.Spinbox.__init__(self, parent, from_=valRange[0], to=valRange[1], *args, **kwargs)
		_NumWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(
			command=self._onEvent,
			increment = valRange[2] if len(valRange) > 2 else 1,
			validate='key',
			validatecommand=(parent.register(self._validate), '%P')
		)



###############################################################################
#
# Create numeric entry widget
#
# Usage:
#
#   Entry = NumEntry(master, options, tkinter-Entry-options)
#
# Parameters:
#
#   master - the parent window
#   options - key-value pairs:
#
#     inputType: Either 'int' or 'float', default = 'int'
#     valRange:  Range of valid values. Format is (from, to)
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

class NumEntry(_NumWidget, tk.Entry):
		
	def __init__(self, parent, id: str = '', inputType: Literal['int', 'float'] = 'int', valRange: tuple = None, initValue = None, onChange = None, *args, **kwargs):
		tk.Spinbox.__init__(self, parent, *args, **kwargs)
		_NumWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(
			validate='key',
			validatecommand=(parent.register(self._validate), '%P')
		)

###############################################################################
#
# Create numeric combobox widget. Strings of selection list are mapped
# to integer numbers
#
# Usage:
#
#   Combobox = NumCombobox(master, options, tkinter-Combobox-options)
#
# Parameters:
#
#   master - the parent window
#   options - key-value pairs:
#
#     inputType: Either 'int' or 'float', default = 'int'
#     valRange:  List entries (strings)
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

class NumCombobox(_NumWidget, ttk.Combobox):

	def __init__(self, parent, id: str = '', inputType: Literal['int', 'float'] = 'int', valRange: tuple = None, initValue = None, onChange = None, *args, **kwargs):
		ttk.Combobox.__init__(self, parent, state='readonly', values=valRange, *args, **kwargs)
		_NumWidget.__init__(self, parent, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.bind("<<ComboboxSelected>>", self._onSelected)

	def _onSelected(self, event=None):
		idx = self.current()
		self.bindVar.set(idx)
		self._onEvent()

	def _checkRange(self, value: int | float) -> bool:
		if self.valRange is None:
			return True
		else:
			return 0 <= value < len(self.valRange)

	def set(self, value: int | float) -> bool:
		if value is None and len(self.valRange) > 0:
			self.bindVar.set(0)
			self.current(newindex=0)
		elif (type(value) == int or type(value) == float) and self._checkRange(value):
			self.bindVar.set(value)
			self.current(newIndex=value)
			return True
		elif type(value) == str:
			idx = self.valRange.index(value)
			self.bindVar.set(idx)
			self.current(newindex=idx)
		else:
			return False

class NumCheckbox(_NumWidget, tk.Checkbutton):
		
	def __init__(self, parent, id: str = '', inputType: Literal['int', 'float'] = 'int', initValue = None, onChange = None, *args, **kwargs):
		tk.Checkbutton.__init__(self, parent, *args, **kwargs)
		_NumWidget.__init__(self, parent, id, inputType=inputType, initValue=initValue, onChange=onChange)

		self.config(
			command=self._onEvent
		)

