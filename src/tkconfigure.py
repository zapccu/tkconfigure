import tkinter as tk
import json
from tkcwidgets import *
from tkcwidgets import _TKCWidget

from typing import Literal

###############################################################################
#
# Create configuration objects
#
# Usage:
#
#   Config = TKConfigure(parameterDefinition , configValues)
#
# Parameters:
#
#   parameterDefinition - Dictionary with definition of config parameters
#   configValues -        Dictionary with parameter values
#
# Parameter definition dictionary:
#
# {
#    "group-name": {
#       "parameter-name": {
#          "attribute-name": attribute-value,
#          ... # Further attributes
#       },
#       ... # Further parameter definitions
#    },
#    ... # Further groups, use "" for no-group
# }
#
# Parameter attributes:
#
#   inputtype -  The input type, either 'int', 'float', 'str', 'bits', 'complex'
#                default = 'str'
#   initvalue -  Initial parameter value, type must match inputtype,
#                default = None
#   valrange -   Depends on inputtype, default = None (no input validation)
#                  'str': list of valid strings
#                  'int','float': tuple with value range (from, to [,increment])
#                  'bits': list of string representing the bits (index 0 = bit 0)
#   widget -     The type of the input widget, either 'TKCEntry', 'TKCSpinbox',
#                'TKCCheckbox', 'TKCListbox', 'TKCRadiobuttons', 'TKCFlags'.
#                Default = 'TKCEntry'
#   label -      Text placed in front of the widget, default = '' (no text)
#   width -      Width of the input widget in characters, default = 20
#   widgetattr - Dictionary with additional TKInter widget attributes,
#                default = {}
#
# Parameter value dictionary:
#
# {
#    "parameter-name": {
#       "value": parameter-value
#    },
#    ... # Further parameter values
# }
#
###############################################################################

