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
#   setDefaultValue(id) - Set default/initial value of parameter <id>
#   resetConfigValues() - Set default/initial values for all parameters
#   setParameterDefiniton(parameterDefintion) - Change parameter definition
#
# A parameter definition is a dictionary with the following syntax:
#
# "group-name": {
#    "parameter-name": {
#       "attribute-name": attribute-value,
#       ... # Further attributes
#    },
#    ... # Further parameter definitions
# },
# ... # Further groups, use "" for no-group
#
###############################################################################

class TKConfigure:

	def __init__(self, parameterdefinition: dict | None = None, config: dict | None = None):

		# Allowed parameter definition keys. Can be enhanced by method addKey()
		self.attributes = [ 'inputType', 'valRange', 'initValue', 'widget', 'label', 'width' ]

		# Default values for parameter attributes
		self.defaults = {
			'inputType': 'str',
			'valRange':  None,
			'initValue': None,
			'widget':    'TKCEntry',
			'label':     '',
			'width':     20
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

	# Set parameter value to default
	def setDefaultValue(self, group: str, id: str):
		if group not in self.parDef or id not in self.parDef[group]:
			raise KeyError(id)
		initValue = self.getPar(group, id, 'initValue')
		valRange = self.getPar(group, id, 'valRange')
		if self.getPar(group, id, 'inputType') != 'str' and type(valRange) is list:
			self.config[id] = valRange.index(initValue)
		else:
			self.config[id] = initValue
	
	# Set all parameters of current config to default values
	def resetConfigValues(self):
		self.config = {}
		for group in self.parDef:
			for id in self.parDef[group]:
				self.setDefaultValue(group, id)

	# Set parameter definition and set config values to default values
	def setParameterDefinition(self, parameterDefinition: dict, config: dict | None = None):
		self.idList = {}

		# Validate parameter definition
		for group in parameterDefinition:
			for id in parameterDefinition[group]:
				if id in self.idList: raise ValueError("Duplicate parameter id", id)
				self.idList[id] = group
				for k in parameterDefinition[group][id]:
					if k not in self.attributes:
						raise KeyError("Unknown parameter attribute", k)
					if k == 'widget' and parameterDefinition[group][id][k] not in _TKCWidget._WIDGETS_:
						raise ValueError("Unknown widget type", parameterDefinition[group][id][k])

		self.parDef = parameterDefinition

		if config is None:
			self.resetConfigValues()
		else:
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
		if group is None or group not in self.parDef: raise ValueError("Unknown parameter group", group)
		return self.parDef[group]
	
	# Get parameter id definition as dictionary
	def getIdDefinition(self, id: str) -> dict:
		if id is None or id not in self.idList: raise ValueError("Unknown parameter id", id)
		return self.parDef[self.idList[id]][id]

	# Add new key to parameter definition
	def addAttribute(self, attribute: str, default = None):
		if attribute in self.attributes: raise KeyError("Parameter attribute exists", attribute)
		self.attributes.append(attribute)
		self.defaults[attribute] = default

	# Add a new parameter to current configuration
	def addParameter(self, group: str, id: str, widget: str | None = None, **kwargs):
		if widget not in _TKCWidget._WIDGETS_: raise ValueError("Unknown widget type", widget)
		if id in self.idList: raise KeyError("Parameter already exists", id)
		# Create new group if it doesn't exist
		if group not in self.parDef: self.parDef[group] = {}
		self.idList[id] = group

		# Set parameter attributes to default, then overwrite by function parameters
		self.parDef[group][id] = { **self.defaults }
		for k in kwargs:
			if k not in self.attributes: raise KeyError("Unknown parameter attribute", k)
			self.parDef[group][id][k] = kwargs[k]
		
		# Set config value of new parameter to default (initValue)
		self.setDefaultValue(group, id)

	# Get parameter attribute
	def getPar(self, group: str, id: str, attribute: str):
		if group not in self.parDef: raise KeyError("Unknown parameter group", group)
		if id not in self.parDef[group]: raise KeyError("Unknown parameter id", id)
		if attribute not in self.attributes: raise KeyError("Unknown attribute", attribute)
		if attribute in self.parDef[group][id]:
			return self.parDef[group][id][attribute]
		else:
			return self.defaults[attribute]

	# Set current config from dictionary
	def setConfig(self, config: dict):
		for id in config:
			if id not in self.idList: raise ValueError("Unknown parameter id", id)
		self.config = config

	# Get current config as dictionary
	def getConfig(self) -> dict:
		return self.config

	# Get parameter value
	def get(self, id: str):
		if id not in self.idList: raise ValueError("Unknown parameter id", id)
		if id in self.config:
			return self.config[id]
		else:
			return self.getPar(id, 'initValue')
		
	# Get parameter widget
	def getWidget(self, id: str):
		if id in self.widget:
			return self.widget[id]
		else:
			return None

	# Get config value ['<id>'], shortcut for get(id)
	def __getitem__(self, id: str):
		return self.get(id)

	# Set config value	
	def set(self, id: str, value):
		if id in self.idList:
			self.config[id] = value
		else:
			raise ValueError("Unknown paramete id", id)
	
	# Create widgets for specified parameter group, return number of next free row
	def createWidgets(self, master, group: str = '', singlecol: bool = False, startrow: int = 0, padx=0, pady=0, *args, **kwargs):
		row = startrow

		for id in self.parDef[group]:
			# Create the input widget
			widgetClass = globals()[self.getPar(group, id, 'widget')]
			justify = 'left' if self.getPar(group, id, 'inputType') == 'str' else 'right'
			self.widget[id] = widgetClass(master, id=id, inputType=self.getPar(group, id, 'inputType'), valRange=self.getPar(group, id, 'valRange'),
					initValue=self.get(id), onChange=self._onChange, justify=justify, width=self.getPar(group, id, 'width'), *args, **kwargs)

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
	
	# Show Toplevel window with input mask. Return True, if config has been changed
	def showDialog(self, master, width: int, height: int, title: str = None, padx: int = 0, pady: int = 0, groups: list = [],
					colwidth: tuple = (50.0, 50.0), *args, **kwargs) -> bool:
		# Create a copy of the current configuration
		newConfig = TKConfigure(self.getParameterDefinition(), self.getConfig())

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
		dlg = tk.Toplevel(master)
		dlg.geometry(f"{width}x{height}")
		dlg.grab_set()
		dlg.title(title)

		# Create the input mask
		row = newConfig.createMask(dlg, startrow=0, padx=padx, pady=pady, groups=groups, groupwidth=width-padx*2,
			colwidth=colwidth, *args, **kwargs)
		
		# Create the buttons
		btnOk = tk.Button(dlg, text='OK', command=lambda: _onDlgButton(dlg, newConfig.getConfig()))
		btnCancel = tk.Button(dlg, text='Cancel', command=lambda: _onDlgButton(dlg))
		btnOk.grid(column=0, row=row)
		btnCancel.grid(column=1, row=row)

		# Wait for dialog window to be closed, then return True for OK and False fro CANCEL
		dlg.wait_window()
		return result

	# Called when widget value has changed
	def _onChange(self, id: str, value):
		if id in self.idList:
			self.config[id] = value

