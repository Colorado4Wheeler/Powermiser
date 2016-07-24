# Device definitions:
#
#	command | label | values | options
#
#	Command: the destination actionId to execute
#	Label: What to show the user or ~|~|~|~ for a separator
#
#	Values: id or optX = fieldPrefix,defaultValue
#		opt1 - opt9 = No valuesDict passed, the function options in that order
#		[field] = [numValue | strValue | boolValue] where [field] is the valuesDict field id
#		[opt | field] = [optValue | lstValue] sends list array
#		[opt | field] = [...] {...} values as a list or dict - values must be separated by commas
#	
#	Options: fieldPrefix = command
#		command options:
#			[optValue | lstValue] = value:label,value:label...
#			[optValue | lstValue] = indigo.[devices | dimmer | sprinkler...]
#			[optValue | lstValue] = pluginId[.deviceTypeId]
#			

ACTION_INDEX =		[
	"property|"
]

INDIGO_DIMMER = 	[
	"setBrightness|Set Brightness|opt1=id,opt2=numValue|", 
	"brighten|Brighten by %|opt1=id,opt2=numValue|", 
	"dim|Dim by %|opt1=id,opt2=numValue|", 
	"match|Match Brightness|opt1=id,opt2=numValue|"
]

INDIGO_RELAY = 		[
	"turnOn|Turn On|opt1=id|", 
	"turnOff|Turn Off|opt1=id|", 
	"toggle|Toggle On/Off|opt1=id|"
]

INDIGO_SPRINKLER =	[
	"run|Run Schedule|opt1=id,opt2=[numValue]|",
	"pause|Pause Schedule|opt1=id",
	"resume|Resume Schedule|opt1=id",
	"stop|Stop (all zones off & clear schedule)|opt1=id",
	"~|~|~|~",
	"previousZone|Activate Previous Zone|opt1=id|",
	"nextZone|Activate Next Zone|opt1=id|",
	"~|~|~|~",
	"setActiveZone|Turn On Specific Zone|opt1=id,opt2=numValue|"
]