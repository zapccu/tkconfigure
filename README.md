# tkconfigure
TkInter based python app configuration

A configuration is a dictionary with the following syntax:

```
{
	"Widgetgroup-1": {
		"parameter-1": {
			"inputtype": 'int' | 'float' | 'complex' | 'str' | 'bits',
			"valrange":  tuple | list,
			"initvalue": value,
			"widget":    'TKCEntry' | 'TKCSpinner' | 'TKCListbox' | 'TKCFlags' | 'TKCRadiobuttons' | 'TKCSlider',
			"label":     "Text",
			"width":     num-value,
			"widgetattr": {
				"attr": "value",
				"..."
			}
		},
		"...": {
			"..."
		}
	},
	"...": {
		"..."
	}
}
```

To define a new configuration, simply pass the dictionary with the parameter defintion to the constructor TKConfigure(). Example:

```
import TKConfigure as tkc

parameterDefiniton = {
	"": {
		"parameter1": {
			"inputtype": 'int',
			"valrange:   (0, 10),
			"initvalue": 0,
			"widget":    'TKCEntry',
			"label":     "Parameter one",
			"width":     8 
		},
		"parameter1": {
			"inputtype": 'int',
			"valrange:   (0, 10, 1),
			"initvalue": 0,
			"widget":    'TKCSlider',
			"label":     "Parameter two"
		},
	}
}
mySettings = tkc.TKConfigure(parameterDefintion)
```

To assign a value to settings parameters, 3 methods are available:

```
mySettings['parameter1'] = 5
mySettings.set('parameter1', 5)
mySettings.setValues(parameter1=5, parameter2=7)
```

Similar functions are available for reading settings parameters:

```
value = mySettings['parameter1']
value = mySettings.get('parameter1')
value1, value2 = mySettings.getValues('parameter1', 'parameter2')
```

To show an input mask for settings parameters:

```
mySettings.createMask()
```
