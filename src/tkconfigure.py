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
#   Config = AppConfig(parameterDefinition [, widgetList])
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
# {
#    "parameter-name-1": {
#       "group":     "group-name" or 'none' (default),
#       "inputType": 'int' or 'float'
#       "valRange":  tuple, depends on widget type
#       "initValue": initial-value
#       "widget":    'NumSpinbox', 'NumEntry' or 'NumCombobox',
#       "label":     "widget-label" or "",
#       "width":     widget-with (characters, default=20s)
#    },
#    "parameter-name-n": {
#       ...
#    }
# }
#
###############################################################################

class AppConfig:

	def __init__(self, parameterDefinition = None):

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

		# Current configuration values: ['id'] -> value
		self.config = {}

		# Created widgets: ['id'] -> widget
		self.widget = {}

		# Parameter definition: ['id'] -> definition
		if parameterDefinition is None:
			self.parDef = {}
		else:
			self.setParameterDefinition(parameterDefinition)

	# Set parameter value to default
	def setDefault(self, group: str, id: str):
		if group not in self.parDef or id not in self.parDef[group]: raise KeyError(id)
		self.config[id] = self.getPar(group, id, 'initValue')
	
	# Set current config to default values
	def reset(self):
		for group in self.parDef:
			for id in self.parDef[group]:
				self.config[id] = self.getPar(group, id, 'initValue')

	def setParameterDefinition(self, parameterDefinition: dict):
		for group in parameterDefinition:
			for id in parameterDefinition[group]:
				for k in parameterDefinition[group][id]:
					if k not in self.keys:
						raise KeyError(k)
					if k == 'widget' and parameterDefinition[group][id][k] not in _TKCWidget._WIDGETS_:
						raise ValueError(parameterDefinition[group][id][k])

		self.parDef = parameterDefinition
		self.reset()

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
		
	# Get current config as dictionary
	def getConfig(self) -> dict:
		return self.config

	# Get config value
	def get(self, id: str, group: str = None):
		if id in self.config:
			return self.config[id]
		elif group is None:
			g = self.getGroup(id)
		else:
			g = group
		return self.getPar(g, id, 'initValue')


	def __getitem__(self, id: str):
		return self.get(id)

	# Set config value	
	def set(self, id: str, value):
		if id in self.parDef:
			self.config[id] = value
		else:
			raise KeyError(id)
	
	# Create the widgets, return number of next free row
	def createWidgets(self, master, group: str = '', columns: int = 2, startRow: int = 0, pady=0, *args, **kwargs):
		row = startRow

		for id in self.parDef[group]:
			widgetClass = globals()[self.getPar(group, id, 'widget')]
			self.widget[id] = widgetClass(master, id=id, inputType=self.getPar(group, id, 'inputType'), valRange=self.getPar(group, id, 'valRange'),
					initValue=self.get(id, group), onChange=self.onChange, justify='right', width=self.getPar(group, id, 'width'), *args, **kwargs)

			lblText = self.getPar(group, id, 'label')
			if lblText != '':
				lbl = tk.Label(master, text=lblText, justify='left', anchor='w')
				lbl.grid(column=0, row=row, sticky='w', pady=pady)
				self.widget[id].grid(column=1, row=row, sticky='w', pady=pady)
			else:
				self.widget[id].grid(columnspan=columns, column=0, row=row, sticky='w', pady=pady)
			
			row += 1

		return row

	# Create the mask for all or some parameter groups, return row number of next free row
	def createMask(self, master, columns: int = 2, startRow: int = 0, padx: int = 0, pady: int = 0, groups: list = [], groupWidth: int = 0, *args, **kwargs):
		row = startRow
		groupList = self.parDef.keys() if len(groups) == 0 else groups

		for g in groupList:
			if g == '':
				# No group, create widgets as child of master frame
				row = self.createWidgets(master, columns=columns, startRow=row, pady=pady, *args, **kwargs)
			else:
				# Create group frame
				self.widget[g] = tk.LabelFrame(master, text=g, width=groupWidth)
				self.widget[g].grid(row=row, column=0, padx=padx, pady=pady, sticky='ew')
				row += 1	# Count the label frame
				# Row number is relative to label frame, starts from 0
				self.createWidgets(self.widget[g], group=g, columns=columns, startRow=0, pady=pady, *args, **kwargs)

		return row

	# Called when widget value has changed
	def onChange(self, id: str, value):
		if id in self.config:
			self.config[id] = value
