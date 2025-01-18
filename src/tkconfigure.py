import tkinter as tk
import json
from .tkcwidgets import *
from .tkcwidgets import _TKCWidget

from typing import Literal

from . import coloreditor as ce


# Class for JSON encode special values
class CustomEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, complex):
			return { '__complex__': True, 'real': obj.real, 'imag': obj.imag }
		elif isinstance(obj, TKConfigure):
			return obj.getConfig(simple=True)
		return super().default(obj)



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
#          ... Further attributes
#       },
#       ... Further parameter definitions
#    },
#    ... Further groups
# }
#
# Special group names:
#
# "" or "_" or "_group-name" - Draw a invisible group frame with border=0
# "#" or "#group-name"       - Do not create a group frame
#
# Parameter attributes:
#
#   inputtype -  The input type, either 'int', 'float', 'str', 'bits', 'complex',
#                'list' or 'tkc'.
#                Default = 'str'
#   initvalue -  Initial parameter value, type must match inputtype,
#                default = None
#   valrange -   Depends on inputtype, default = None (no input validation)
#                  'str': list of valid strings
#                  'int','float': tuple with value range (from, to [,increment])
#                  'bits': list of string representing the bits (index 0 = bit 0)
#   widget -     The type of the input widget, either 'TKCEntry', 'TKCSpinbox',
#                'TKCCheckbox', 'TKCListbox', 'TKCRadiobuttons', 'TKCFlags',
#                'TKCSlider', 'TKCColor', 'TKCColortable', 'TKCDialog',
#                'TKCMask' (placeholder for submask)
#                Default = None = Do not create a widget
#   label -      Text placed in front of the widget, default = '' (no text)
#   width -      Width of the input widget in characters, default = 20
#   widgetattr - Dictionary with additional TKInter widget attributes,
#                default = {}
#   notify -     Calback function. Called when widget value has changed with
#                old value and new value as parameters.
#   row -        Row of widget relative to group (starts with 0 for 1st group
#                widget)
#   column -     Column of widget. Grid column is calculated by multiplying
#                this value with the columns parameter, which is 2 if the 
#                label and the widget are placed side-by-side.
#   readonly   - If set to True, widget value cannot be changed
#   tooltip    - Text which is displayed when moving mouse over widget
#
# Parameter value dictionary:
#
# {
#    "parameter-name": {
#       "value":    parameter-value,
#       "oldValue": previous-parameter-value
#    },
#    ... Further parameter values
# }
#
###############################################################################

