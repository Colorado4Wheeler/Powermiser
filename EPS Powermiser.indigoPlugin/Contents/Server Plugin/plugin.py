#! /usr/bin/env python
# -*- coding: utf-8 -*-

import indigo

import os
import sys
import time
import datetime

from eps.cache import cache
from eps.conditions import conditions
from eps import ui
from eps import dtutil
from eps import eps
import re
from datetime import timedelta
from bs4 import BeautifulSoup
import urllib2

import ast

################################################################################
# RELEASE NOTES
################################################################################

# June 24, 2016
#	- Added updateCheck
#	- Added import of timedelta, re and BeautifulSoup
#	- Added updateCheck to first action of onConcurrentThread
#	- Added menu option to check for updates
#	- Added self.pluginUrl as a startup option (points to forum thread with hidden version info)

# June 20, 2016
#   - setStateDisplay added as an EPS routine to set the state icon and text
#	- deviceStartComm modified to call setStateDisplay at the end of the routine
#	- onConcurrentThread modified to call setStateDisplay as the last statement

################################################################################
class Plugin(indigo.PluginBase):
	
	#
	# Init
	#
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		# EPS common startup
		try:
			self.debug = pluginPrefs["debugMode"]
			pollingMode = pluginPrefs["pollingMode"]
			pollingInterval = int(pluginPrefs["pollingInterval"])
			pollingFrequency = pluginPrefs["pollingFrequency"]
			self.monitor = pluginPrefs["monitorChanges"]
		except:
			indigo.server.log ("Preference options may have changed or are corrupt,\n\tgo to Plugins -> %s -> Configure to reconfigure %s and then reload the plugin.\n\tUsing defaults for now, the plugin should operate normally." % (pluginDisplayName, pluginDisplayName), isError = True)
			self.debug = False
			pollingMode = "realTime"
			pollingInterval = 1
			pollingFrequency = "s"
			self.monitor = False
			
		# EPS common variables and classes
		self.pluginUrl = "http://forums.indigodomo.com/viewtopic.php?f=196&t=16343"
		eps.parent = self
		self.reload = False
		self.cache = cache (self, pluginId, pollingMode, pollingInterval, pollingFrequency)
		self.cond = conditions (self)
		
		# EPS plugin specific variables and classes
		
			
	################################################################################
	# EPS ROUTINES
	################################################################################
	
	#
	# Plugin menu: Performance options
	#
	def performanceOptions (self, valuesDict, typeId):
		self.debugLog(u"Saving performance options")
		errorsDict = indigo.Dict()
		
		# Save the performance options into plugin prefs
		self.pluginPrefs["pollingMode"] = valuesDict["pollingMode"]
		self.pluginPrefs["pollingInterval"] = valuesDict["pollingInterval"]
		self.pluginPrefs["pollingFrequency"] = valuesDict["pollingFrequency"]
		
		self.cache.setPollingOptions (valuesDict["pollingMode"], valuesDict["pollingInterval"], valuesDict["pollingFrequency"])
		
		return (True, valuesDict, errorsDict)
		
	#
	# Plugin menu: Library versions
	#
	def showLibraryVersions (self, forceDebug = False):
		s =  eps.debugHeader("LIBRARY VERSIONS")
		s += eps.debugLine (self.pluginDisplayName + " - v" + self.pluginVersion)
		s += eps.debugHeaderEx ()
		s += eps.debugLine ("Cache %s" % self.cache.version)
		s += eps.debugLine ("Conditions %s" % self.cond.version)
		s += eps.debugLine ("UI %s" % ui.libVersion(True))
		s += eps.debugLine ("DateTime %s" % dtutil.libVersion(True))
		s += eps.debugLine ("Core %s" % eps.libVersion(True))
		s += eps.debugHeaderEx ()
		
		if forceDebug:
			self.debugLog (s)
			return
			
		indigo.server.log (s)
		
	#
	# Device action: Update
	#
	def updateDevice (self, devAction):
		dev = indigo.devices[devAction.deviceId]
		
		children = self.cache.getSubDevices (dev)
		for devId in children:
			subDev = indigo.devices[int(devId)]	
			self.updateDeviceStates (dev, subDev)	
		
		return
			
	#
	# Update device
	#
	def updateDeviceStates (self, parentDev, childDev = None):
		stateChanges = self.cache.deviceUpdate (parentDev)
		
		return
		
	#
	# Add watched states
	#
	def addWatchedStates (self, subDevId = "*", deviceTypeId = "*", mainDevId = "*"):
		
		self.cache.addWatchState ("onOffState", subDevId, "AutoOff")
		
		#self.cache.addWatchState (848833485, "onOffState", 1089978714)
		
		#self.cache.addWatchState ("onOffState", subDevId, deviceTypeId, mainDevId) # All devices, pass vars
		#self.cache.addWatchState ("onOffState") # All devices, all subdevices, all types
		#self.cache.addWatchState ("onOffState", 848833485) # All devices, this subdevice, all types
		#self.cache.addWatchState ("onOffState", subDevId, "epslcdth") # All devices, all subdevices of this type
		#self.cache.addWatchState ("onOffState", 848833485, "*", 1089978714) # This device, this subdevice of all types
		
		return
		
	#
	# Set state display on the device
	#
	def setStateDisplay (self, dev, force = False):
		stateValue = None
		stateUIValue = ""
		stateIcon = None
		stateDecimals = -1
		
		if dev.deviceTypeId == "devtemplate":
			X = 1 # placeholder
		
		else:
			return # failsafe
				
		if stateValue is None: return # nothing to do
		
		if force == False:
			if "statedisplay.ui" in dev.states:
				if stateValue == dev.states["statedisplay"] and stateUIValue == dev.states["statedisplay.ui"]: return # nothing to do
			else:
				if stateValue == dev.states["statedisplay"]: return # nothing to do
		
		dev.updateStateImageOnServer(stateIcon)
		
		if stateDecimals > -1:
			dev.updateStateOnServer("statedisplay", value=stateValue, uiValue=stateUIValue, decimalPlaces=stateDecimals)
		else:
			dev.updateStateOnServer("statedisplay", value=stateValue, uiValue=stateUIValue)	
	
	################################################################################
	# EPS HANDLERS
	################################################################################
		
	#
	# Device menu selection changed
	#
	def onDeviceSelectionChange (self, valuesDict, typeId, devId):
		return valuesDict
		
	#
	# Device menu selection changed (for MenuItems.xml only)
	#
	def onMenuDeviceSelectionChange (self, valuesDict, typeId):
		# Just here so we can refresh the states for dynamic UI
		return valuesDict
	
	#
	# Return folder list
	#
	def getIndigoFolders(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getIndigoFolders (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of device states to (filter is the device to query)
	#
	def getStatesForDevice(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getStatesForDevice (filter, valuesDict, typeId, targetId)
	
	#
	# Return option array of devices with filter in states (filter is the state(s) to query)
	#
	def getDevicesWithStates(self, filter="onOffState", valuesDict=None, typeId="", targetId=0):
		return ui.getDevicesWithStates (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of device plugin props to (filter is the device to query)
	#
	def getPropsForDevice(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getPropsForDevice (filter, valuesDict, typeId, targetId)
		
	#
	# Return option array of plugin devices props to (filter is the plugin(s) to query)
	#
	def getPluginDevices(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getPluginDevices (filter, valuesDict, typeId, targetId)
		
	#
	# Return custom list
	#
	def getDataList(self, filter="", valuesDict=None, typeId="", targetId=0):
		return ui.getDataList (filter, valuesDict, typeId, targetId)
	
	#
	# Handle ui button click
	#
	def uiButtonClicked (self, valuesDict, typeId, devId):
		return valuesDict
		
	#
	# Concurrent thread process fired
	#
	def onRunConcurrentThread (self):
		self.updateCheck(True, False)
		
		for dev in indigo.devices.iter(self.pluginId):
			if eps.valueValid (dev.states, "autoOffTimes", True):
				if dev.states["autoOffTimes"] != "{}":
					autoOffTimes = ast.literal_eval (dev.states["autoOffTimes"])
					
					for devId, offDict in autoOffTimes.iteritems():
						d = datetime.datetime.strptime (offDict["offTime"], "%Y-%m-%d %H:%M:%S")
						diff = dtutil.DateDiff ("seconds", d, indigo.server.getTime())
						if diff < 0:
							self.debugLog("Turning off device %s" % indigo.devices[int(devId)].name)
							indigo.device.turnOff(devId)
										
				if dev.states["autoOffTimes"] == "{}" and dev.states["statedisplay"] != "off":
					dev.updateStateImageOnServer(indigo.kStateImageSel.PowerOff)
					dev.updateStateOnServer("statedisplay", "off")
					
				if dev.states["autoOffTimes"] != "{}" and dev.states["statedisplay"] == "off":
					dev.updateStateImageOnServer(indigo.kStateImageSel.PowerOn)
					dev.updateStateOnServer("statedisplay", "on")
		
		return
		
	################################################################################
	# EPS CONDITIONS ROUTINES
	################################################################################		
	
	#
	# Conditions field changed
	#
	def onConditionsChange (self, valuesDict, typeId, devId):
		# Just here so we can refresh the states for dynamic UI
		if typeId == "AutoOff":
			valuesDict = self.cond.setUIDefaults (valuesDict, "timebetween")
					
		return valuesDict
		
	#
	# Return conditions library options
	#
	def getConditionsList (self, filter="conditions", valuesDict=None, typeId="", targetId=0):
		if filter.lower() == "conditions": return self.cond.appendUIConditions ([], "all")	
		if filter.lower() == "evals": return self.cond.addUIEvals ([])	
		if filter.lower() == "conditionmenu": return self.cond.addUIConditionMenu ([])	
		
	
	#
	# Return custom list with condition options
	#
	def getConditionDateValues(self, filter="", valuesDict=None, typeId="", targetId=0):
		return self.cond.getConditionDateValues (filter, valuesDict, typeId, targetId)
		
		
	################################################################################
	# EPS ROUTINES TO BE PUT INTO THEIR OWN CLASSES / METHODS
	################################################################################
		
	
	################################################################################
	# INDIGO DEVICE EVENTS
	################################################################################
	
	#
	# Device starts communication
	#
	def deviceStartComm(self, dev):
		self.debugLog(u"%s starting communication" % dev.name)
		dev.stateListOrDisplayStateIdChanged() # Make sure any device.xml changes are incorporated
		if self.cache is None: return
		
		if "lastreset" in dev.states:
			d = indigo.server.getTime()
			if dev.states["lastreset"] == "": dev.updateStateOnServer("lastreset", d.strftime("%Y-%m-%d"))
			
		if eps.valueValid (dev.states, "autoOffTimes", True) == False:
			dev.updateStateOnServer("autoOffTimes", "{}")
				
		if self.cache.deviceInCache (dev.id) == False:
			self.debugLog(u"%s not in cache, appears to be a new device or plugin was just started" % dev.name)
			self.cache.cacheDevices() # Failsafe
			
		self.addWatchedStates("*", dev.deviceTypeId, dev.id) # Failsafe
		#self.cache.dictDump (self.cache.devices[dev.id])

		self.setStateDisplay(dev)
			
		return
			
	#
	# Device stops communication
	#
	def deviceStopComm(self, dev):
		self.debugLog(u"%s stopping communication" % dev.name)
		
	#
	# Device property changed
	#
	def didDeviceCommPropertyChange(self, origDev, newDev):
		self.debugLog(u"%s property changed" % origDev.name)
		return True	
	
	#
	# Insteon command received
	#
	def insteonCommandReceived (self, cmd):
		dev = self.cache.deviceForAddress (cmd.address)
		if dev:
			for devId in dev: 
				self.processRawCommand (indigo.devices[devId], cmd.cmdFunc)
		
	#
	# Insteon command sent
	#
	def insteonCommandSent (self, cmd):
		dev = self.cache.deviceForAddress (cmd.address)
		if dev: 
			for devId in dev: 
				self.processRawCommand (indigo.devices[devId], cmd.cmdFunc, "Indigo") # Outgoing means Indigo sent the command, it's not a button press
			
	#
	# Device property changed
	#
	def deviceUpdated(self, origDev, newDev):
		if self.cache is None: return
		
		if eps.isNewDevice(origDev, newDev):
			self.debugLog("New device '%s' detected, restarting device communication" % newDev.name)
			self.deviceStartComm (newDev)
			return		
		
		if origDev.pluginId == self.pluginId:
			self.debugLog(u"Plugin device %s was updated" % origDev.name)
			
			# Re-cache the device and it's subdevices and states
			if eps.dictChanged (origDev, newDev):
				self.debugLog(u"Plugin device %s settings changed, rebuilding watched states" % origDev.name)
				self.cache.removeDevice (origDev.id)
				self.deviceStartComm (newDev)
				
			# Collapse conditions if they got expanded
			self.cond.collapseAllConditions (newDev)
			
		else:
			
			changedStates = self.cache.watchedStateChanged (origDev, newDev)
			if changedStates:
				self.debugLog(u"The monitored device %s had a watched state change" % origDev.name)
				# Send parent device array and changed states array to function to disseminate
				#indigo.server.log(unicode(changedStates))
				X = 1 # placeholder
			
		return
		
	#
	# Variable updated
	#
	def variableUpdated (self, origVariable, newVariable):
		# Since we don't use variable caching find any date/time devices using variables
		return
		
	#
	# Device deleted
	#
	def deviceDeleted(self, dev):
		if dev.pluginId == self.pluginId:
			self.debugLog("%s was deleted" % dev.name)
			self.cache.removeDevice (dev.id)
		
	
	################################################################################
	# INDIGO DEVICE UI EVENTS
	################################################################################	
	
		
	#
	# Device pre-save event
	#
	def validateDeviceConfigUi(self, valuesDict, typeId, devId):
		dev = indigo.devices[devId]
		self.debugLog(u"%s is validating device configuration UI" % dev.name)
		
		if len(valuesDict["devicelist"]) == 0:
			errorDict = indigo.Dict()
			errorDict["devicelist"] = "You must select at least one device"
			errorDict["showAlertText"] = "You must select at least one device for this plugin to work!"
			return (False, valuesDict, errorDict)
		
		# Make sure they aren't choosing a device that is already on another auto off device
		for deviceId in valuesDict["devicelist"]:
			for dev in indigo.devices.iter(self.pluginId):
				if str(dev.id) != str(devId):
					if eps.valueValid (dev.pluginProps, "devicelist", True):
						for d in dev.pluginProps["devicelist"]:
							if d == deviceId and valuesDict["allowSave"] == False:
								errorDict = indigo.Dict()
								errorDict["devicelist"] = "One or more devices are already managed by other Powermiser auto-off devices"
								errorDict["showAlertText"] = "You are already managing %s in another Powermiser auto-off device, the conditions could overlap and cause problems.\n\nBe sure that your conditions are different enough not to collide with the other Powermiser device.\n\nThis is only a warning, hit save again to ignore this warning." % indigo.devices[int(deviceId)].name
								valuesDict["allowSave"] = True
								return (False, valuesDict, errorDict)
		
		# All is good, set the allowSave back to false for the next round
		valuesDict["allowSave"] = False
		
		# If we get here all is good so far, return from conditions in case there are problems there
		return self.cond.validateDeviceConfigUi(valuesDict, typeId, devId)
		
	#
	# Device config button clicked event
	#
	def closedDeviceConfigUi(self, valuesDict, userCancelled, typeId, devId):
		dev = indigo.devices[devId]
		self.debugLog(u"%s is closing device configuration UI" % dev.name)
		
		if userCancelled == False: 
			self.debugLog(u"%s configuration UI was not cancelled" % dev.name)
			
		#self.cache.dictDump (self.cache.devices[dev.id])
			
		return
		
	#
	# Event pre-save event
	#
	def validateEventConfigUi(self, valuesDict, typeId, eventId):
		self.debugLog(u"Validating event configuration UI")
		return (True, valuesDict)
		
	#
	# Event config button clicked event
	#
	def closedEventConfigUi(self, valuesDict, userCancelled, typeId, eventId):
		self.debugLog(u"Closing event configuration UI")
		return
		
	#
	# Action pre-save event
	#
	def validateActionConfigUi(self, valuesDict, typeId, actionId):
		self.debugLog(u"Validating event configuration UI")
		return (True, valuesDict)
		
	#
	# Action config button clicked event
	#
	def closedActionConfigUi(self, valuesDict, userCancelled, typeId, actionId):
		self.debugLog(u"Closing action configuration UI")
		return
		
		
	################################################################################
	# INDIGO PLUGIN EVENTS
	################################################################################	
	
	#
	# Plugin startup
	#
	def startup(self):
		self.debugLog(u"Starting plugin")
		if self.cache is None: return
		
		if self.monitor: 
			if self.cache.pollingMode == "realTime": 
				#indigo.variables.subscribeToChanges()
				indigo.devices.subscribeToChanges()
				#indigo.zwave.subscribeToIncoming()
				indigo.insteon.subscribeToIncoming()
				indigo.insteon.subscribeToOutgoing()
				
		
		# Add all sub device variables that our plugin links to, reloading only on the last one
		#self.cache.addSubDeviceVar ("weathersnoop", False) # Add variable, don't reload cache
		#self.cache.addSubDeviceVar ("irrigation") # Add variable, reload cache
		
		# Not adding any sub device variables, reload the cache manually
		self.cache.cacheDevices()
		
		#self.cache.dictDump (self.cache.devices)
		
		return
		
	#	
	# Plugin shutdown
	#
	def shutdown(self):
		self.debugLog(u"Plugin shut down")	
	
	#
	# Concurrent thread
	#
	def runConcurrentThread(self):
		if self.cache is None:
			try:
				while True:
					self.sleep(1)
					if self.reload: break
			except self.StopThread:
				pass
			
			# Only happens if we break out due to a restart command
			serverPlugin = indigo.server.getPlugin(self.pluginId)
			serverPlugin.restart(waitUntilDone=False)
				
			return
		
		try:
			while True:
				if self.cache.pollingMode == "realTime" or self.cache.pollingMode == "pollDevice":
					self.onRunConcurrentThread()
					self.sleep(1)
					if self.reload: break
				else:
					self.onRunConcurrentThread()
					self.sleep(self.cache.pollingInterval)
					if self.reload: break
					
				# Only happens if we break out due to a restart command
				serverPlugin = indigo.server.getPlugin(self.pluginId)
         		serverPlugin.restart(waitUntilDone=False)
		
		except self.StopThread:
			pass	# Optionally catch the StopThread exception and do any needed cleanup.
			
			
	################################################################################
	# INDIGO DEVICE EVENTS
	################################################################################
	
	#
	# Dimmer/relay actions
	#
	def actionControlDimmerRelay(self, action, dev):
		if action.deviceAction == indigo.kDimmerRelayAction.TurnOn:
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s" % (dev.name, "on"))
				dev.updateStateOnServer("onOffState", True)
			else:
				indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "on"), isError=True)

		elif action.deviceAction == indigo.kDimmerRelayAction.TurnOff:
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s" % (dev.name, "off"))
				dev.updateStateOnServer("onOffState", False)
			else:
				indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "off"), isError=True)

		elif action.deviceAction == indigo.kDimmerRelayAction.Toggle:
			newOnState = not dev.onState
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s" % (dev.name, "toggle"))
				dev.updateStateOnServer("onOffState", newOnState)
			else:
				indigo.server.log(u"send \"%s\" %s failed" % (dev.name, "toggle"), isError=True)

		elif action.deviceAction == indigo.kDimmerRelayAction.SetBrightness:
			newBrightness = action.actionValue
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s to %d" % (dev.name, "set brightness", newBrightness))
				dev.updateStateOnServer("brightnessLevel", newBrightness)
			else:
				indigo.server.log(u"send \"%s\" %s to %d failed" % (dev.name, "set brightness", newBrightness), isError=True)

		elif action.deviceAction == indigo.kDimmerRelayAction.BrightenBy:
			newBrightness = dev.brightness + action.actionValue
			if newBrightness > 100:
				newBrightness = 100
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s to %d" % (dev.name, "brighten", newBrightness))
				dev.updateStateOnServer("brightnessLevel", newBrightness)
			else:
				indigo.server.log(u"send \"%s\" %s to %d failed" % (dev.name, "brighten", newBrightness), isError=True)

		elif action.deviceAction == indigo.kDimmerRelayAction.DimBy:
			newBrightness = dev.brightness - action.actionValue
			if newBrightness < 0:
				newBrightness = 0
			sendSuccess = True

			if sendSuccess:
				indigo.server.log(u"sent \"%s\" %s to %d" % (dev.name, "dim", newBrightness))
				dev.updateStateOnServer("brightnessLevel", newBrightness)
			else:
				indigo.server.log(u"send \"%s\" %s to %d failed" % (dev.name, "dim", newBrightness), isError=True)
	
	################################################################################
	# INDIGO PLUGIN UI EVENTS
	################################################################################	
	
	#
	# Plugin config pre-save event
	#
	def validatePrefsConfigUi(self, valuesDict):
		self.debugLog(u"%s is validating plugin config UI" % self.pluginDisplayName)
		return (True, valuesDict)
		
	#
	# Plugin config button clicked event
	#
	def closedPrefsConfigUi(self, valuesDict, userCancelled):
		self.debugLog(u"%s is closing plugin config UI" % self.pluginDisplayName)
		
		if userCancelled == False:
			if "debugMode" in valuesDict:
				self.debug = valuesDict["debugMode"]
		
		return
			
	#
	# Stop concurrent thread
	#
	def stopConcurrentThread(self):
		self.debugLog(u"Plugin stopping concurrent threads")	
		self.stopThread = True
		
	#
	# Delete
	#
	def __del__(self):
		self.debugLog(u"Plugin delete")	
		indigo.PluginBase.__del__(self)
		
	
	################################################################################
	# PLUGIN SPECIFIC ROUTINES
	################################################################################	
	
	#
	# Break down device command (method incoming is physical, outgoing is Indigo)
	#
	def processRawCommand (self, devChild, cmd, method = "Physical"):
		try:
			self.debugLog(u"A monitored device '%s' processed a raw command '%s'" % (devChild.name, cmd))
			dev = False
			
			for d in indigo.devices.iter(self.pluginId):
				if eps.valueValid (d.pluginProps, "devicelist", True):
					for devId in d.pluginProps["devicelist"]:
						if devId == str(devChild.id):
							devParent = d
							self.debugLog ("\tProcessing auto off group '%s' managing this device" % devParent.name)
							autoOffTimes = ast.literal_eval (devParent.states["autoOffTimes"])
							
							if devParent.pluginProps["physicalOnly"] and cmd == "on" and method != "Physical":
								self.debugLog("\t%s is configured for physical only, this on command was sent from Insteon so it will be ignored" % devParent.name)
								continue # so we can see if it's in another Powermiser device
							
							if devChild.id in autoOffTimes:
								self.debugLog ("\tThe device is currently in an on state in the plugin")
								
								if cmd == "off":
									self.debugLog ("\tThe command is to turn it off")
									del autoOffTimes[devChild.id]
									devParent.updateStateOnServer("autoOffTimes", unicode(autoOffTimes))
									
								else:
									self.debugLog ("\tThe command is to turn it on")
									self.turnDeviceOn (devParent, devChild, autoOffTimes)
								
							else:
								self.debugLog ("\tThe device is currently in an off state in the plugin")
								
								if cmd == "off":
									self.debugLog ("\tThe command is to turn it off and it's not in cache, nothing to do")
								else:
									self.debugLog ("\tThe command is to turn it on")
									self.turnDeviceOn (devParent, devChild, autoOffTimes)
			
		except Exception as e:
			eps.printException(e)
			
	#
	# Turn device on or extend it's on time
	#
	def turnDeviceOn (self, devParent, devChild, autoOffTimes):
		try:
			d = indigo.server.getTime()
			
			if self.cond.conditionsPass (devParent) == False:
				self.debugLog ("\tDevice doesn't pass conditions, ignoring command")
				return
			
			if devChild.id in autoOffTimes:
				if devParent.pluginProps["tapDuration"]:
					if eps.valueValid (devParent.pluginProps, "extendTime", True):
						self.debugLog ("\tExtending time on by %s minutes" % devParent.pluginProps["extendTime"])
						offDict = autoOffTimes[devChild.id]
						offDict["repeats"] = offDict["repeats"] + 1
						
						if eps.valueValid (devParent.pluginProps, "turnOn", True):
							if int(devParent.pluginProps["turnOn"]) > 0:
								if offDict["repeats"] >= int(devParent.pluginProps["turnOn"]):
									self.debugLog ("\tMaximum repeats reached, cancelling auto off")
									del autoOffTimes[devChild.id]
									devParent.updateStateOnServer("autoOffTimes", unicode(autoOffTimes))
									return
						
						autoOff = datetime.datetime.strptime (offDict["offTime"], "%Y-%m-%d %H:%M:%S")
						autoOff = dtutil.DateAdd ("minutes", int(devParent.pluginProps["extendTime"]), autoOff)
						offDict["offTime"] = autoOff.strftime("%Y-%m-%d %H:%M:%S")
						
						autoOffTimes[devChild.id] = offDict
						devParent.updateStateOnServer("autoOffTimes", unicode(autoOffTimes))
						self.debugLog ("\tThe device will turn off automatically at %s" % autoOff.strftime("%Y-%m-%d %H:%M:%S"))
						
			else:
				self.debugLog ("\tSetting the initial auto off time")
				
				if eps.valueValid (devParent.pluginProps, "timeOut", True):
					offDict = {}
					offDict["repeats"] = 1
					
					autoOff = dtutil.DateAdd ("minutes", int(devParent.pluginProps["timeOut"]), d)
					offDict ["offTime"] = autoOff.strftime("%Y-%m-%d %H:%M:%S")
					
					autoOffTimes[devChild.id] = offDict
					devParent.updateStateOnServer("autoOffTimes", unicode(autoOffTimes))
					self.debugLog ("\tThe device will turn off automatically at %s" % autoOff.strftime("%Y-%m-%d %H:%M:%S"))
		
		except Exception as e:
			eps.printException(e)
		
	
	################################################################################
	# SUPPORT DEBUG ROUTINE
	################################################################################	
	
	#
	# Plugin menu: Support log
	#
	def supportLog (self):
		self.showLibraryVersions ()
		
		s = eps.debugHeader("SUPPORT LOG")
		
		# Get plugin prefs
		s += eps.debugHeader ("PLUGIN PREFRENCES", "=")
		for k, v in self.pluginPrefs.iteritems():
			s += eps.debugLine(k + " = " + unicode(v), "=")
			
		s += eps.debugHeaderEx ("=")
		
		# Report on cache
		s += eps.debugHeader ("DEVICE CACHE", "=")
		
		for devId, devProps in self.cache.devices.iteritems():
			s += eps.debugHeaderEx ("*")
			s += eps.debugLine(devProps["name"] + ": " + str(devId) + " - " + devProps["deviceTypeId"], "*")
			s += eps.debugHeaderEx ("*")
			
			s += eps.debugHeaderEx ("-")
			s += eps.debugLine("SUBDEVICES", "-")
			s += eps.debugHeaderEx ("-")
			
			for subDevId, subDevProps in devProps["subDevices"].iteritems():
				s += eps.debugHeaderEx ("+")
				s += eps.debugLine(subDevProps["name"] + ": " + str(devId) + " - " + subDevProps["deviceTypeId"] + " (Var: " + subDevProps["varName"] + ")", "+")
				s += eps.debugHeaderEx ("+")
				
				s += eps.debugLine("WATCHING STATES:", "+")
				
				for z in subDevProps["watchStates"]:
					s += eps.debugLine("     " + z, "+")
					
				s += eps.debugHeaderEx ("+")
					
				s += eps.debugLine("WATCHING PROPERTIES:", "+")
				
				for z in subDevProps["watchProperties"]:
					s += eps.debugLine("     " + z, "+")
					
				if subDevId in indigo.devices:
					d = indigo.devices[subDevId]
					if d.pluginId != self.pluginId:
						s += eps.debugHeaderEx ("!")
						s += eps.debugLine(d.name + ": " + str(d.id) + " - " + d.deviceTypeId, "!")
						s += eps.debugHeaderEx ("!")
					
						s += eps.debugHeaderEx ("-")
						s += eps.debugLine("PREFERENCES", "-")
						s += eps.debugHeaderEx ("-")
			
						for k, v in d.pluginProps.iteritems():
							s += eps.debugLine(k + " = " + unicode(v), "-")
				
						s += eps.debugHeaderEx ("-")
						s += eps.debugLine("STATES", "-")
						s += eps.debugHeaderEx ("-")
			
						for k, v in d.states.iteritems():
							s += eps.debugLine(k + " = " + unicode(v), "-")
						
						s += eps.debugHeaderEx ("-")
						s += eps.debugLine("RAW DUMP", "-")
						s += eps.debugHeaderEx ("-")
						s += unicode(d) + "\n"
				
						s += eps.debugHeaderEx ("-")
					else:
						s += eps.debugHeaderEx ("!")
						s += eps.debugLine("Plugin Device Already Summarized", "+")
						s += eps.debugHeaderEx ("!")
				else:
					s += eps.debugHeaderEx ("!")
					s += eps.debugLine("!!!!!!!!!!!!!!! DEVICE DOES NOT EXIST IN INDIGO !!!!!!!!!!!!!!!", "+")
					s += eps.debugHeaderEx ("!")
				
			s += eps.debugHeaderEx ("-")
		
		
		s += eps.debugHeaderEx ("=")
		
		# Loop through all devices for this plugin and report
		s += eps.debugHeader ("PLUGIN DEVICES", "=")
		
		for dev in indigo.devices.iter(self.pluginId):
			s += eps.debugHeaderEx ("*")
			s += eps.debugLine(dev.name + ": " + str(dev.id) + " - " + dev.deviceTypeId, "*")
			s += eps.debugHeaderEx ("*")
			
			s += eps.debugHeaderEx ("-")
			s += eps.debugLine("PREFERENCES", "-")
			s += eps.debugHeaderEx ("-")
			
			for k, v in dev.pluginProps.iteritems():
				s += eps.debugLine(k + " = " + unicode(v), "-")
				
			s += eps.debugHeaderEx ("-")
			s += eps.debugLine("STATES", "-")
			s += eps.debugHeaderEx ("-")
			
			for k, v in dev.states.iteritems():
				s += eps.debugLine(k + " = " + unicode(v), "-")
				
			s += eps.debugHeaderEx ("-")
			
		s += eps.debugHeaderEx ("=")
		
		
		
		
		indigo.server.log(s)

	################################################################################
	# UPDATE CHECKS
	################################################################################

	def updateCheck (self, onlyNewer = False, force = True):
		try:
			try:
				if self.pluginUrl == "": 
					if force: indigo.server.log ("This plugin currently does not check for newer versions", isError = True)
					return
			except:
				# Normal if pluginUrl hasn't been defined
				if force: indigo.server.log ("This plugin currently does not check for newer versions", isError = True)
				return
			
			d = indigo.server.getTime()
			
			if eps.valueValid (self.pluginPrefs, "latestVersion") == False: self.pluginPrefs["latestVersion"] = False
			
			if force == False and eps.valueValid (self.pluginPrefs, "lastUpdateCheck", True):
				last = datetime.datetime.strptime (self.pluginPrefs["lastUpdateCheck"], "%Y-%m-%d %H:%M:%S")
				lastCheck = dtutil.DateDiff ("hours", d, last)
								
				if self.pluginPrefs["latestVersion"]:
					if lastCheck < 72: return # if last check has us at the latest then only check every 3 days
				else:
					if lastCheck < 2: return # only check every four hours in case they don't see it in the log
			
			
			page = urllib2.urlopen(self.pluginUrl)
			soup = BeautifulSoup(page)
		
			versions = soup.find(string=re.compile("\#Version\|"))
			versionData = unicode(versions)
		
			versionInfo = versionData.split("#Version|")
			newVersion = float(versionInfo[1][:-1])
		
			if newVersion > float(self.pluginVersion):
				self.pluginPrefs["latestVersion"] = False
				indigo.server.log ("Version %s of %s is available, you are currently using %s." % (str(round(newVersion,2)), self.pluginDisplayName, str(round(float(self.pluginVersion), 2))), isError=True)
			
			else:
				self.pluginPrefs["latestVersion"] = True
				if onlyNewer == False: indigo.server.log("%s version %s is the most current version of the plugin" % (self.pluginDisplayName, str(round(float(self.pluginVersion), 2))))
				
			self.pluginPrefs["lastUpdateCheck"] = d.strftime("%Y-%m-%d %H:%M:%S")
			
				
		except Exception as e:
			eps.printException(e)
		
	################################################################################
	# LEGACY MIGRATED ROUTINES
	################################################################################
	


	

	
