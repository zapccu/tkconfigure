import tkinter as tk
import tkinter.ttk as ttk
from typing import Literal

widgets = [ 'TKCNumSpinbox', 'TKCTxtSpinbox', 'TKCNumEntry', 'TKCListBox', 'TKCCheckbox' ]

###############################################################################
# Base class for all TKC widgets
###############################################################################

class _TKCWidget:

	def __init__(self, parent, id: str, valRange: tuple = None, initValue = None, onChange = None):
		self.parent   = parent
		self.id       = id
		self.onChange = onChange
		self.valRange = valRange
		self.textVar  = tk.StringVar()

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

	def _validate(self, value) -> bool:
		return True
	
	def _checkRange(self, value) -> bool:
		return True

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
# Base class for numeric widgets
###############################################################################

class _TKCNumWidget(_TKCWidget):

	def __init__(self, parent, id: str, inputType: Literal['int','float'] = 'int', valRange: tuple = None, initValue = None, onChange = None, *args, **kwargs):
		
		super().__init__(parent, id, valRange=valRange, initValue=initValue, onChange=onChange)

		self.inputType = inputType
		self.increment = valRange[2] if valRange is not None and len(valRange) else 1

		self.config(
			validate='key',
			validatecommand=(parent.register(self._validate), '%P')
		)

	def _getWidgetValue(self):
		if self.inputType == 'int':
			return int(self.textVar.get())
		else:
			return float(self.textVar.get())
		
	def _checkRange(self, value) -> bool:
		if self.valRange is None or len(self.valRange) < 2:
			return True
		else:
			return self.valRange[0] <= value <= self.valRange[1]

	def _validate(self, value) -> bool:
		try:
			if self.inputType == 'int':
				v = int(value)
			else:
				v = float(value)
			return True
		except ValueError:
			return False

###############################################################################
#
# Create numeric Spinbox widget
#
# Usage:
#
#   Spinbox = TKCNumSpinbox(master, options, tkinter-Spinbox-options)
#
# Parameters:
#
#   master - the parent window
#   options - key-value pairs:
#
#     inputType: Either 'int' or 'float', default = 'int'
#     valRange:  Range of valid values. Format is (from, to [,increment=1])
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

class TKCNumSpinbox(_TKCNumWidget, tk.Spinbox):

	def __init__(self, parent, id: str, inputType: Literal['int', 'float'] = 'int',
				valRange: tuple = (0, 0, 1), initValue = None, onChange = None, *args, **kwargs):
		
		tk.Spinbox.__init__(self, parent, from_=valRange[0], to=valRange[1], *args, **kwargs)
		_TKCNumWidget.__init__(self, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(
			command=self._update,			# Spinner control pressed
			increment = self.increment
		)

class TKCTxtSpinbox(_TKCWidget, tk.Spinbox):

	def __init__(self, parent, id: str, valRange: tuple,
				initValue = None, onChange = None, *args, **kwargs):
		
		tk.Spinbox.__init__(self, parent, values=valRange, *args, **kwargs)
		_TKCWidget.__init__(self, id, valRange=valRange, initValue=initValue, onChange=onChange)

		self.config(
			command=self._update,			# Spinner control pressed
			increment = self.increment
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

class TKCNumEntry(_TKCNumWidget, tk.Entry):
		
	def __init__(self, parent, id: str, inputType: Literal['int', 'float'] = 'int',
				valRange: tuple = None, initValue = None, onChange = None, *args, **kwargs):
		
		tk.Entry.__init__(self, parent, *args, **kwargs)
		_TKCNumWidget.__init__(self, id, inputType=inputType, valRange=valRange, initValue=initValue, onChange=onChange)


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
#   options - key-value pairs:
#
#     valRange:  Tuple of list entries (strings)
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

	def __init__(self, parent, id: str, valRange: tuple, initValue = 0, onChange = None, *args, **kwargs):

		ttk.Combobox.__init__(self, parent, state='readonly', values=valRange, *args, **kwargs)
		_TKCWidget.__init__(self, id, valRange=valRange, initValue=initValue, onChange=onChange)

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
		
	def __init__(self, parent, id: str, initValue = False, onChange = None, *args, **kwargs):
		tk.Checkbutton.__init__(self, parent, *args, **kwargs)
		_TKCWidget.__init__(self, parent, id, initValue=initValue, onChange=onChange)

		self.config(
			command=self._update
		)