class TKConfigure:

	def __init__(self, parameterdefinition: dict | None = None, config: dict | None = None):

		# Input types:
		self.types = {
			'int': int, 'float': float, 'str': str, 'bits': int, 'complex': complex, 'list': list, 'tkc': TKConfigure
		}

		# Allowed parameter definition keys
		self.attributes = [
			'inputtype', 'valrange', 'initvalue', 'widget', 'label', 'width', 'widgetattr',
			'notify', 'row', 'column', 'readonly', 'tooltip', 'pardef'
		]

		# Default values for parameter attributes
		self.defaults = {
			'inputtype':   'str',
			'valrange':    None,
			'initvalue':   '',
			'widget':      None,
			'label':       '',
			'width':       20,
			'widgetattr':  {},
			'notify':      None,
			'row':         -1,
			'column':      -1,
			'readonly':    False,
			'tooltip':     '',
			'pardef':      None
		}

		# Maximum width of widgets
		self.maxWidth = 0

		# Initialize parameter definition (if specified)
		self.setParameterDefinition(parameterdefinition, config)

		# Created widgets: ['<id>'] -> <widget>
		self.widget = {}

		# Created tooltips: ['<id>'] -> <tooltip>
		self.tooltip = {}

		# Callback functions, can be set with notify()
		self.notifyChange = None
		self.notifyError  = None


	###########################################################################
	# Helper functions
	###########################################################################

	# Extract values as list from dictionary
	@staticmethod
	def _getDictValues(dictionary: dict, attributes: list, defaults: dict = {}) -> list:
		return [dictionary[a] if a in dictionary else (defaults[a] if a in defaults else None) for a in attributes ]
	
	# Dump current parameter values
	def dumpConfig(self):
		for id in self.config:
			value = self.config[id]['value']
			parCfg = self.getIdDefinition(id)
			if parCfg['inputtype'] == 'tkc':
				value.dumpConfig()
			else:
				print(f"{id} = {value}")

	# Inform app about change of config value
	def notify(self, onchange=None, onerror=None):
		self.notifyChange = onchange
		self.notifyError  = onerror

	
	###########################################################################
	# JSON encoding and decoding functions for configuration values
	#
	# The internal dictionary of configuration values is converted to a
	# simplified JSON structure:
	#
	# Internal dictionary:
	#
	# {
	#    "id1": {
	#       "oldValue": Value
	#       "value": Value
	#    },
	#    "id2": {
	#       ...
	#    }
	# }
	#
	# Simplified JSON:
	#
	# {
	#    "id1": Value,
	#    "id2": Value,
	#    ...
	# }
	#
	# If a value is of type TKConfigure, it's stored as a child JSON structure:
	#
	# {
	#    "id1": {
	#       "id11": Value,
	#       "id12": Value,
	#       ...
	#    },
	#    "id2": Value,
	#    ...
	# }
	###########################################################################

	# Encode JSON.
	# Callback function for encoding special datatypes 'complex' and 'TKConfigure'
	@staticmethod
	def _encodeJSON(obj):
		if isinstance(obj, complex):
			# Complex values are split into dict with 'real' and 'imag' keys
			return { 'real': obj.real, 'imag': obj.imag }
		elif isinstance(obj, TKConfigure):
			# TKConfigure values are resolved to simple dict
			return obj.getConfig(simple=True)
		raise TypeError(f'Cannot serialize object of type {type(obj)}')
	
	# Decode JSON.
	# Callback function for decoding special datatype 'complex'
	@staticmethod
	def _decodeJSON(dct: dict):
		if len(dct.keys()) == 2 and 'real' in dct and 'imag' in dct:
			# Convert { 'real': r, 'imag': i } to complex(r, i)
			return complex(dct['real'], dct['imag'])
		return dct

	# Convert dictionary to JSON string considering special datatypes 'complex' and 'TKConfigure'
	@staticmethod
	def toJSON(dct: dict, indent: int = 4) -> str:
		return json.dumps(dct, indent=indent, default=TKConfigure._encodeJSON)
	
	# Get current config values from internal dict as simple JSON
	def getJSON(self, indent: int = 4) -> str:
		return json.dumps(self.getConfig(simple=True), indent=indent, default=TKConfigure._encodeJSON)
	
	# Set current config values from JSON string
	def setJSON(self, jsonData: str):
		self.setConfig(json.loads(jsonData, object_hook=TKConfigure._decodeJSON), simple=True)


	###########################################################################
	# Validation functions
	###########################################################################

	# Validate group and/or id
	def _validateGroupId(self, group: str | None = None, id: str | None = None):
		if group is not None and group not in self.parDef:
			raise ValueError(f"Unknown parameter group {group}")
		if id is not None and id not in self.idList:
			raise ValueError(f"Unknown parameter id {id}")
		
	# Validate parameter defintion
	def _validateParDef(self, id: str, parCfg: dict):
		inputtype = parCfg['inputtype']
		initvalue = parCfg['initvalue']
		valrange  = parCfg['valrange']

		# Validate the inputtype
		if inputtype not in self.types:
			raise TypeError(f"Unknown inputtype for parameter {id}")
		
		# Validate attributes
		for a in parCfg:
			if a not in self.attributes:
				raise ValueError(f"Unknown attribute {a} for parameter {id}")

		# inputtype 'tkc' requires a parameter definition
		if inputtype == 'tkc':
			if parCfg['pardef'] is None:
				raise ValueError(f"inputtype 'tkc' of parameter {id} requires attribute 'pardef'")
			if type(parCfg['pardef']) is not dict:
				raise ValueError(f"Attribute 'pardef' of parameter {id} must be of type 'dict'")
		
		# initvalue must match inputtype
		if type(initvalue) is not self.types[inputtype]:
			raise TypeError(f"Type of initvalue doesn't match inputtype for parameter {id}")
		
		# Validate widget type
		if parCfg['widget'] not in _TKCWidget._WIDGETS_:
			raise ValueError(f"Unknown widget type {parCfg['widget']} for parameter {id}")
		
		# Validate valrange / initvalue / inputtype
		if type(valrange) is tuple:
			if (len(valrange) < 2 or len(valrange) > 3) and inputtype != 'str':
				raise ValueError(f"valrange tuple must have 2 or 3 values for parameter {id}")
			if inputtype in ['int','float','complex'] and (initvalue < valrange[0] or initvalue > valrange[1]):
				raise ValueError(f"initvalue out of valrange for parameter {id}")
			elif inputtype == 'str':
				if len(valrange) == 2 and (len(initvalue) < valrange[0] or len(initvalue) > valrange[1]):
					raise ValueError(f"Length of initvalue string out of valrange for parameter {id}")	
				elif len(valrange) == 1 and not re.match('^#([0-9a-fA-F]{2}){3}$', initvalue):
					raise ValueError(f"initvalue doesn't match regular expression for parameter {id}")
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
			
		if 'width' in parCfg:
			self.maxWidth = max(self.maxWidth, parCfg['width'])

	# Validate parameter value
	def _validateValue(self, id: str, value, bCast: bool = False):
		parCfg = self.getIdDefinition(id)

		# Type of value must match inputtype
		if type(value) is dict and parCfg['inputtype'] != 'tkc':
			raise TypeError(f"Value of type dict requires inputtype tkc")	
		if type(value) is not dict and type(value) is not self.types[parCfg['inputtype']]:
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
			elif parCfg['inputtype'] == 'str':
				if len(parCfg['valrange']) == 2 and (len(str(value)) < parCfg['valrange'][0] or (len(str(value))) > parCfg['valrange'][1]):
					raise ValueError(f"String lenght out of valrange for parameter {id}")
				elif len(parCfg['valrange']) == 1 and type(parCfg['valrange']) is str and not re.match('^#([0-9a-fA-F]{2}){3}$', value):
					raise ValueError(f"String doesn't match regular expression for parameter {id}")
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
	def _validateConfig(self, config: dict, simple: bool = False):
		for id in config:
			self._validateGroupId(id=id)
			if simple:
				self._validateValue(id, config[id])
			else:
				if 'value' not in config[id]:
					raise ValueError(f"Missing value for parameter {id}")
				for a in config[id]:
					if a not in ['value', 'oldValue']:
						raise KeyError(f"Attribute {a} not allowed for parameter {id}")
				self._validateValue(id, config[id]['value'])


	###########################################################################
	# Parameter configuration functions
	###########################################################################

	# Set new parameter definition and set config values.
	# If config is None, set default values
	def setParameterDefinition(self, parameterDefinition: dict, config: dict | None = None):
		# Reset parameter configuration

		# Parameter ids: ['<id>'] -> <group>
		self.idList = {}
		
		# Parameter definition: ['<group>']['<id>'] -> <definition>
		self.parDef = {}

		# Parameter values: ['<id>']['value' | 'oldvalue'] -> <value>
		self.config = {}

		# Set new parameter definition
		if parameterDefinition is not None:
			self.updateParameterDefinition(parameterDefinition, config)

	# Update/enhance parameter defintion
	def updateParameterDefinition(self, parameterDefinition: dict, config: dict | None = None):
		# Complete parameter definition. Add defaults for missing attributes
		for group in parameterDefinition:
			for id in parameterDefinition[group]:
				if id in self.idList:
					raise KeyError(f"Duplicate parameter id {id}")
				else:
					self.idList[id] = group

				# Complete missing attributes with defaults
				for a in self.defaults:
					if a not in parameterDefinition[group][id]:
						parameterDefinition[group][id][a] = self.defaults[a]

				# Validate parameter definition (will raise exceptions on error)
				self._validateParDef(id, parameterDefinition[group][id])

		# Store parameter defintion
		self.parDef.update(parameterDefinition)

		# Update parameter values
		if config is None:
			# Set values of added parameters to default
			self.resetConfigValues(parameterDefinition)
		else:
			# Validate parameter values (will raise excpetions on error)
			self._validateConfig(config)
			self.setConfig(config)

	# Get current parameter definition as dictionary:
	# all paramters, all parameters of specified group or specified parameter id
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
	
	# Set parameter attribute
	def setPar(self, group: str, id: str, attribute: str, attrvalue):
		self._validateGroupId(group=group, id=id)
		self.parDef[group][id][attribute] = attrvalue
		self._validateParDef(id, self.parDef[group][id])

	# Get parameter id list. Either all ids or ids of specified group
	def getIds(self, group: str | None = None) -> list:
		if group is None:
			return list(self.idList.keys())
		else:
			groupDef = self.getGroupDefinition(group)
			return list(groupDef.keys())
		

	###########################################################################
	# Functions for setting configuration values
	###########################################################################

	# Set parameter value to default
	def setDefaultValue(self, group: str, id: str):
		self._validateGroupId(group=group, id=id)

		initvalue = self.getPar(group, id, 'initvalue')

		# Validate inputtype and initvalue, cast type for int or float
		nInitValue = self._validateValue(id, initvalue, bCast=True)
		self.set(id, nInitValue)
	
	# Set all parameters of current config to default values
	def resetConfigValues(self, parameterDefinition: dict | None = None):
		if parameterDefinition is None:
			# Reset all existing parameter values
			for group in self.parDef:
				for id in self.parDef[group]:
					self.setDefaultValue(group, id)
		else:
			# Reset only parameter values in specified parameter definition
			for group in parameterDefinition:
				for id in parameterDefinition[group]:
					self.setDefaultValue(group, id)

	# Set current config values from dictionary
	#
	# Flags:
	#
	#   simple:
	#     True - config contains only id-value-pairs. Child dicts are allowed as value
	#     False - config contains ids as keys and child dict with 'oldValue' and 'value' keys (default)
	#   checkmissing:
	#     True - Raise exception if id is missing
	#     False - Do not check missing ids (default)
	#   reset:
	#     True - Set all config values to default before applying config
	#     False - Do not reset config values to default (default)
	#   clear:
	#     True - Delete config dictionary before applying config
	#     False - Do not delete config dictionary (default)
	#   sync:
	#     True - Sync widget values
	#
	def setConfig(self, config: dict, simple: bool = False, checkmissing: bool = False, reset: bool = False, clear: bool = False, sync: bool = False):
		self._validateConfig(config, simple=simple)

		if clear: self.config = {}
		if reset: self.resetConfigValues()

		if simple:
			for id, value in config.items():
				try:
					parDef = self.getIdDefinition(id)
					if parDef['inputtype'] == 'tkc':
						if type(value) is dict:
							self.config[id]['value'].setConfig(value, simple=True)
							self.syncWidget(id)
						else:
							raise TypeError(f"JSON value for inputtype 'tkc' must be of type 'dict'")
					else:
						self.set(id, value, sync=sync, init=True)
				except Exception as e:
					raise ValueError(f"Error {e} in setConfig: id={id}, value={value}")
		else:
			self.config.update(config)

		if checkmissing:
			# Check for missing ids
			for id in self.idList:
				if id not in self.config:
					raise KeyError(f"Missing id {id} in configuration values")

	# Set config value if new value is different from current value
	# If sync is True, update widget (if widget linked with parameter)
	def set(self, id: str, value, sync: bool = False, init: bool = False):
		newValue = self._validateValue(id, value, bCast=True)

		if id not in self.config or 'value' not in self.config[id] or init:
			self.config.update({ id: { 'oldValue': newValue, 'value': newValue }})
		else:
			# Store value if different from current value
			curValue = self.config.get(id, {}).get('value')
			if newValue != curValue:
				self.config.update({ id: { 'oldValue': curValue, 'value': newValue }})

		if sync and id in self.widget:
			self.syncWidget(id)

	# Set multiple config values
	# If sync is True, update widgets (if widget linked with parameter)
	#
	# Usage:
	#
	#   setValues(id1 = Value1, id2 = Value2, ...)
	#
	def setValues(self, sync: bool = False, **kwargs):
		for id in kwargs:
			self.set(id, kwargs[id], sync)
		
	# Set config value ['<id>'], shortcut for set(id) with sync=False
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


	###########################################################################
	# Functions for getting configuration values
	###########################################################################

	# Get current config values as dictionary
	def getConfig(self, simple: bool = False) -> dict:
		if simple:
			simpleConfig = {}
			for id in self.config.keys():
				simpleConfig[id] = self.config[id]['value']
			return simpleConfig
		else:
			return self.config

	# Get parameter value
	def get(self, id: str, returndefault: bool = True, sync: bool = False):
		if id not in self.config: print(f"{id} not in self.config")
		self._validateGroupId(id=id)
		if id in self.config and 'value' in self.config[id]:
			if sync and id in self.widget: self.widget[id]._update()
			return self.config[id]['value']
		elif returndefault:
			return self.getPar(self.idList[id], id, 'initvalue')
		else:
			raise ValueError(f"No value assigned to parameter {id}")
		
	# Get multiple parameter values. If idList is None, all values will be returned
	def getValues(self, idList: list[str] | None = None, returndefault: bool = True, sync: bool = False) -> list:
		if idList is None:
			ids = self.getIds()
		else:
			if type(idList) is not list:
				raise("Parameter idList must be of type list")
			ids = idList
		values = [self.get(id, returndefault=returndefault, sync=sync) for id in ids]
		return values

	# Get config value ['<id>'], shortcut for get(id) with returndefault=True and sync=False
	def __getitem__(self, id: str):
		return self.get(id)

	# Get all values of a group as dict
	def getGroupValues(self, group: str) -> dict:
		groupDef = self.getGroupDefinition(group)
		valueDict = { an: self.get(an) for an in groupDef }
		return valueDict


	###########################################################################
	# UI and widgets related functions
	###########################################################################

	# Get parameter widget object
	def getWidget(self, id: str):
		if id in self.widget:
			return self.widget[id]
		else:
			return None
	
	# Enable/disable widget
	def setWidgetState(self, id: str, state: str):
		widget = self.getWidget(id)
		if widget is not None:
			widget.config(state=state)

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
		else:
			raise KeyError(f"Unknown parameter id {id}")

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

	# Called when button linked to widget is pressed
	# Parameter settings contains the TKConfigure object to be changed
	def onParEditButton(self, id: str, master, title: str, settings):
		parCfg = self.getIdDefinition(id)
		padx   = 10
		pady   = 5
		width  = 0
		height = 0

		# Dialog dimensions and padding can defined in parameter "widgetattr"
		if 'widgetattr' in parCfg:
			width, height, padx, pady = TKConfigure._getDictValues(
				parCfg['widgetattr'], ['width', 'height', 'padx', 'pady'], defaults = {
					'width': width, 'height': height, 'padx': padx, 'pady': pady
				}
			)
		
		if parCfg['widget'] == 'TKCDialog':
			if width == 0: width  = max(settings.maxWidth * 3 + 2 * padx, 150)
			if height == 0: height = max(len(settings.idList.keys()) * (55 + pady), 200)
			if settings.showDialog(master, title=title, width=width, height=height, padx=padx, pady=pady):
				# No need to call _onChange(), because config is directly updated by widget
				self.syncWidget(id)

		elif parCfg['widget'] == 'TKCColortable':
			cEdit = ce.ColorEditor(master, width=max(width, 400), height=max(height, 600))
			if cEdit.show(settings, title=title):
				self._onChange(id, cEdit.masterSettings['colorTable'])
				self.syncWidget(id)
				# self.set(id, cEdit.masterSettings['colorTable'], sync=True)

	# Create widgets for specified parameter group, return number of next free row
	def createWidgets(self, master, group: str = '', columns: int = 2, startrow: int = 0, padx=0, pady=0, submasks: bool = True, *args, **kwargs):
		self._validateGroupId(group=group)
		row = startrow

		for id in self.parDef[group]:
			inputType = self.getPar(group, id, 'inputtype')
			widgetType = self.getPar(group, id, 'widget')

			# Ignore parameters without widget type
			if widgetType is None:
				continue
			elif widgetType == 'TKCMask':
				if submasks:
					# Create a submask
					subSetting = self.get(id)
					row = subSetting.createMask(master, startrow=row, **self.getPar(group, id, 'widgetattr'))
					continue
				else:
					break

			# Create the input widget
			widgetClass = globals()[widgetType]
			# justify = 'left' if self.getPar(group, id, 'inputtype') == 'str' else 'right'
			try:
				self.widget[id] = widgetClass(master, id=id, inputtype=inputType,
						valrange=self.getPar(group, id, 'valrange'), initvalue=self.get(id), readonly=self.getPar(group, id, 'readonly'),
						onChange=self._onChange, width=self.getPar(group, id, 'width'), *args, **kwargs)
			except Exception as e:
				print(type(e), e)
				raise RuntimeError(f"Error while creating widget of type {widgetType} for parameter {id}")
			
			# Set parameter specific widget attributes
			widgetattr = self.getPar(group, id, 'widgetattr')
			if len(widgetattr) > 0 and widgetType != 'TKCDialog':
				self.widget[id].config(**widgetattr)

			grow = self.getPar(group, id, 'row')
			if grow != -1: row = grow
			gcol = self.getPar(group, id, 'column')
			if gcol == -1: gcol = 0
			gcol *= columns

			lblText = self.getPar(group, id, 'label')
			if lblText != '':
				tipText = self.getPar(group, id, 'tooltip')

				# Checkbox: label = text of checkbox
				if widgetType == 'TKCCheckbox':
					self.widget[id].config(text=lblText)
					self.widget[id].grid(columnspan=2, column=gcol, row=row, sticky='nw', padx=padx, pady=pady)
					if tipText != '': self.tooltip[id] = Tooltip(self.widget[id], tipText)

				# Dialog windows: label = text of button
				elif widgetType == 'TKCDialog' or widgetType == 'TKCColortable':
					btnId = 'btn_' + id
					idSettings = self.get(id)
					self.widget[btnId] = tk.Button(master, text=lblText,
								command=lambda i=id, m=master, t=lblText, s=idSettings: self.onParEditButton(i, m, t, s))
					self.widget[btnId].grid(column=gcol, row=row, sticky='w', padx=padx, pady=pady)
					self.widget[id].grid(column=gcol+1, row=row, sticky='w', padx=padx, pady=pady)
					if tipText != '': self.tooltip[btnId] = Tooltip(self.widget[btnId], tipText)

				else:
					# Two widgets: label and input widget
					lblId = 'lbl_' + id
					self.widget[lblId] = tk.Label(master, text=lblText, justify='left', anchor='w')
					if tipText != '': self.tooltip[lblId] = Tooltip(self.widget[lblId], tipText)

					if columns == 1:
						# Two rows, label in first row, input widget in second
						self.widget[lblId].grid(columnspan=2, column=gcol, row=row, sticky='w', padx=padx, pady=pady)
						row += 1
						self.widget[id].grid(columnspan=2, column=gcol, row=row, sticky='w', padx=padx, pady=pady)
					else:
						# One row, label and input widget side by side
						self.widget[lblId].grid(column=gcol, row=row, sticky='w', padx=padx, pady=pady)
						self.widget[id].grid(column=gcol+1, row=row, sticky='w', padx=padx, pady=pady)
			else:
				# One column (no label), i.e. radio button groups
				self.widget[id].grid(columnspan=2, column=gcol, row=row, sticky='nw', padx=padx, pady=pady)
			
			row += 1

		return row

	# Create the mask for all or some parameter groups, return row number of next free row
	# Before the widgets are created, the current parameter values are saved as old values (for specified groups only).
	# So every change can be reverted by calling undo()
	def createMask(self, master, columns: int = 2, startrow: int = 0, padx: int = 0, pady: int = 0, groups: list = [],
					groupwidth: int = 0, colwidth: tuple = (50.0, 50.0), submasks: bool = True, *args, **kwargs) -> int:
		row = startrow
		grpList = list(self.parDef.keys()) if len(groups) == 0 else groups

		for g in grpList:
			# Do not create a group frame when group name starts with '#'
			if len(g) == 0 or g[0] != '#':
				# Do not show a border around group for empty group names or group names starting with '_'
				border = 0 if g == '' or (len(g) > 0 and g[0] == '_')  else 2

				# Create group frame
				self.widget[g] = tk.LabelFrame(master, text=g, borderwidth=border)
				self.widget[g].grid(columnspan=2, row=row, column=0, padx=padx, pady=pady, sticky='we')

				# Configure width of columns
				if columns == 1:
					self.widget[g].columnconfigure(0, minsize=groupwidth)
				else:
					self.widget[g].columnconfigure(0, minsize=int(groupwidth * colwidth[0] / 100.0))
					self.widget[g].columnconfigure(1, minsize=int(groupwidth * colwidth[1] / 100.0))

				# Count only the label frame
				row += 1

				# Create widgets as childs of label frame. Row number is relative to label frame, starts from 0
				self.createWidgets(self.widget[g], group=g, columns=columns, startrow=0, padx=padx, pady=pady, submasks=submasks, *args, **kwargs)

			else:
				# Count rows of all created widgets
				row = self.createWidgets(master, group=g, columns=columns, startrow=0, padx=padx, pady=pady, submasks=submasks, *args, **kwargs)

		return row
	
	# Delete an input mask, destroy all widgets
	def deleteMask(self):
		for w in self.widget:
			self.widget[w].destroy()
		self.widget.clear()
	
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
			if value is not None:
				oldValue = self.get(id, returndefault=False)
				self.set(id, value)
			else:
				oldValue = None

			# Inform app about change of specific widget value
			parCfg = self.getIdDefinition(id)
			if 'notify' in parCfg and parCfg['notify'] is not None:
				parCfg['notify'](oldValue, value)

			# Inform app about change of any widget value
			if self.notifyChange is not None:
				self.notifyChange(id, oldValue, value)

# Create a new configuration object by cloning 
def TKConfigureCopy(config: TKConfigure) -> TKConfigure:
	return TKConfigure(config.getParameterDefinition(), config.getConfig())
