import tkinter as tk
import tkcwidgets as tkcw

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
		self.keys = [ 'group', 'inputType', 'valRange', 'initValue', 'widget', 'label', 'width' ]

		# Current configuration values: ['id'] -> value
		self.config = {}

		# Created widgets: ['id'] -> widget
		self.widget = {}

		# Parameter definition: ['id'] -> definition
		if parameterDefinition is None:
			self.parDef = {}
		else:
			self.setParameterDefinition(parameterDefinition)

	def setDefault(self, id: str):
		if id not in self.parDef:
			raise KeyError(id)
		if 'initValue' in self.parDef[id]:
			self.config[id] = self.parDef[id]['initValue']
	
	# Set current config to defualt values
	def reset(self):
		for id in self.parDef:
			self.setDefault(id)

	def setParameterDefinition(self, parameterDefinition: dict):
		for id in parameterDefinition:
			for k in parameterDefinition[id]:
				if k not in self.keys:
					raise KeyError(k)
				if k == 'widget' and parameterDefinition[id][k] not in tkcw.widgets:
					raise ValueError(parameterDefinition[id][k])

		self.parDef = parameterDefinition
		self.reset()

	# Add new key to parameter definition
	def addKey(self, id: str):
		if id in self.keys:
			raise KeyError(id)
		self.keys.append(id)

	# Add a new parameter
	def addParameter(self, id: str, widget: Literal['NumSpinbox', 'NumEntry', 'NumCombobox'], **kwargs):
		self.parDef[id] = {
			'widget':    widget
		}
		for k in kwargs:
			if k in self.keys:
				self.parDef[id][k] = kwargs[k]
		self.setDefault(id)

	# Get current config as dictionary
	def getConfig(self) -> dict:
		return self.config

	# Get config value
	def get(self, id: str):
		if id in self.config:
			return self.config[id]
		elif id in self.parDef:
			return self.parDef[id]['initValue']
		else:
			raise KeyError(id)

	# Set config value	
	def set(self, id: str, value):
		if id in self.parDef:
			self.config[id] = value
		else:
			raise KeyError(id)
	
	# Create the widgets, return row of last widget
	def createWidgets(self, master, group: str, columns: int = 2, startRow: int = 0, pady=0, *args, **kwargs):
		row = startRow

		for r, id in enumerate(self.parDef):
			if self.parDef[id]['group'] == group:
				row = startRow+r
				width = self.parDef[id]['width'] if 'width' in self.parDef[id] else 20
				if (self.parDef[id]['widget'] == 'NumSpinbox'):
					self.widget[id] = tkcw.NumSpinbox(master, id=id, inputType=self.parDef[id]['inputType'], valRange=self.parDef[id]['valRange'], initValue=self.get(id),
						onChange=self.onChange, justify='right', width=width, *args, **kwargs)
				elif (self.parDef[id]['widget'] == 'NumEntry'):
					self.widget[id] = tkcw.NumEntry(master, id=id, inputType=self.parDef[id]['inputType'], valRange=self.parDef[id]['valRange'], initValue=self.get(id),
						onChange=self.onChange, justify='right', width=width, *args, **kwargs)
				elif (self.parDef[id]['widget'] == 'NumCombobox'):
					self.widget[id] = tkcw.NumCombobox(master, id=id, valRange=self.parDef[id]['valRange'], initValue=self.get(id),
						onChange=self.onChange, justify='left', width=width, *args, **kwargs)
				else:
					raise ValueError(self.parDef[id]['widget'])

				if self.parDef[id]['label'] != '':
					lbl = tk.Label(master, text=self.parDef[id]['label'], justify='left', anchor='w', width=17)
					lbl.grid(column=0, row=row, sticky='W', pady=pady)
					self.widget[id].grid(column=1, row=row, sticky='w', pady=pady)
				else:
					self.widget[id].grid(columnspan=columns, column=0, row=row, sticky='w', pady=pady)

		return row

	# Create the mask, return row of last group or widget
	def createMask(self, master, columns: int = 2, startRow: int = 0, padx: int = 0, pady: int = 0, groups: list = [ 'all' ], groupWidth: int = 0, *args, **kwargs):
		row = startRow

		for r, g in enumerate(groups):
			row = startRow + r
			self.widget[g] = tk.LabelFrame(master, text=g, width=groupWidth)
			self.widget[g].grid(row=row, column=0, padx=padx, pady=pady, sticky='ew')
			self.createWidgets(self.widget[g], g, columns=columns, startRow=0, pady=pady, *args, **kwargs)

		return row

	# Called when widget has been left
	def onChange(self, id: str, value):
		if id in self.config:
			self.config[id] = value
