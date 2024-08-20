import tkinter as tk
from tkcwidgets import *
from tkcwidgets import _TKCWidget

from typing import Literal

###############################################################################
#
# Create configuration objects
#
# Usage:
#
#   Config = TKConfigure(parameterDefinition [, widgetList])
#
# Parameters:
#
#   parameterDefinition - dictionary with config parameters
#
# Methods:
#
#   setDefault(id) - Set default/initial value of parameter <id>
#   reset() - Set default/initial values for all parameters
#   setParameterDefiniton(parameterDefintion) - Change parameter definition
#
# A parameter definition is a dictionary with the following syntax:
#
# "group-name-1": {
#    "parameter-name-1": {
#       "group":     "group-name" or 'none' (default),
#       "inputType": 'int' or 'float'
#       "valRange":  tuple or list depending on widget type
#       "initValue": initial-value. If valRange is a list of values,
#                    initialValue must be part of the list
#       "widget":    'NumSpinbox', 'NumEntry' or 'NumCombobox',
#       "label":     "widget-label" or "",
#       "width":     widget-with (characters, default=20s)
#    },
#    "parameter-name-n": {
#       ...
#    }
# },
# "": {
# }
#
###############################################################################

class TKConfigure:

	def __init__(self, parameterdefinition: dict | None = None, config: dict | None = None):

		# Allowed parameter definition keys. Can be enhanced by method addKey()
		self.keys = [ 'inputType', 'valRange', 'initValue', 'widget', 'label', 'width' ]
		self.defaults = {
			'inputType': 'str',
			'valRange':  None,
			'initValue': None,
			'widget':    'TKCEntry',
			'label':     '',
			'width':     20
		}
		
		# Parameter definition: ['id'] -> definition
		if parameterdefinition is None:
			self.parDef = {}
			self.config = {}
		else:
			self.setParameterDefinition(parameterdefinition, config)

		# Created widgets: ['id'] -> widget
		self.widget = {}

	# Set parameter value to default
	def setDefault(self, group: str, id: str):
		if group not in self.parDef or id not in self.parDef[group]:
			raise KeyError(id)
		initValue = self.getPar(group, id, 'initValue')
		valRange = self.getPar(group, id, 'valRange')
		if self.getPar(group, id, 'inputType') != 'str' and type(valRange) is list:
			self.config[id] = valRange.index(initValue)
		else:
			self.config[id] = initValue
	
	# Set current config to default values
	def reset(self):
		self.config = {}
		for group in self.parDef:
			for id in self.parDef[group]:
				self.setDefault(group, id)

	# Set parameter definition and set config values to default values
	def setParameterDefinition(self, parameterDefinition: dict, config: dict | None = None):
		# Validate parameter definition
		for group in parameterDefinition:
			for id in parameterDefinition[group]:
				for k in parameterDefinition[group][id]:
					if k not in self.keys:
						raise KeyError(k)
					if k == 'widget' and parameterDefinition[group][id][k] not in _TKCWidget._WIDGETS_:
						raise ValueError(parameterDefinition[group][id][k])

		self.parDef = parameterDefinition

		if config is None:
			self.reset()
		else:
			self.setConfig(config)

	# Get current parameter definition as dictionary
	def getParameterDefinition(self):
		return self.parDef

	# Add new key to parameter definition
	def addKey(self, id: str):
		if id in self.keys:
			raise KeyError(id)
		self.keys.append(id)

	# Add a new parameter
	def addParameter(self, group: str, id: str, widget: str, **kwargs):
		if widget not in _TKCWidget._WIDGETS_: raise ValueError(widget)

		self.parDef[group][id] = {
			'widget': widget
		}
		for k in kwargs:
			if k not in self.keys: raise ValueError(k)
			self.parDef[group][id][k] = kwargs[k]
		self.setDefault(group, id)

	def getGroup(self, id: str) -> str:
		for g in self.parDef:
			if id in self.parDef[g]:
				return g
		raise KeyError(id)
		
	# Get parameter attribute
	def getPar(self, group: str, id: str, key: str):
		if group not in self.parDef: raise KeyError(group)
		if id not in self.parDef[group]: raise KeyError(id)
		if key not in self.keys: raise KeyError(key)
		if key in self.parDef[group][id]:
			return self.parDef[group][id][key]
		else:
			return self.defaults[key]
	
	# Set current config from dictionary
	def setConfig(self, config: dict):
		for id in config:
			self.getGroup(id)
		self.config = config

	# Get current config as dictionary
	def getConfig(self) -> dict:
		return self.config

	# Get config value
	def get(self, id: str, group: str = None):
		if id in self.config:
			return self.config[id]
		g = self.getGroup(id) if group is None else group
		return self.getPar(g, id, 'initValue')

	# Get config value [id]
	def __getitem__(self, id: str):
		return self.get(id)

	# Set config value	
	def set(self, id: str, value):
		if id in self.parDef:
			self.config[id] = value
		else:
			raise KeyError(id)
	
	# Create widgets for specified parameter group, return number of next free row
	def createWidgets(self, master, group: str = '', singlecol: bool = False, startrow: int = 0, padx=0, pady=0, *args, **kwargs):
		row = startrow

		for id in self.parDef[group]:
			# Create the input widget
			widgetClass = globals()[self.getPar(group, id, 'widget')]
			justify = 'left' if self.getPar(group, id, 'inputType') == 'str' else 'right'
			self.widget[id] = widgetClass(master, id=id, inputType=self.getPar(group, id, 'inputType'), valRange=self.getPar(group, id, 'valRange'),
					initValue=self.get(id, group), onChange=self.onChange, justify=justify, width=self.getPar(group, id, 'width'), *args, **kwargs)

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
	def createMask(self, master, singlecol: bool = False, startrow: int = 0, padx: int = 0, pady: int = 0, groups: list = [],
					groupwidth: int = 0, colwidth: tuple = (50.0, 50.0), *args, **kwargs):
		row = startrow
		groupList = self.parDef.keys() if len(groups) == 0 else groups

		for g in groupList:
			# Do not show a border for widgets without group name
			border = 0 if g == '' else 2

			# Create group frame
			self.widget[g] = tk.LabelFrame(master, text=g, borderwidth=border)
			self.widget[g].grid(columnspan=2, row=row, column=0, padx=padx, pady=pady, sticky='w')

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

	# Called when widget value has changed
	def onChange(self, id: str, value):
		if id in self.config:
			self.config[id] = value

