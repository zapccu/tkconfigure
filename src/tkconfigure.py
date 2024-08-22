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
#   Config = TKConfigure(parameterDefinition , configValues)
#
# Parameters:
#
#   parameterDefinition - dictionary with definition of config parameters
#   configValues - dictionary with parameter values
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
# Parameter value dictionary:
#
# {
#    "parameter-name": parameter-value,
#    ...
# }
#
###############################################################################

class TKConfigure:

	def __init__(self, parameterdefinition: dict | None = None, config: dict | None = None):

		# Allowed parameter definition keys. Can be enhanced by method addKey()
		self.attributes = [ 'inputType', 'valRange', 'initValue', 'widget', 'label', 'width', 'widgetAttr' ]

		# Default values for parameter attributes
		self.defaults = {
			'inputType':  'str',
			'valRange':   None,
			'initValue':  '',
			'widget':     'TKCEntry',
			'label':      '',
			'width':      20,
			'widgetAttr': {}
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
		if group not in self.parDef: raise KeyError("Unknown parameter group", group)
		if id not in self.parDef[group]: raise KeyError("Unknown parameter id", id)

		inputType = self.getPar(group, id, 'inputType')
		initValue = self.getPar(group, id, 'initValue')
		valRange  = self.getPar(group, id, 'valRange')
		nInitValue = initValue

		# Validate inputType and initValue
		if inputType == 'str' and type(initValue) is not str:
			raise TypeError("Type of initValue doesn't match inputType for parameter", id)
		elif inputType == 'int' and type(initValue) is float:
			nInitValue = int(initValue)
		elif inputType == 'float' and type(initValue) is int:
			nInitValue = float(initValue)
			
		# Validate initValue and valRange
		if type(valRange) is list:
			if inputType != 'int' and inputType != 'str':
				raise ValueError("inputType not allowed for valRange list for parametet", id)
			if type(initValue) is str and initValue not in valRange:
				raise ValueError("initValue not in valRange for parameter", id)
			elif type(initValue) is int and (initValue < 0 or initValue >= len(valRange)):
				raise IndexError("initValue not in valRange for parameter", id)
			elif type(initValue) is float or initValue is None:
				raise TypeError("Type of initValue doesn't match inputType for parameter", id)
		elif type(valRange) is tuple:
			if type(initValue) is str:
				raise TypeError("initValue of parameter", id)
			elif initValue < valRange[0] or initValue > valRange[1]:
				raise ValueError("initValue out of valRange for parameter", id)

		if type(nInitValue) is not type(initValue):
			self.parDef[group][id]['initValue'] = nInitValue
		self.set(id, nInitValue)
	
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
				if id in self.idList: raise KeyError("Duplicate parameter id", id)
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
		if group is None or group not in self.parDef: raise KeyError("Unknown parameter group", group)
		return self.parDef[group]
	
	# Get parameter id definition as dictionary
	def getIdDefinition(self, id: str) -> dict:
		if id is None or id not in self.idList: raise KeyError("Unknown parameter id", id)
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

	# Get parameter attribute(s)
	def getPar(self, group: str, id: str, attribute: str | None = None):
		if group not in self.parDef: raise KeyError("Unknown parameter group", group)
		if id not in self.parDef[group]: raise KeyError("Unknown parameter id", id)

		if attribute is None:
			return self.parDef[group][id]
		elif attribute not in self.attributes:
			raise KeyError("Unknown attribute", attribute)
		elif attribute in self.parDef[group][id]:
			return self.parDef[group][id][attribute]
		else:
			return self.defaults[attribute]

	# Set current config from dictionary
	def setConfig(self, config: dict):
		for id in config:
			if id not in self.idList: raise KeyError("Unknown parameter id", id)
		self.config = config

	# Get current config as dictionary
	def getConfig(self) -> dict:
		return self.config

	# Get parameter value
	def get(self, id: str, returnDefault: bool = True):
		if id not in self.idList: raise KeyError("Unknown parameter id", id)
		if id in self.config and 'value' in self.config[id]:
			return self.config[id]['value']
		elif returnDefault:
			return self.getPar(self.idList[id], id, 'initValue')
		else:
			raise ValueError("No value assigned parameter", id)
		
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
	def set(self, id: str, newValue):
		if id not in self.idList: raise KeyError("Unknown parameter id", id)
		if id not in self.config or 'value' not in self.config[id]:
			self.config.update({ id: { 'oldValue': newValue, 'value': newValue }})
		else:
			curValue = self.config.get(id, {}).get('value')
			if newValue != curValue:
				self.config.update({ id: { 'oldValue': curValue, 'value': newValue }})
		
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

	# Copy parameter values to old values. This is done automatically before an input mask is shown
	def apply(self, groups: list = [], id: str | None = None):
		if id is None:
			for i in self.config:
				self.apply(groups, i)
		elif id in self.config and len(groups) == 0 or self.idList[id] in groups and 'value' in self.config[id]:
			self.config[id]['oldValue'] = self.config[id]['value']

	# Sync widget value(s) with current config value(s)
	def syncWidget(self, id: str | None = None):
		if id is None:
			for i in self.widget:
				if i in self.config:
					v = self.get(i)
					self.widget[i].set(self.get(i))
		elif id not in self.widget:
			raise KeyError("Unknown widget id", id)
		elif id in self.config:
			self.widget[id].set(self.get(id))

	# Sync current config with widget value(s)
	# Usually this function is not needed. Configuration is synced automatically when a widget value has been changed
	def syncConfig(self, id: str | None = None):
		if id is None:
			for id in self.config:
				if id in self.widget:
					self.set(id, self.widget[id].get())
		elif id not in self.config:
			raise KeyError("Unknown parameter id", id)
		else:
			self.set(id, self.widget[id].get())

	# Create widgets for specified parameter group, return number of next free row
	def createWidgets(self, master, group: str = '', singlecol: bool = False, startrow: int = 0, padx=0, pady=0, *args, **kwargs):
		row = startrow

		for id in self.parDef[group]:
			# Create the input widget
			widgetClass = globals()[self.getPar(group, id, 'widget')]
			justify = 'left' if self.getPar(group, id, 'inputType') == 'str' else 'right'
			self.widget[id] = widgetClass(master, id=id, inputType=self.getPar(group, id, 'inputType'), valRange=self.getPar(group, id, 'valRange'),
					initValue=self.get(id), onChange=self._onChange, justify=justify, width=self.getPar(group, id, 'width'), *args, **kwargs)
			
			# Set parameter specific widget attributes
			widgetAttr = self.getPar(group, id, 'widgetAttr')
			if len(widgetAttr) > 0:
				self.widget[id].config(**widgetAttr)

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

		# Apply current parameter values
		self.apply(grpList)

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
		# newConfig = TKConfigure(self.getParameterDefinition(), self.getConfig())

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
			self.set(id, value)

def TKConfigureCopy(config: TKConfigure) -> TKConfigure:
	return TKConfigure(config.getParameterDefinition(), config.getConfig())
