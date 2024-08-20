
import tkinter as tk

from tkconfigure import TKConfigure

class TKCDialog:

	def __init__(self, config: TKConfigure):
		self.newConfig = TKConfigure(config.getParameterDefinition(), config.getConfig())
			  
	def show(self, master, width: int, height: int, title: str = None, padx: int = 0, pady: int = 0, groups: list = [],
					colwidth: tuple = (50.0, 50.0), *args, **kwargs):
		# Create a copy of current configuration
		newConfig = TKConfigure(self.getParameterDefinition(), self.getConfig())

		self.dlg = tk.Toplevel(master)
		self.dlg.geometry(f"{width}x{height}")
		self.dlg.grab_set()
		self.dlg.title(title)

		row = newConfig.createMask(self.dlg, startrow=0, padx=padx, pady=pady, groups=groups, groupwidth=width-padx*2,
			colwidth=colwidth, *args, **kwargs)
		
		btnOk = tk.Button(self.dlg, text='OK', command=lambda: self.onDlgButton(newConfig))
		btnCancel = tk.Button(self.dlg, text='Cancel', command=self.onDlgButton)
		btnOk.grid(column=0, row=row)
		btnCancel.grid(column=1, row=row)

		self.dlg.wait_window()
	
	def onDlgButton(self, config: dict | None = None):
		if config is not None:
			self.setConfig(config)
		self.dlg.destroy()