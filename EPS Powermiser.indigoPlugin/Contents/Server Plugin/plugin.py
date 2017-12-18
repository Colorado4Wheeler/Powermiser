#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Core libraries
import indigo
import os
import sys
import time
import datetime
from datetime import date, timedelta

# EPS 3.0 Libraries
import logging
from lib.eps import eps
from lib import ext
from lib import dtutil
from lib import iutil

# Plugin libraries
import ast


eps = eps(None)

################################################################################
# plugin - 	Basically serves as a shell for the main plugin functions, it passes
# 			all Indigo commands to the core engine to do the "standard" operations
#			and raises onBefore_ and onAfter_ if it wants to do something 
#			interesting with it.  The meat of the plugin is in here while the
#			EPS library handles the day-to-day and common operations.
################################################################################
class Plugin(indigo.PluginBase):

	# Define the plugin-specific things our engine needs to know
	TVERSION	= "3.2.1"
	PLUGIN_LIBS = ["cache", "conditions"]
	UPDATE_URL 	= ""#"http://forums.indigodomo.com/viewtopic.php?f=196&t=16343"
	
	#
	# Init
	#
	def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
		indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
		
		eps.__init__ (self)
		eps.loadLibs (self.PLUGIN_LIBS)
		eps.plug.subscribeProtocols ({"zwave":"incoming|outgoing","insteon":"incoming|outgoing"})
		
		
	################################################################################
	# PLUGIN HANDLERS
	#
	# Raised onBefore_ and onAfter_ for interesting Indigo or custom commands that 
	# we want to intercept and do something with
	################################################################################	
	
	def onWatchedObjectRequest (self, dev):
		self.logger.threaddebug ("Returning watched devices for '{0}'".format(dev.name))
		ret = {}
		
		try:
			if dev.deviceTypeId == "AutoOff":
				for devId in dev.pluginProps["devicelist"]:
					ret[int(devId)] = []
								
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
		return ret
	
	def onAfter_protocolCommandReceivedFromCache (self, dev, cmd, type):
		try:
			self.logger.debug ("Received {0} command from cached {1} device '{2}'".format (cmd, type, dev.name))
			self.processCommand (dev, cmd)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
		
	def onAfter_protocolCommandSentFromCache (self, dev, cmd, type):
		try:
			self.logger.debug ("Indigo sent {0} command to cached {1} device '{2}'".format (cmd, type, dev.name))
			self.processCommand (dev, cmd, "Indigo")
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	def onAfter_validateDeviceConfigUi(self, valuesDict, typeId, devId):
		try:
			dev = indigo.devices[devId]
			self.logger.debug(u"%s is validating device configuration UI" % dev.name)
		
			if len(valuesDict["devicelist"]) == 0:
				errorDict = indigo.Dict()
				errorDict["devicelist"] = "You must select at least one device"
				errorDict["showAlertText"] = "You must select at least one device for this plugin to work!"
				return (False, valuesDict, errorDict)
		
			# Make sure they aren't choosing a device that is already on another auto off device
			for deviceId in valuesDict["devicelist"]:
				for dev in indigo.devices.iter(self.pluginId):
					if str(dev.id) != str(devId):
						if ext.valueValid (dev.pluginProps, "devicelist", True):
							for d in dev.pluginProps["devicelist"]:
								if d == deviceId and valuesDict["allowSave"] == False:
									errorDict = indigo.Dict()
									errorDict["devicelist"] = "One or more devices are already managed by other Powermiser auto-off devices"
									errorDict["showAlertText"] = "You are already managing %s in another Powermiser auto-off device, the conditions could overlap and cause problems.\n\nBe sure that your conditions are different enough not to collide with the other Powermiser device.\n\nThis is only a warning, hit save again to ignore this warning." % indigo.devices[int(deviceId)].name
									valuesDict["allowSave"] = True
									return (False, valuesDict, errorDict)
		
			# All is good, set the allowSave back to false for the next round
			valuesDict["allowSave"] = False
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	def onAfter_runConcurrentThread (self):
		#return
		try:
			for dev in indigo.devices.iter(self.pluginId):
				if ext.valueValid (dev.states, "autoOffTimes", True):
					if dev.states["autoOffTimes"] != "{}":
						autoOffTimes = ast.literal_eval (dev.states["autoOffTimes"])
					
						for devId, offDict in autoOffTimes.iteritems():
							d = datetime.datetime.strptime (offDict["offTime"], "%Y-%m-%d %H:%M:%S")
							diff = dtutil.dateDiff ("seconds", d, indigo.server.getTime())
							if diff < 0:
								self.logger.info("Turning off device %s" % indigo.devices[int(devId)].name)
								indigo.device.turnOff(devId)
										
					if dev.states["autoOffTimes"] == "{}" and dev.states["statedisplay"] != "off":
						dev.updateStateImageOnServer(indigo.kStateImageSel.PowerOff)
						dev.updateStateOnServer("statedisplay", "off")
					
					if dev.states["autoOffTimes"] != "{}" and dev.states["statedisplay"] == "off":
						dev.updateStateImageOnServer(indigo.kStateImageSel.PowerOn)
						dev.updateStateOnServer("statedisplay", "on")
		
		except Exception as e:
			self.logger.error (ext.getException(e))
	
	#
	# Break down device command (method incoming is physical, outgoing is Indigo)
	#
	def processCommand (self, devChild, cmd, method = "Physical"):
		try:
			watchers = eps.cache.getDevicesWatchingId (devChild.id)
			if len(watchers) > 0:
				for parentId in watchers:
					parent = indigo.devices[int(parentId)]
					
					self.logger.debug ("\tProcessing auto off group '%s' managing this device" % parent.name)
					autoOffTimes = ast.literal_eval (parent.states["autoOffTimes"])
					
					if parent.pluginProps["physicalOnly"] and cmd == "on" and method != "Physical":
						self.logger.debug("\t%s is configured for physical only, this on command was sent from Indigo so it will be ignored" % parent.name)
						continue # so we can see if it's in another Powermiser device
						
					if devChild.id in autoOffTimes:
						self.logger.debug ("\tThe device is currently in an on state in the plugin")
					
						if cmd == "off":
							self.logger.debug ("\tThe command is to turn it off")
							del autoOffTimes[devChild.id]
							parent.updateStateOnServer("autoOffTimes", unicode(autoOffTimes))
						
						else:
							self.logger.debug ("\tThe command is to turn it on")
							self.turnDeviceOn (parent, devChild, autoOffTimes)
							
					else:
						self.logger.debug ("\tThe device is currently in an off state in the plugin")
					
						if cmd == "off":
							self.logger.debug ("\tThe command is to turn it off and it's not in cache, nothing to do")
						else:
							self.logger.debug ("\tThe command is to turn it on")
							self.turnDeviceOn (parent, devChild, autoOffTimes)
			
		except Exception as e:
			self.logger.error (ext.getException(e))	
			
	#
	# Turn device on or extend it's on time
	#
	def turnDeviceOn (self, devParent, devChild, autoOffTimes):
		try:
			d = indigo.server.getTime()
			
			if eps.plug.checkConditions (devParent.pluginProps, devParent) == False:
				self.logger.debug ("\tDevice doesn't pass conditions, ignoring command")
				return
			
			if devChild.id in autoOffTimes:
				if devParent.pluginProps["tapDuration"]:
					if ext.valueValid (devParent.pluginProps, "extendTime", True):
						self.logger.info ("Extending %s time on by %s minutes" % (devChild.name, devParent.pluginProps["extendTime"]))
						offDict = autoOffTimes[devChild.id]
						offDict["repeats"] = offDict["repeats"] + 1
						
						if ext.valueValid (devParent.pluginProps, "turnOn", True):
							if int(devParent.pluginProps["turnOn"]) > 0:
								if offDict["repeats"] >= int(devParent.pluginProps["turnOn"]):
									self.logger.info ("\t%s maximum repeats reached, cancelling auto off" % devChild.name)
									del autoOffTimes[devChild.id]
									devParent.updateStateOnServer("autoOffTimes", unicode(autoOffTimes))
									return
						
						autoOff = datetime.datetime.strptime (offDict["offTime"], "%Y-%m-%d %H:%M:%S")
						autoOff = dtutil.dateAdd ("minutes", int(devParent.pluginProps["extendTime"]), autoOff)
						offDict["offTime"] = autoOff.strftime("%Y-%m-%d %H:%M:%S")
						
						autoOffTimes[devChild.id] = offDict
						devParent.updateStateOnServer("autoOffTimes", unicode(autoOffTimes))
						self.logger.info ("%s will turn off automatically at %s" % (devChild.name, autoOff.strftime("%Y-%m-%d %H:%M:%S")))
						
			else:
				self.logger.debug ("\tSetting the initial auto off time")
				
				if ext.valueValid (devParent.pluginProps, "timeOut", True):
					offDict = {}
					offDict["repeats"] = 1
					
					autoOff = dtutil.dateAdd ("minutes", int(devParent.pluginProps["timeOut"]), d)
					offDict ["offTime"] = autoOff.strftime("%Y-%m-%d %H:%M:%S")
					
					autoOffTimes[devChild.id] = offDict
					devParent.updateStateOnServer("autoOffTimes", unicode(autoOffTimes))
					self.logger.info ("%s will turn off automatically at %s" % (devChild.name, autoOff.strftime("%Y-%m-%d %H:%M:%S")))
		
		except Exception as e:
			self.logger.error (ext.getException(e))	
	
	################################################################################
	# INDIGO COMMAND HAND-OFFS
	#
	# Everything below here are standard Indigo plugin actions that get handed off
	# to the engine, they really shouldn't change from plugin to plugin
	################################################################################
	
	################################################################################
	# INDIGO PLUGIN EVENTS
	################################################################################		
	
	# System
	def startup(self): return eps.plug.startup()
	def shutdown(self): return eps.plug.shutdown()
	def runConcurrentThread(self): return eps.plug.runConcurrentThread()
	def stopConcurrentThread(self): return eps.plug.stopConcurrentThread()
	def __del__(self): return eps.plug.delete()
	
	# UI
	def validatePrefsConfigUi(self, valuesDict): return eps.plug.validatePrefsConfigUi(valuesDict)
	def closedPrefsConfigUi(self, valuesDict, userCancelled): return eps.plug.closedPrefsConfigUi(valuesDict, userCancelled)
	
	################################################################################
	# INDIGO DEVICE EVENTS
	################################################################################
	
	# Basic comm events
	def deviceStartComm (self, dev): return eps.plug.deviceStartComm (dev)
	def deviceUpdated (self, origDev, newDev): return eps.plug.deviceUpdated (origDev, newDev)
	def deviceStopComm (self, dev): return eps.plug.deviceStopComm (dev)
	def deviceDeleted(self, dev): return eps.plug.deviceDeleted(dev)
	def actionControlDimmerRelay(self, action, dev): return eps.plug.actionControlDimmerRelay(action, dev)
	
	# UI Events
	def getDeviceDisplayStateId(self, dev): return eps.plug.getDeviceDisplayStateId (dev)
	def validateDeviceConfigUi(self, valuesDict, typeId, devId): return eps.plug.validateDeviceConfigUi(valuesDict, typeId, devId)
	def closedDeviceConfigUi(self, valuesDict, userCancelled, typeId, devId): return eps.plug.closedDeviceConfigUi(valuesDict, userCancelled, typeId, devId)		
	
	################################################################################
	# INDIGO PROTOCOL EVENTS
	################################################################################
	def zwaveCommandReceived(self, cmd): return eps.plug.zwaveCommandReceived(cmd)
	def zwaveCommandSent(self, cmd): return eps.plug.zwaveCommandSent(cmd)
	def insteonCommandReceived (self, cmd): return eps.plug.insteonCommandReceived(cmd)
	def insteonCommandSent (self, cmd): return eps.plug.insteonCommandSent(cmd)
	def X10CommandReceived (self, cmd): return eps.plug.X10CommandReceived(cmd)
	def X10CommandSent (self, cmd): return eps.plug.X10CommandSent(cmd)

	################################################################################
	# INDIGO VARIABLE EVENTS
	################################################################################
	
	# Basic comm events
	def variableCreated(self, var): return eps.plug.variableCreated(var)
	def variableUpdated (self, origVar, newVar): return eps.plug.variableUpdated (origVar, newVar)
	def variableDeleted(self, var): return self.variableDeleted(var)
		
	################################################################################
	# INDIGO EVENT EVENTS
	################################################################################
	
	# Basic comm events
	
	# UI
	def validateEventConfigUi(self, valuesDict, typeId, eventId): return eps.plug.validateEventConfigUi(valuesDict, typeId, eventId)
	def closedEventConfigUi(self, valuesDict, userCancelled, typeId, eventId): return eps.plug.closedEventConfigUi(valuesDict, userCancelled, typeId, eventId)
		
	################################################################################
	# INDIGO ACTION EVENTS
	################################################################################
	
	# Basic comm events
	def actionGroupCreated(self, actionGroup): eps.plug.actionGroupCreated(actionGroup)
	def actionGroupUpdated (self, origActionGroup, newActionGroup): eps.plug.actionGroupUpdated (origActionGroup, newActionGroup)
	def actionGroupDeleted(self, actionGroup): eps.plug.actionGroupDeleted(actionGroup)
		
	# UI
	def validateActionConfigUi(self, valuesDict, typeId, actionId): return eps.plug.validateActionConfigUi(valuesDict, typeId, actionId)
	def closedActionConfigUi(self, valuesDict, userCancelled, typeId, actionId): return eps.plug.closedActionConfigUi(valuesDict, userCancelled, typeId, actionId)
		
	################################################################################
	# INDIGO TRIGGER EVENTS
	################################################################################
	
	# Basic comm events
	def triggerStartProcessing(self, trigger): return eps.plug.triggerStartProcessing(trigger)
	def triggerStopProcessing(self, trigger): return eps.plug.triggerStopProcessing(trigger)
	def didTriggerProcessingPropertyChange(self, origTrigger, newTrigger): return eps.plug.didTriggerProcessingPropertyChange(origTrigger, newTrigger)
	def triggerCreated(self, trigger): return eps.plug.triggerCreated(trigger)
	def triggerUpdated(self, origTrigger, newTrigger): return eps.plug.triggerUpdated(origTrigger, newTrigger)
	def triggerDeleted(self, trigger): return eps.plug.triggerDeleted(trigger)
                                   
	# UI
	
	################################################################################
	# INDIGO SYSTEM EVENTS
	################################################################################
	
	# Basic comm events
	
	# UI
	
	################################################################################
	# EPS EVENTS
	################################################################################		
	
	# Plugin menu actions
	def pluginMenuSupportData (self): return eps.plug.pluginMenuSupportData ()
	def pluginMenuSupportDataEx (self): return eps.plug.pluginMenuSupportDataEx ()
	def pluginMenuSupportInfo (self): return eps.plug.pluginMenuSupportInfo ()
	def pluginMenuCheckUpdates (self): return eps.plug.pluginMenuCheckUpdates ()
	
	# UI Events
	def getCustomList (self, filter="", valuesDict=None, typeId="", targetId=0): return eps.ui.getCustomList (filter, valuesDict, typeId, targetId)
	def formFieldChanged (self, valuesDict, typeId, devId): return eps.plug.formFieldChanged (valuesDict, typeId, devId)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	