class TKConfigure:

	def __init__(self, parameterdefinition: dict | None = None, config: dict | None = None):

		# Input types:
		self.types = { 'int': int, 'float': float, 'str': str, 'bits': int, 'complex': complex }

		# Allowed parameter definition keys. Can be enhanced by method addKey()
		self.attributes = [ 'inputtype', 'valrange', 'initvalue', 'widget', 'label', 'width', 'widgetattr' ]

		# Default values for parameter attributes
		self.defaults = {
			'inputtype':  'str',
			'valrange':   None,
			'initvalue':  '',
			'widget':     'TKCEntry',
			'label':      '',
			'width':      20,
			'widgetattr': {}
		}

		# Parameter ids: ['<id>'] -> <group>
		self.idList = {}
		
		# Parameter definition: ['<group>']['<id>'] -> <definition>
		if parameterdefinition is None:
			self.parDef = {}
			self.config = {}
		else:
			self.setParameterDefinition(parameterdefinition, config)

		# Created widgets: ['<id>'] -> <widget>
		self.widget = {}

		self.notifyChange = None
		self.notifyError  = None

	def notify(self, onchange=None, onerror=None):
		self.notifyChange = onchange
		self.notifyError  = onerror

	# Validate group and/or id
	def _validateGroupId(self, group: str | None = None, id: str | None = None):
		if group is not None and group not in self.parDef:
			raise ValueError(f"Unknown parameter group {group}")
		if id is not None and id not in self.idList:
			raise ValueError(f"Unknown parameter id {id}")
		
	# Validate parameter defintion
	def _validateParDef(self, id: str, parCfg: dict):
		# Validate attributes
		for a in parCfg:
			if a not in self.attributes:
				raise ValueError(f"Unknown attribute {a} for parameter {id}")
			
		inputtype = parCfg['inputtype']
		initvalue = parCfg['initvalue']
		valrange  = parCfg['valrange']

		# Validate the inputtype
		if inputtype not in self.types:
			raise TypeError(f"Unknown inputtype for parameter {id}")
		
		# initvalue must match inputtype
		if type(initvalue) is not self.types[inputtype]:
			raise TypeError(f"Type of initvalue doesn't match inputtype for parameter {id}")
		
		# Validate widget type
		if parCfg['widget'] not in _TKCWidget._WIDGETS_:
			raise ValueError(f"Unknown widget type for parameter {id}")
		
		# Validate valrange / initvalue / inputtype
		if type(valrange) is tuple:
			if len(valrange) < 2 or len(valrange) > 3:
				raise ValueError(f"valrange tuple must have 2 or 3 values for parameter {id}")
			if inputtype in ['int','float','complex'] and (initvalue < valrange[0] or initvalue > valrange[1]):
				raise ValueError(f"initvalue out of valrange for parameter {id}")
			elif inputtype == 'str' and (len(initvalue) < valrange[0] or len(initvalue) > valrange[1]):
				raise ValueError(f"Length of initvalue string out of valrange for paramter {id}")
			elif inputtype == 'bits':
				raise TypeError(f"Unsupported inputtype {inputtype} for valrange tuple for parameter {id}")
		elif type(valrange) is list:
			if len(valrange) == 0:
				raise ValueError(f"valrange list must not be empty for parameter {id}")
			if inputtype == 'str' and initvalue not in valrange:
				raise ValueError(f"initvalue is not part of valrange for parameter {id}")
			elif inputtype == 'int' and (initvalue < 0 or initvalue > len(valrange)):
				raise IndexError(f"initvalue out of valrange for parameter {id}")
			elif inputtype == 'bits' and (initvalue < 0 or initvalue >= 2**len(valrange)):
				raise IndexError(f"initvalue out of valrange for parameter {id}")
			elif inputtype in ['float', 'complex']:
				raise TypeError(f"Unsupported inputtype {inputtype}for valrange list for parameter {id}")

	# Validate parameter value
	def _validateValue(self, id: str, value, bCast = False):
		self._validateGroupId(id=id)
		parCfg = self.getPar(self.idList[id], id)

		# Type of value must match inputtype
		if type(value) is not self.types[parCfg['inputtype']]:
			raise TypeError(f"Type of value {value} doesn't match input type {parCfg['inputtype']} of parameter {id}")
		
		if bCast:
			if type(value) is int and parCfg['inputtype'] == 'float':
				value = float(value)
			elif type(value) is float and parCfg['inputtype'] == 'int':
				value = int(value)
			elif (type(value) is int or type(value) is float) and parCfg['inputtype'] == 'complex':
				value = complex(value)

		# Validate valrange / value
		if type(parCfg['valrange']) is tuple:
			if parCfg['inputtype'] in ['int','float','complex'] and (value < parCfg['valrange'][0] or value > parCfg['valrange'][1]):
				raise ValueError(f"Value {value} not in valrange for parameter {id}")
			elif parCfg['inputtype'] == 'str' and (len(str(value)) < parCfg['valrange'][0] or (len(str(value))) > parCfg['valrange'][1]):
				raise ValueError(f"String lenght out of valrange for parameter {id}")
		elif type(parCfg['valrange']) is list:
			if type(value) is str and value not in parCfg['valrange']:
				raise ValueError(f"Value {value} not in valrange list for parameter {id}")
			if type(value) is int:
				if parCfg['inputtype'] == 'int' and (value < 0 or value >= len(parCfg['valrange'])):
					raise IndexError(f"Value {value} is not a valid valrange index for parameter {id}")
				elif parCfg['inputtype'] == 'bits' and (value < 0 or value >= 2**len(parCfg['valrange'])):
					raise ValueError(f"Value {value} is not valid for valrange bitmask for parameter {id}")
		
		return value
	
	# Validate configuration / parameter values
	def _validateConfig(self, config: dict):
		for id in config:
			self._validateGroupId(id=id)
			if 'value' not in config[id]:
				raise ValueError(f"Missing value for parameter {id}")
			for a in config[id]:
				if a not in ['value', 'oldValue']:
					raise KeyError(f"Attribute {a} not allowed for parameter {id}")
			self._validateValue(id, config[id]['value'])

	# Set parameter value to default
	def setDefaultValue(self, group: str, id: str):
		self._validateGroupId(group=group, id=id)

		initvalue = self.getPar(group, id, 'initvalue')

		# Validate inputtype and initvalue, cast type for int or float
		nInitValue = self._validateValue(id, initvalue, bCast=True)
		self.set(id, nInitValue)
	
	# Set all parameters of current config to default values
	def resetConfigValues(self):
		self.config = {}
		for group in self.parDef:
			for id in self.parDef[group]:
				self.setDefaultValue(group, id)

	# Set new parameter definition and set config values to default values
	def setParameterDefinition(self, parameterDefinition: dict, config: dict | None = None):
		self.idList = {}
		self.parDef = {}
		self.updateParameterDefinition(parameterDefinition, config)

	# Update/enhance parameter defintion
	def updateParameterDefinition(self, parameterDefinition: dict, config: dict | None = None):
		# Complete parameter definition. Add defaults for missing attributes
		for group in parameterDefinition:
			for id in parameterDefinition[group]:
				if id in self.idList: raise KeyError(f"Duplicate parameter id {id}")
				self.idList[id] = group
				for a in self.defaults:
					if a not in parameterDefinition[group][id]:
						parameterDefinition[group][id][a] = self.defaults[a]

				# Validate parameter definition (will raise exceptions on error)
				self._validateParDef(id, parameterDefinition[group][id])

		# Store parameter defintion
		self.parDef.update(parameterDefinition)

		# Update parameter values
		if config is None:
			self.resetConfigValues()
		else:
			# Validate parameter values (will raise excpetions on error)
			self._validateConfig(config)
			self.setConfig(config)

	# Get current parameter definition as dictionary:
	# all paramters, all parameterss of specified group or specified parameter id
	def getParameterDefinition(self, group: str | None = None, id: str | None = None) -> dict:
		if id is None:
			if group is None:
				return self.parDef
			else:
				return self.getGroupDefinition(group)
		else:
			return self.getIdDefinition(id)

	# Get parameter group defintion as dictionary
	def getGroupDefinition(self, group: str) -> dict:
		self._validateGroupId(group=group)
		return self.parDef[group]
	
	# Get parameter id definition as dictionary
	def getIdDefinition(self, id: str) -> dict:
		self._validateGroupId(id=id)
		return self.parDef[self.idList[id]][id]

	# Add new key to parameter definition
	def addAttribute(self, attribute: str, default = None):
		if attribute in self.attributes: raise KeyError(f"Parameter attribute {attribute} already exists")
		self.attributes.append(attribute)
		self.defaults[attribute] = default

	# Add a new parameter to current configuration
	def addParameter(self, group: str, id: str, widget: str | None = None, **kwargs):
		if widget not in _TKCWidget._WIDGETS_: raise ValueError(f"Unknown widget type {widget}")
		if id in self.idList: raise KeyError(f"Parameter {id} already exists")
		# Create new group if it doesn't exist
		if group not in self.parDef: self.parDef[group] = {}
		self.idList[id] = group

		# Set parameter attributes to default, then overwrite by function parameters
		self.parDef[group][id] = { **self.defaults }
		for k in kwargs:
			if k not in self.attributes: raise KeyError(f"Unknown parameter attribute {k}")
			self.parDef[group][id][k] = kwargs[k]
		
		# Set config value of new parameter to default (initvalue)
		self.setDefaultValue(group, id)

	# Get parameter attribute(s)
	def getPar(self, group: str, id: str, attribute: str | None = None):
		self._validateGroupId(group=group, id=id)

		if attribute is None:
			return self.parDef[group][id]
		elif attribute not in self.attributes:
			raise KeyError(f"Unknown attribute {attribute} for parameter {id}")
		elif attribute in self.parDef[group][id]:
			return self.parDef[group][id][attribute]
		else:
			return self.defaults[attribute]

	# Set current config from dictionary
	def setConfig(self, config: dict):
		self._validateConfig(config)
		self.config = {}
		self.config.update(config)

	# Set current config from JSON data
	def setJSON(self, jsonData: str):
		self.setConfig(json.loads(jsonData))

	# Get current config as dictionary
	def getConfig(self) -> dict:
		return self.config
	
	# Get current config from dictionary as JSONx^
	def getJSON(self, indent: int = 4) -> str:
		return json.dumps(self.config, indent=indent)

	# Get parameter value
	def get(self, id: str, returndefault: bool = True, sync: bool = False):
		self._validateGroupId(id=id)
		if id in self.config and 'value' in self.config[id]:
			if sync and id in self.widget: self.widget[id]._update()
			return self.config[id]['value']
		elif returndefault:
			return self.getPar(self.idList[id], id, 'initvalue')
		else:
			raise ValueError(f"No value assigned to parameter {id}")
		
	# Get parameter id list
	def getIds(self) -> list:
		return list(self.idList.keys())
		
	# Get parameter widget
	def getWidget(self, id: str):
		if id in self.widget:
			return self.widget[id]
		else:
			return None

	# Get config value ['<id>'], shortcut for get(id)
	def __getitem__(self, id: str):
		return self.get(id)

	# Set config value if new value is different from current value
	def set(self, id: str, value, sync: bool = False):
		newValue = self._validateValue(id, value, bCast=True)

		if id not in self.config or 'value' not in self.config[id]:
			self.config.update({ id: { 'oldValue': newValue, 'value': newValue }})
		else:
			curValue = self.config.get(id, {}).get('value')
			if newValue != curValue:
				self.config.update({ id: { 'oldValue': curValue, 'value': newValue }})

		if sync and id in self.widget:
			self.syncWidget(id)
		
	# Set config value ['<id>'], shortcut for set(id)
	def __setitem__(self, id: str, value):
		self.set(id, value)

	# Reset parameter value(s) to old values (if old value exists)
	def undo(self, groups: list = [], id: str | None = None):
		if id is None:
			for i in self.config:
				self.undo(groups, i)
		elif id in self.config and (len(groups) == 0 or self.idList[id] in groups) and 'oldValue' in self.config[id]:
			self.config[id]['value'] = self.config[id]['oldValue']

	# Copy parameter values to old values
	def apply(self, groups: list = [], id: str | None = None, sync: bool = True):
		if id is None:
			for i in self.config:
				self.apply(groups, i)
		elif id in self.config and len(groups) == 0 or self.idList[id] in groups and 'value' in self.config[id]:
			if sync and id in self.widget: self.widget[id]._update()
			self.config[id]['oldValue'] = self.config[id]['value']

	# Sync widget value(s) with current config value(s)
	def syncWidget(self, id: str | None = None):
		if id is None:
			for i in self.widget:
				if i in self.config:
					v = self.get(i)
					self.widget[i].set(self.get(i))
		elif id not in self.widget:
			raise KeyError(f"Widget for parameter {id} not found")
		elif id in self.config:
			self.widget[id].set(self.get(id))

	# Sync current config with widget value(s)
	# Usually this function is not needed. Configuration is synced automatically when a widget value has been changed
	def syncConfig(self, id: str | None = None):
		if id is None:
			for id in self.config:
				if id in self.widget:
					self.widget[id]._update()
					self.set(id, self.widget[id].get())
		elif id not in self.config:
			raise KeyError("Unknown parameter {id}")
		elif id in self.widget:
			self.set(id, self.widget[id].get())

	# Create widgets for specified parameter group, return number of next free row
	def createWidgets(self, master, group: str = '', singlecol: bool = False, startrow: int = 0, padx=0, pady=0, *args, **kwargs):
		self._validateGroupId(group=group)
		row = startrow

		for id in self.parDef[group]:
			# Create the input widget
			widgetClass = globals()[self.getPar(group, id, 'widget')]
			justify = 'left' if self.getPar(group, id, 'inputtype') == 'str' else 'right'
			self.widget[id] = widgetClass(master, id=id, inputtype=self.getPar(group, id, 'inputtype'), valrange=self.getPar(group, id, 'valrange'),
					initvalue=self.get(id), onChange=self._onChange, justify=justify, width=self.getPar(group, id, 'width'), *args, **kwargs)
			
			# Set parameter specific widget attributes
			widgetattr = self.getPar(group, id, 'widgetattr')
			if len(widgetattr) > 0:
				self.widget[id].config(**widgetattr)

			lblText = self.getPar(group, id, 'label')
			if lblText != '':
				# Two columns: label and input widget
				lbl = tk.Label(master, text=lblText, justify='left', anchor='w')

				if singlecol:
					# Two rows, label in first row, input widget in second
					lbl.grid(columnspan=2, column=0, row=row, sticky='w', padx=padx, pady=pady)
					row += 1
					self.widget[id].grid(columnspan=2, column=0, row=row, sticky='w', padx=padx, pady=pady)
				else:
					# One row, label and input widget side by side
					lbl.grid(column=0, row=row, sticky='w', padx=padx, pady=pady)
					self.widget[id].grid(column=1, row=row, sticky='w', padx=padx, pady=pady)
			else:
				# One column (no label)
				self.widget[id].grid(columnspan=2, column=0, row=row, sticky='w', padx=padx, pady=pady)
			
			row += 1

		return row

	# Create the mask for all or some parameter groups, return row number of next free row
	# Before the widgets are created, the current parameter values are saved as old values (for specified groups only).
	# So every change can be reverted by calling undo()
	def createMask(self, master, singlecol: bool = False, startrow: int = 0, padx: int = 0, pady: int = 0, groups: list = [],
					groupwidth: int = 0, colwidth: tuple = (50.0, 50.0), *args, **kwargs):
		row = startrow
		grpList = list(self.parDef.keys()) if len(groups) == 0 else groups

		for g in grpList:
			# Do not show a border for widgets without group name
			border = 0 if g == '' else 2

			# Create group frame
			self.widget[g] = tk.LabelFrame(master, text=g, borderwidth=border)
			self.widget[g].grid(columnspan=2, row=row, column=0, padx=padx, pady=pady, sticky='we')

			# Configure width of columns
			if singlecol:
				self.widget[g].columnconfigure(0, minsize=groupwidth)
			else:
				self.widget[g].columnconfigure(0, minsize=int(groupwidth * colwidth[0] / 100.0))
				self.widget[g].columnconfigure(1, minsize=int(groupwidth * colwidth[1] / 100.0))

			# Count the label frame
			row += 1

			# Create widgets as childs of label frame. Row number is relative to label frame, starts from 0
			self.createWidgets(self.widget[g], group=g, singlecol=singlecol, startrow=0, padx=padx, pady=pady, *args, **kwargs)

		return row
	
	# Show Toplevel window with input mask. Return True, if config has been changed
	def showDialog(self, master, width: int = 0, height: int = 0, title: str = None, groupwidth=0, padx: int = 0, pady: int = 0, groups: list = [],
					colwidth: tuple = (50.0, 50.0), *args, **kwargs) -> bool:
		# Create a copy of the current configuration
		newConfig = TKConfigureCopy(self)

		result = False

		# Button handler
		def _onDlgButton(dlg: tk.Toplevel, newConfig: dict = None) -> bool:
			nonlocal result
			result = False
			if newConfig is not None:
				self.setConfig(newConfig)
				result = True
			dlg.destroy()
			return result

		# Create modal dialog window
		width = max(width, groupwidth+2*padx)
		dlg = tk.Toplevel(master)
		if width > 0 and height > 0:
			dlg.geometry(f"{width}x{height}")
			parent = dlg
		else:
			parent = tk.LabelFrame(dlg, borderwidth=0)
			parent.grid(column=0, row=0, padx=10, pady=5, sticky='we')
		dlg.grab_set()
		dlg.title(title)

		# Create the input mask
		row = newConfig.createMask(parent, startrow=0, padx=padx, pady=pady, groups=groups, groupwidth=max(0, width-padx*2),
			colwidth=colwidth, *args, **kwargs)
		
		# Create the buttons
		btnOk = tk.Button(parent, text='OK', command=lambda: _onDlgButton(dlg, newConfig.getConfig()))
		btnCancel = tk.Button(parent, text='Cancel', command=lambda: _onDlgButton(dlg))
		btnOk.grid(column=0, row=row)
		btnCancel.grid(column=1, row=row)

		# Wait for dialog window to be closed, then return True for OK and False fro CANCEL
		dlg.wait_window()
		return result

	# Called when widget value has changed
	def _onChange(self, id: str, value):
		if id in self.idList:
			oldValue = self.get(id, returndefault=False)
			self.set(id, value)
			if self.notifyChange is not None: self.notifyChange(id, oldValue, value)

# Create a new configuration object by cloning 
def TKConfigureCopy(config: TKConfigure) -> TKConfigure:
	return TKConfigure(config.getParameterDefinition(), config.getConfig())
