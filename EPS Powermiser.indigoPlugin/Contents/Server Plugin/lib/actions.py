# eps.actions - Manage and execute actions
#
# Copyright (c) 2016 ColoradoFourWheeler / EPS
#

import indigo
import logging

import ext
import dtutil

class actions:	

	#
	# Initialize the  class
	#
	def __init__(self, factory):
		self.logger = logging.getLogger ("Plugin.actions")
		self.factory = factory
		self.maxFields = 10 # Max number of fields to populate for ConfigUI actions
	
	#
	# Compile action options and run them
	#
	def runAction (self, propsDict, method = "Pass"):
		try:
			# Check that we have either a strValuePassOn or strValueFailOn, if we don't then this is either
			# not an action or it's a pseudo action device that the plugin is handling one-off
			if ext.valueValid (propsDict, "isActionConfig") == False:
				self.logger.threaddebug ("The current device is not an action device, not running action")
				return False
				
			# See if we are allowing multiple objects, if not default to device
			objType = "device"
		
			# If we are allowing multiple objects make sure our selection is valid
			if ext.valueValid (propsDict, "if" + method):
				if ext.valueValid (propsDict, "if" + method, True):
					objType = propsDict["if" + method]
				
				else:
					# It's blank or a line or something, just skip
					self.logger.warn ("No method was selected for an action, it cannot be run")
					return False
			
			if objType == "device":
				if ext.valueValid (propsDict, "device" + method, True):
					# No sense proceeding here unless they selected an action so we know what options to turn on
					if ext.valueValid (propsDict, "deviceAction" + method, True):		
						dev = indigo.devices[int(propsDict["device" + method])]
						
						# Get the action list from plugcache for this device
						actions = self.factory.plugcache.getActions (dev)
						
						args = {}
						actionItem = None
						rawAction = ""
						
						fieldIdx = 1
						for id, action in actions.iteritems():
							if id == propsDict["deviceAction" + method]:
								actionItem = action
								rawAction = id
								
								if "ConfigUI" in action:
									if "Fields" in action["ConfigUI"]:
										for field in action["ConfigUI"]["Fields"]:
											args[field["id"]] = self._getGroupFieldValue (propsDict, method, field["ValueType"], field["Default"], fieldIdx)
											fieldIdx = fieldIdx + 1			
						
						
						return self._executeAction (dev, rawAction, actionItem, args)
						
			if objType == "variable":
				if ext.valueValid (propsDict, "variable" + method, True):
					# No sense proceeding here unless they selected an action so we know what options to turn on
					if ext.valueValid (propsDict, "variableAction" + method, True):		
						var = indigo.variables[int(propsDict["variable" + method])]
						
						# Get the action list from plugcache for this device
						actions = self.factory.plugcache.getActions (var)
						
						args = {}
						actionItem = None
						rawAction = ""
						
						fieldIdx = 1
						for id, action in actions.iteritems():
							if id == propsDict["variableAction" + method]:
								actionItem = action
								rawAction = id
								
								if "ConfigUI" in action:
									if "Fields" in action["ConfigUI"]:
										for field in action["ConfigUI"]["Fields"]:
											args[field["id"]] = self._getGroupFieldValue (propsDict, method, field["ValueType"], field["Default"], fieldIdx)
											fieldIdx = fieldIdx + 1			
						
						
						return self._executeAction (var, rawAction, actionItem, args)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True
		
	#
	# Execute an action
	#
	def _executeAction (self, obj, rawAction, action, args):	
		try:
			self.logger.info ("Executing Indigo action {0}".format(action["Name"]))
			
			#indigo.server.log(unicode(action))
			#indigo.server.log(rawAction)
			#indigo.server.log(unicode(args))
			
			# Check if we have a known custom command
			if rawAction == "indigo_match":
				# Custom dimmer command to match brightness
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				
				for devId in args["devices"]:
					indigo.dimmer.setBrightness (int(devId), value=obj.states["brightnessLevel"], delay=args["delay"])
					
			elif rawAction == "indigo_insertTimeStamp":
				# Insert pre-formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.variable.updateValue(obj.id, value=indigo.server.getTime().strftime("%Y-%m-%d %H:%M:%S"))
				
			elif rawAction == "indigo_insertTimeStamp_2":
				# Insert custom formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				indigo.variable.updateValue(obj.id, value=indigo.server.getTime().strftime(args["format"]))
				
			elif rawAction == "indigo_setVarToVar":
				# Insert custom formatted timestamp into variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				var = indigo.variables[obj.id]
				copyVar = indigo.variables[args["variable"]]
				
				indigo.variable.updateValue(obj.id, value=copyVar.value)
				
			elif rawAction == "indigo_toggle_3":
				# Toggle between various true/false values in variable
				self.logger.threaddebug ("Executing custom command {0} using arguments {1}".format(rawAction, unicode(args)))
				
				var = indigo.variables[obj.id]
				oldVal = var.value
				newVal = "true"
				
				if args["value"] == "truefalse":
					if oldVal.lower() == "true":
						newVal = "false"
					else:
						newVal = "true"
						
				elif args["value"] == "onoff":
					if oldVal.lower() == "on":
						newVal = "off"
					else:
						newVal = "on"
						
				elif args["value"] == "yesno":
					if oldVal.lower() == "yes":
						newVal = "no"
					else:
						newVal = "yes"
						
				elif args["value"] == "enabledisable":
					if oldVal.lower() == "enable":
						newVal = "disable"
					else:
						newVal = "enable"
						
				elif args["value"] == "openclose":
					if oldVal.lower() == "open":
						newVal = "close"
					else:
						newVal = "open"
						
				elif args["value"] == "unlocklock":
					if oldVal.lower() == "unlock":
						newVal = "lock"
					else:
						newVal = "unlock"
						
				indigo.variable.updateValue(obj.id, value=newVal)
				
			elif rawAction[0:7] == "indigo_":
				# An indigo action
				rawAction = rawAction.replace("indigo_", "")
				
				topFunc = None
				if type(obj) is indigo.RelayDevice: topFunc = indigo.relay
				if type(obj) is indigo.DimmerDevice: topFunc = indigo.dimmer
				if type(obj) is indigo.indigo.MultiIODevice: topFunc = indigo.iodevice
				if type(obj) is indigo.SensorDevice: topFunc = indigo.sensor
				if type(obj) is indigo.SpeedControlDevice: topFunc = indigo.speedcontrol
				if type(obj) is indigo.SprinklerDevice: topFunc = indigo.sprinkler
				if type(obj) is indigo.ThermostatDevice: topFunc = indigo.thermostat
				
				if type(obj) is indigo.Variable: topFunc = indigo.variable
				
				func = getattr (topFunc, rawAction)
				
				self.logger.threaddebug ("Sending command to {0} using arguments {1}".format(unicode(func), unicode(args)))
				
				if len(args) > 0:
					func(obj.id, **args)
				else:
					func(obj.id)
					
			else:
				# A plugin action
				rawAction = rawAction.replace("plugin_", "")
				
				plugin = indigo.server.getPlugin (obj.pluginId)
				if plugin.isEnabled() == False:
					self.logger.error ("Unabled to run '{0}' on plugin '{1}' because the plugin is disabled".format(action["Name"], plugin.pluginDisplayName))
					return False
					
				self.logger.threaddebug ("Running action '{0}' for '{1}' using arguments {2}".format(rawAction, plugin.pluginDisplayName, unicode(args)))
				self.logger.info ("Running '{0}' action '{1}'".format(plugin.pluginDisplayName, action["Name"]))
			
				
				ret = None
				
				#indigo.server.log(rawAction)
				#indigo.server.log(unicode(args))
				
				try:
					ret = plugin.executeAction (rawAction, deviceId=obj.id, props=args)	
					
				except Exception as e:
					self.logger.error (ext.getException(e))	
					self.factory.plug.actionGotException (action, obj.id, args, e)
					
				if ret is not None and ret != "":
					self.factory.plug.actionReturnedValue (action, obj.id, args, ret)
			
			return True
						
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		
		
	#
	# Get the group field value for a given group ID
	#
	def _getGroupFieldValue (self, propsDict, method, type, default, index):
		ret = ""
		
		try:
			if ext.valueValid (propsDict, "optionGroup" + method + str(index), True):
				if propsDict["optionGroup" + method + str(index)] == "textfield":
					ret = propsDict["strValue" + method + str(index)]
					
				elif propsDict["optionGroup" + method + str(index)] == "menu":
					ret = propsDict["menuValue" + method + str(index)]
					
				elif propsDict["optionGroup" + method + str(index)] == "list":
					ret = propsDict["listValue" + method + str(index)]
					
				elif propsDict["optionGroup" + method + str(index)] == "checkbox":
					ret = propsDict["checkValue" + method + str(index)]
				
				if ret is None or ret == "": ret = default
				
				if ret != "":
					if type == "integer": 
						ret = int(ret)
						
					elif type == "delay":
						# Convert HH:MM:SS to seconds
						timeStr = ret.split(":")
						ret = 0
						
						if len(timeStr) == 3:
							ret = ret + (int(timeStr[0]) * 1440)
							ret = ret + (int(timeStr[1]) * 60)
							ret = ret + int(timeStr[2])
							
					elif type == "list":
						# Converts a string or comma delimited string to a list
						data = ret.split(",")
						ret = []
						
						for d in data:
							ret.append(d.strip())
					
					elif type == "indigo_enum":
						# The value is the enum to lookup
						ret = ret.replace("indigo.", "")
						data = ret.split(".")

						ret = getattr (indigo, data[0])
						ret = getattr (ret, data[1])
					
					else:
						# It's a string
						ret = ret
					
					
				
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret
		
	#
	# Get the option value for the provided key value
	#
	def _getOptionValue (self, propsDict, method, keyValue, isAction = False):
		ret = keyValue # failsafe
		
		try:
			fieldValue = ""
			
			if keyValue.lower() == "id": 
				if isAction == False:
					if ext.valueValid (propsDict, "device" + method, True):
						return int(propsDict["device" + method])
					else:
						return 0
			
			if keyValue.lower() == "intvalue": 
				if ext.valueValid (propsDict, "intValue" + method, True):
					return int(propsDict["intValue" + method])
				else:
					return 0
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
						
		return ret
		
	#
	# Execute an action
	#
	def _executeActionEx (self, action, args):
		try:
			if action is None: return False
			
			# Break down the ID so we can determine the source
			command = action.id.split(".")
			topFunc = ""
			
			if command[0] == "indigo":
				# Built in action
				if command[1] == "DimmerDevice": topFunc = indigo.dimmer
				if command[1] == "RelayDevice": topFunc = indigo.relay
				if command[1] == "SprinklerDevice": topFunc = indigo.sprinkler
				if command[1] == "SensorDevice": topFunc = indigo.sensor
				if command[1] == "SpeedControlDevice": topFunc = indigo.speedcontrol
				if command[1] == "ThermostatDevice": topFunc = indigo.thermostat
				
				func = getattr (topFunc, command[len(command) - 1])
			
				self.logger.threaddebug ("Sending command to {0} using arguments {1}".format(unicode(func), unicode(args)))
				self.logger.info ("Executing Indigo action {0}".format(action.name))
				
				if len(args) > 0:
					func(*args)
				else:
					func()
				
			else:
				# It's a plugin
				indigo.server.log("PLUGIN")
				pluginId = command[0].replace(":", ".")
				plugin = indigo.server.getPlugin (pluginId)
				if plugin.isEnabled() == False:
					self.logger.error ("Unabled to run '{0}' on plugin '{1}' because the plugin is disabled".format(command[len(command) - 1], plugin.pluginDisplayName))
					return False
					
				#indigo.server.log(unicode(plugin))
				#indigo.server.log(unicode(command))
				#indigo.server.log(unicode(action))
				#indigo.server.log(unicode(args))
				
				self.logger.threaddebug ("Running action '{0}' for '{1}' using arguments {2}".format(command[len(command) - 1], plugin.pluginDisplayName, unicode(args)))
				self.logger.info ("Running '{0}' action '{1}'".format(plugin.pluginDisplayName, action.name))
			
				# The first arg should be the ID, the rest are props, put together the line
				id = args[0]
				props = {}
				
				if len(args) > 1:
					for i in range (1, len(args)):
						props[args[i]] = args[i]
					
				ret = None
				
				try:
					ret = plugin.executeAction (command[len(command) - 1], id, props=props)	
					
				except Exception as e:
					self.logger.error (ext.getException(e))	
					self.factory.plug.actionGotException (action, id, props, e)
				
				if ret is not None and ret != "":
					self.factory.plug.actionReturnedValue (action, id, props, ret)
			
			
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return False
			
		return True
		
	#
	# Set up any UI defaults that we need
	#
	def setUIDefaults (self, propsDict, defaultCondition = "disabled", defaultState = "onOffState"):
		try:
			# Check that we have either a strValuePassOn or strValueFailOn, if we don't then this is either
			# not an action or it's a pseudo action device that the plugin is handling one-off
			if ext.valueValid (propsDict, "isActionConfig") == False and ext.valueValid (propsDict, "strValueFailOn") == False:
				self.logger.threaddebug ("The current device is not an action device, not setting defaults")
				return propsDict
				
			for i in range (0, 2):
				method = "Pass"
				if i == 1: method = "Fail"
				
				if ext.valueValid (propsDict, "optionLabel" + method + "1") == False: continue # may not have pass or may not have fail
				
				# See if we are allowing multiple objects, if not default to device
				objType = "device"
			
				# If we are allowing multiple objects make sure our selection is valid
				if ext.valueValid (propsDict, "if" + method):
					if ext.valueValid (propsDict, "if" + method, True):
						objType = propsDict["if" + method]
					
					else:
						# It's blank or a line or something, just skip
						continue
						
				# Assume no fields unless we find some
				maxFormFields = 0
				for j in range (1, self.maxFields): 
					if ext.valueValid (propsDict, "optionGroup" + method + str(j)):
						propsDict["optionGroup" + method + str(j)] = "hidden" 
						maxFormFields = maxFormFields + 1
						
				# Assume this action can be run
				propsDict["showWarning"] = False
				propsDict["showFieldWarning"] = False
				
				
					
				if objType == "variable":	
					if ext.valueValid (propsDict, "variable" + method, True):
						# No sense proceeding here unless they selected an action so we know what options to turn on
						if ext.valueValid (propsDict, "variableAction" + method, True):	
							var = indigo.variables[int(propsDict["variable" + method])]
				
							# Get the action list from plugcache for this device
							actions = self.factory.plugcache.getActions (var)
							fieldIdx = 1
							for id, action in actions.iteritems():
								if id == propsDict["variableAction" + method]:
									if "ConfigUI" in action:
										if "Fields" in action["ConfigUI"]:
											# First make sure we have enough fields to support the action
											if len(action["ConfigUI"]["Fields"]) > maxFormFields: propsDict["showFieldWarning"] = True
											
											for field in action["ConfigUI"]["Fields"]:
												propsDict = self._addFieldToUI (propsDict, var, action, field, method, fieldIdx)
												fieldIdx = fieldIdx + 1
						
				elif objType == "device":
					if ext.valueValid (propsDict, "device" + method, True):
						# No sense proceeding here unless they selected an action so we know what options to turn on
						if ext.valueValid (propsDict, "deviceAction" + method, True):	
							dev = indigo.devices[int(propsDict["device" + method])]
				
							# Get the action list from plugcache for this device
							actions = self.factory.plugcache.getActions (dev)
							fieldIdx = 1
							for id, action in actions.iteritems():
								if id == propsDict["deviceAction" + method]:
									if "ConfigUI" in action:
										if "Fields" in action["ConfigUI"]:
											# First make sure we have enough fields to support the action
											if len(action["ConfigUI"]["Fields"]) > maxFormFields: propsDict["showFieldWarning"] = True
											
											for field in action["ConfigUI"]["Fields"]:
												propsDict = self._addFieldToUI (propsDict, dev, action, field, method, fieldIdx)
												fieldIdx = fieldIdx + 1
										
							# In case our actions caused the developer warning, turn off all field options
							if propsDict["showWarning"] or propsDict["showFieldWarning"]:
								for j in range (1, self.maxFields): 
									if ext.valueValid (propsDict, "optionGroup" + method + str(j)):
										propsDict["optionGroup" + method + str(j)] = "hidden" 
										
							# In case we got a developer warning make sure the field warning is off
							if propsDict["showWarning"]: propsDict["showFieldWarning"] = False
										
							
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return propsDict
		
	#
	# Build dynamic configUI fields
	#
	def _addFieldToUI (self, propsDict, obj, action, field, method, fieldIdx):
		try:
			if ext.valueValid (propsDict, "optionGroup" + method + str(fieldIdx)):
				# See if this is a self callback, in which case we need to disable the action
				if len(field["List"]) > 0:
					for listItem in field["List"]:
						if listItem["class"] == "self":
							msg = "\n" + self.factory.ui.debugHeaderEx ()
							msg += self.factory.ui.debugLine ("Incompatible Device Action")
							msg += self.factory.ui.debugLine (" ")
							msg += self.factory.ui.debugLine ("Plugin Device: " + obj.name)
							msg += self.factory.ui.debugLine ("Action       : " + action["Name"])
							msg += self.factory.ui.debugLine (" ")
							msg += self.factory.ui.debugLine ("This action cannot be called because the plugin that manages it")
							msg += self.factory.ui.debugLine ("requires that one or more of their fields must 'callback' to")
							msg += self.factory.ui.debugLine ("their plugin in order for the action to work properly.")
							msg += self.factory.ui.debugLine (" ")
							msg += self.factory.ui.debugLine ("Please consider asking the developer of the plugin to add support")
							msg += self.factory.ui.debugLine ("for " + self.factory.plugin.pluginDisplayName + " by")
							msg += self.factory.ui.debugLine ("visiting our forum topic regarding developer API's.")

							msg += self.factory.ui.debugHeaderEx ()

							self.logger.warn (msg)
							
							propsDict["showWarning"] = True
					
			
				if field["hidden"]: return propsDict # never show hidden fields
				
				if field["Label"] != "":
					propsDict["optionLabel" + method + str(fieldIdx)] = field["Label"]
				else:
					propsDict["optionLabel" + method + str(fieldIdx)] = field["Description"]
			
				propsDict["optionGroup" + method + str(fieldIdx)] = field["type"]
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return propsDict
	
	#
	# Called from UI if the custom list type is "actionoptionlist"
	#
	def getActionOptionUIList (self, args, valuesDict):
		ret = [("default", "No data")]
		
		try:
			retList = []
			
			if ext.valueValid (args, "group", True) and ext.valueValid (args, "method", True): 
				group = args["group"]
				method = args["method"]
				
				objType = "device"
				if ext.valueValid (valuesDict, "if" + method, True):
					if valuesDict["if" + method] == "variable": objType = "variable"
				
				# In order to populate we have to have a device and an action
				if ext.valueValid (valuesDict, objType + method, True):
					if objType == "device": obj = indigo.devices[int(valuesDict[objType + method])]
					if objType == "variable": obj = indigo.variables[int(valuesDict[objType + method])]
					listData = self._getActionOptionUIList (obj, objType, valuesDict, method)
					
					listIdx = 1
					for listItem in listData:
						# Only return the list for this group
						if listIdx != int(group):
							listIdx = listIdx + 1
							continue
					
						#indigo.server.log(unicode(listItem))
						#indigo.server.log(unicode(listItem["Options"]))
					
						if len(listItem["Options"]) > 0:
							for opt in listItem["Options"]:
								if opt["value"] == "-line-":
									option = ("-line-", self.factory.ui.getSeparator())						
								else:
									option = (opt["value"], opt["Label"])
	
								retList.append (option)
								
						elif listItem["class"] == "indigo.dimmer":
							for d in indigo.devices.iter("indigo.dimmer"):
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "indigo.devices":
							for d in indigo.devices:
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "indigo.variables":
							for d in indigo.variables:
								option = (d.id, d.name)
								retList.append (option)
								
						elif listItem["class"] == "custom.zonenames":
							for i in range (0, 8):
								if dev.zoneEnableList[i]:
									option = (str(i + 1), dev.zoneNames[i])
									retList.append (option)
													
						listIdx = listIdx + 1
						
					
				
				if len(retList) > 0: return retList
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			return ret
		
		return ret
		
	#
	# Get list data from plugcache (called from getActionOptionUIList)
	#
	def _getActionOptionUIList (self, obj, objType, valuesDict, method):
		try:
			actions = self.factory.plugcache.getActions (obj)
					
			for id, action in actions.iteritems():
				if id == valuesDict[objType + "Action" + method]:
					if "ConfigUI" in action:
						if "Fields" in action["ConfigUI"]:
							for field in action["ConfigUI"]["Fields"]:
								return field["List"]
											
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return []
		
	#
	# Validate the UI
	#
	def validateDeviceConfigUi(self, valuesDict, typeId, devId):
		self.logger.debug ("Validating action parameters on device")
		errorDict = indigo.Dict()
		msg = ""
		
		try:
			# Check that we have either a strValuePassOn or strValueFailOn, if we don't then this is either
			# not an action or it's a pseudo action device that the plugin is handling one-off
			if ext.valueValid (valuesDict, "isActionConfig") == False:
				self.logger.threaddebug ("The current device is not an action device, not validating actions")
				return (True, valuesDict, errorDict)
				
			# Make sure no -line- items are selected
			for i in range (0, 1):
				method = "Pass"
				if i == 1: method = "Fail"
				
				if ext.valueValid (valuesDict, "optionLabel" + method + "1") == False: continue # may not have pass or may not have fail
				
				for j in range (1, self.maxFields): 
					if ext.valueValid (valuesDict, "menuValue" + method + str(j)):
						if valuesDict["menuValue" + method + str(j)] == "-line-":
							msg += "Field {0} has a line selected.  ".format(str(j))
							errorDict["menuValue" + method + str(j)] = "Invalid selection"
							
				
			if msg != "":
				msg = "There are problems with your conditions:\n\n" + msg
				errorDict["showAlertText"] = msg
				return (False, valuesDict, errorDict)
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return (True, valuesDict, errorDict)







































		