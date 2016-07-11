import datetime
import time
import indigo
import sys
import dtutil
import eps
import string
import ui
import calendar

class conditions:

	#
	# Initialize the class
	#
	def __init__ (self, parent):
		self.parent = parent
		self.maxConditions = 10
		self.enablePlaceholders = True # Indigo 6
		
		iVer = str(indigo.server.version).split(".")
		if int(iVer[0]) > 6: 
			self.debugLog ("Disabling placeholders for Indigo 7 or greater")
			self.enablePlaceholders = False # Indigo 7
		
		self.version = "1.0"
		
	#
	# Debug log
	#
	def debugLog (self, value):
		if self.parent is None: return
		self.parent.debugLog (value)	
		
	################################################################################
	# CONDITION CHECKING
	################################################################################
		
	#
	# Check if conditions pass, return false on any condition failure
	#
	def conditionsPass (self, dev):
		try:
			isTrue = 0
			isFalse = 0
			
			if eps.valueValid (dev.pluginProps, "conditions", True) == False: return False
			condition = dev.pluginProps["conditions"]
			
			self.debugLog ("\tCondition is set to %s, testing condition(s)" % condition)
			
			if condition == "none": return True
			
			for i in range (0, self.maxConditions + 1):
				if eps.valueValid (dev.pluginProps, "condition" + str(i), True) == False: continue # no condition for this index
				if dev.pluginProps["condition" + str(i)] == "disabled": continue # this condition is disabled
				
				val = [0,0] # Failsafe
				
				if dev.pluginProps["evaluation" + str(i)] == "between" or dev.pluginProps["evaluation" + str(i)] == "notbetween": val = self.conditionBetween (dev, i)
				if dev.pluginProps["evaluation" + str(i)] == "equal" or dev.pluginProps["evaluation" + str(i)] == "notequal": val = self.conditionEquals (dev, i)
				if dev.pluginProps["evaluation" + str(i)] == "greater": val = self.conditionGreater (dev, i)
				if dev.pluginProps["evaluation" + str(i)] == "less": val = self.conditionLess (dev, i)
				if dev.pluginProps["evaluation" + str(i)] == "contains" or dev.pluginProps["evaluation" + str(i)] == "notcontains": val = self.conditionContain (dev, i)
					
				isTrue = isTrue + val[0]
				isFalse = isFalse + val[1]			
		
			if condition == "alltrue" and isFalse <> 0: return False
			if condition == "anytrue" and isTrue == 0: return False
			if condition == "allfalse" and isTrue <> 0: return False
			if condition == "anyfalse" and isFalse == 0: return False
		
		except Exception as e:
			eps.printException(e) 
			return False
	
	
	#
	# Check condition evaluation CONTAINS
	#
	def conditionContain (self, dev, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			compareString = ""
			devEx = None
			
			if dev.pluginProps["condition" + str(index)] == "device" or dev.pluginProps["condition" + str(index)] == "devstatedateonly" or dev.pluginProps["condition" + str(index)] == "devstatetimeonly" or dev.pluginProps["condition" + str(index)] == "devstatedatetime" or dev.pluginProps["condition" + str(index)] == "devstatedow":
				devEx = indigo.devices[int(dev.pluginProps["device" + str(index)])]
			
			if dev.pluginProps["condition" + str(index)] == "device":
				if eps.valueValid (devEx.states, dev.pluginProps["state" + str(index)]):
					compareString = unicode(devEx.states[dev.pluginProps["state" + str(index)]])
			
			elif dev.pluginProps["condition" + str(index)] == "variable":
				var = indigo.variables[int(dev.pluginProps["variable" + str(index)])]
				compareString = unicode(var.value)
				
			elif dev.pluginProps["condition" + str(index)] == "datetime" or dev.pluginProps["condition" + str(index)] == "devstatedatetime" or dev.pluginProps["condition" + str(index)] == "vardatetime":
				d = indigo.server.getTime()
				if dev.pluginProps["condition" + str(index)] == "devstatedatetime": d = self.getDevStateDateTime (dev, devEx, index)
				if dev.pluginProps["condition" + str(index)] == "vardatetime": d = self.getVarDateTime (dev, index)
				
				compareString = d.strftime ("%Y-%m-%d %H:%M:%S | %m %b %B | %A %w | %I | %p")
				
			else:
				indigo.server.log("Unknown condition %s in contains" % dev.pluginProps["condition" + str(index)], isError=True)
				
			self.debugLog ("\tChecking if %s is in %s" % (dev.pluginProps["value" + str(index)], compareString))
			
			compareValue = ""
			if compareString != "": compareValue = compareString.lower()
			
			findValue = ""
			if dev.pluginProps["value" + str(index)] != "": findValue = str(dev.pluginProps["value" + str(index)]).lower()
			
			if findValue != "":
				foundAt = string.find (compareString, findValue)
			
				if foundAt > -1:
					isTrue = 1	
				else:
					# It's the negative version so reverse the values
					isFalse = 1
			
			else:
				if compareValue == "":
					isTrue = 1
				else:
					isFalse = 1
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
		
	
	#
	# Check condition evaluation LESS THAN
	#
	def conditionLess (self, dev, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			#if dev.pluginProps["condition" + str(index)] == "timeonly" or dev.pluginProps["condition" + str(index)] == "devstatetimeonly" or dev.pluginProps["condition" + str(index)] == "vartimeonly": val = self.conditionsDateLess (dev, index, True, False)
			#if dev.pluginProps["condition" + str(index)] == "dateonly" or dev.pluginProps["condition" + str(index)] == "devstatedateonly" or dev.pluginProps["condition" + str(index)] == "vardateonly": val = self.conditionsDateLess (dev, index, False, True)
			#if dev.pluginProps["condition" + str(index)] == "datetime" or dev.pluginProps["condition" + str(index)] == "devstatedatetime" or dev.pluginProps["condition" + str(index)] == "vardatetime": val = self.conditionsDateLess (dev, index, True, True)
			#if dev.pluginProps["condition" + str(index)] == "dow" or dev.pluginProps["condition" + str(index)] == "devstatedow": val = self.conditionsDow (dev, index)
			
			if dev.pluginProps["condition" + str(index)] == "datetime" or dev.pluginProps["condition" + str(index)] == "devstatedatetime" or dev.pluginProps["condition" + str(index)] == "vardatetime": val = self.conditionsDate (dev, index)
			
			if dev.pluginProps["condition" + str(index)] == "device":
				val = [0, 0] # Failsafe
				devEx = indigo.devices[int(dev.pluginProps["device" + str(index)])]
				if eps.valueValid (devEx.states, dev.pluginProps["state" + str(index)]):
					compareString = unicode(devEx.states[dev.pluginProps["state" + str(index)]])
					self.debugLog ("\tChecking if device state '%s' value of '%s' is less than '%s'" % (dev.pluginProps["state" + str(index)], compareString, dev.pluginProps["value" + str(index)]))
					
					if compareString.lower() < dev.pluginProps["value" + str(index)].lower():
						val[0] = 1
						val[1] = 0
					else:
						val[0] = 0
						val[1] = 1
						
			if dev.pluginProps["condition" + str(index)] == "variable":
				val = [0, 0] # Failsafe
				var = indigo.variables[int(dev.pluginProps["variable" + str(index)])]
				compareString = unicode(var.value)
				self.debugLog ("\tChecking if variable '%s' value of '%s' is less than '%s'" % (var.name, compareString, dev.pluginProps["value" + str(index)]))
									
				if compareString.lower() < dev.pluginProps["value" + str(index)].lower():
					val[0] = 1
					val[1] = 0
				else:
					val[0] = 0
					val[1] = 1
		
			isTrue = isTrue + val[0]
			isFalse = isFalse + val[1]			
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
	
	#
	# Check condition evaluation GREATER THAN
	#
	def conditionGreater (self, dev, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			#if dev.pluginProps["condition" + str(index)] == "timeonly" or dev.pluginProps["condition" + str(index)] == "devstatetimeonly" or dev.pluginProps["condition" + str(index)] == "vartimeonly": val = self.conditionsDateGreater (dev, index, True, False)
			#if dev.pluginProps["condition" + str(index)] == "dateonly" or dev.pluginProps["condition" + str(index)] == "devstatedateonly" or dev.pluginProps["condition" + str(index)] == "vardateonly": val = self.conditionsDateGreater (dev, index, False, True)
			#if dev.pluginProps["condition" + str(index)] == "datetime" or dev.pluginProps["condition" + str(index)] == "devstatedatetime" or dev.pluginProps["condition" + str(index)] == "vardatetime": val = self.conditionsDateGreater (dev, index, True, True)
			#if dev.pluginProps["condition" + str(index)] == "dow" or dev.pluginProps["condition" + str(index)] == "devstatedow": val = self.conditionsDow (dev, index)
			
			if dev.pluginProps["condition" + str(index)] == "datetime" or dev.pluginProps["condition" + str(index)] == "devstatedatetime" or dev.pluginProps["condition" + str(index)] == "vardatetime": val = self.conditionsDate (dev, index)
			
			if dev.pluginProps["condition" + str(index)] == "device":
				val = [0, 0] # Failsafe
				devEx = indigo.devices[int(dev.pluginProps["device" + str(index)])]
				if eps.valueValid (devEx.states, dev.pluginProps["state" + str(index)]):
					compareString = unicode(devEx.states[dev.pluginProps["state" + str(index)]])
					self.debugLog ("\tChecking if device state '%s' value of '%s' is greater than '%s'" % (dev.pluginProps["state" + str(index)], compareString, dev.pluginProps["value" + str(index)]))
					
					if compareString.lower() > dev.pluginProps["value" + str(index)].lower():
						val[0] = 1
						val[1] = 0
					else:
						val[0] = 0
						val[1] = 1
						
			if dev.pluginProps["condition" + str(index)] == "variable":
				val = [0, 0] # Failsafe
				var = indigo.variables[int(dev.pluginProps["variable" + str(index)])]
				compareString = unicode(var.value)
				self.debugLog ("\tChecking if variable '%s' value of '%s' is greater than '%s'" % (var.name, compareString, dev.pluginProps["value" + str(index)]))
									
				if compareString.lower() > dev.pluginProps["value" + str(index)].lower():
					val[0] = 1
					val[1] = 0
				else:
					val[0] = 0
					val[1] = 1
		
			isTrue = isTrue + val[0]
			isFalse = isFalse + val[1]			
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
	
	#
	# Check condition evaluation EQUAL
	#
	def conditionEquals (self, dev, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			#if dev.pluginProps["condition" + str(index)] == "timeonly" or dev.pluginProps["condition" + str(index)] == "devstatetimeonly" or dev.pluginProps["condition" + str(index)] == "vartimeonly": val = self.conditionsDateEquals (dev, index, True, False)
			#if dev.pluginProps["condition" + str(index)] == "dateonly" or dev.pluginProps["condition" + str(index)] == "devstatedateonly" or dev.pluginProps["condition" + str(index)] == "vardateonly": val = self.conditionsDateEquals (dev, index, False, True)
			#if dev.pluginProps["condition" + str(index)] == "datetime" or dev.pluginProps["condition" + str(index)] == "devstatedatetime" or dev.pluginProps["condition" + str(index)] == "vardatetime": val = self.conditionsDateEquals (dev, index, True, True)
			#if dev.pluginProps["condition" + str(index)] == "dow" or dev.pluginProps["condition" + str(index)] == "devstatedow": val = self.conditionsDow (dev, index)
			
			if dev.pluginProps["condition" + str(index)] == "datetime" or dev.pluginProps["condition" + str(index)] == "devstatedatetime" or dev.pluginProps["condition" + str(index)] == "vardatetime": val = self.conditionsDate (dev, index)
			
			if dev.pluginProps["condition" + str(index)] == "device":
				val = [0, 0] # Failsafe
				devEx = indigo.devices[int(dev.pluginProps["device" + str(index)])]
				if eps.valueValid (devEx.states, dev.pluginProps["state" + str(index)]):
					compareString = unicode(devEx.states[dev.pluginProps["state" + str(index)]])
					self.debugLog ("\tChecking if device state '%s' value of '%s' is equal to '%s'" % (dev.pluginProps["state" + str(index)], compareString, dev.pluginProps["value" + str(index)]))
					
					if compareString.lower() == dev.pluginProps["value" + str(index)].lower():
						val[0] = 1
						val[1] = 0
					else:
						val[0] = 0
						val[1] = 1
						
			if dev.pluginProps["condition" + str(index)] == "variable":
				val = [0, 0] # Failsafe
				var = indigo.variables[int(dev.pluginProps["variable" + str(index)])]
				compareString = unicode(var.value)
				self.debugLog ("\tChecking if variable '%s' value of '%s' is equal to '%s'" % (var.name, compareString, dev.pluginProps["value" + str(index)]))
									
				if compareString.lower() == dev.pluginProps["value" + str(index)].lower():
					val[0] = 1
					val[1] = 0
				else:
					val[0] = 0
					val[1] = 1
			
			if dev.pluginProps["evaluation" + str(index)] == "equal":
				isTrue = isTrue + val[0]
				isFalse = isFalse + val[1]						
			else:
				# It's the negative version so reverse the values
				isTrue = isTrue + val[1]
				isFalse = isFalse + val[0]
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
		
	#
	# Check condition evaluation BETWEEN
	#
	def conditionBetween (self, dev, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			#if dev.pluginProps["condition" + str(index)] == "timeonly" or dev.pluginProps["condition" + str(index)] == "devstatetimeonly" or dev.pluginProps["condition" + str(index)] == "vartimeonly": val = self.conditionsDateBetween (dev, index, True, False)
			#if dev.pluginProps["condition" + str(index)] == "dateonly" or dev.pluginProps["condition" + str(index)] == "devstatedateonly" or dev.pluginProps["condition" + str(index)] == "vardateonly": val = self.conditionsDateBetween (dev, index, False, True)
			#if dev.pluginProps["condition" + str(index)] == "datetime" or dev.pluginProps["condition" + str(index)] == "devstatedatetime" or dev.pluginProps["condition" + str(index)] == "vardatetime": val = self.conditionsDateBetween (dev, index, True, True)
			#if dev.pluginProps["condition" + str(index)] == "dow" or dev.pluginProps["condition" + str(index)] == "devstatedow": val = self.conditionsDow (dev, index)
			
			if dev.pluginProps["condition" + str(index)] == "datetime" or dev.pluginProps["condition" + str(index)] == "devstatedatetime" or dev.pluginProps["condition" + str(index)] == "vardatetime": val = self.conditionsDate (dev, index)
			
			if dev.pluginProps["condition" + str(index)] == "device":
				val = [0, 0] # Failsafe
				devEx = indigo.devices[int(dev.pluginProps["device" + str(index)])]
				if eps.valueValid (devEx.states, dev.pluginProps["state" + str(index)]):
					compareString = unicode(devEx.states[dev.pluginProps["state" + str(index)]])
					self.debugLog ("\tChecking if device state '%s' value of '%s' is between '%s' and '%s'" % (dev.pluginProps["state" + str(index)], compareString, dev.pluginProps["value" + str(index)], dev.pluginProps["endValue" + str(index)]))
					
					if compareString.lower() >= dev.pluginProps["value" + str(index)].lower() and compareString.lower() <= dev.pluginProps["endValue" + str(index)].lower():
						val[0] = 1
						val[1] = 0
					else:
						val[0] = 0
						val[1] = 1
						
			if dev.pluginProps["condition" + str(index)] == "variable":
				val = [0, 0] # Failsafe
				var = indigo.variables[int(dev.pluginProps["variable" + str(index)])]
				compareString = unicode(var.value)
				self.debugLog ("\tChecking if variable '%s' value of '%s' is between '%s' and '%s'" % (var.name, compareString, dev.pluginProps["value" + str(index)], dev.pluginProps["endValue" + str(index)]))
									
				if compareString.lower() >= dev.pluginProps["value" + str(index)].lower() and compareString.lower() <= dev.pluginProps["endValue" + str(index)].lower():
					val[0] = 1
					val[1] = 0
				else:
					val[0] = 0
					val[1] = 1
		
			if dev.pluginProps["evaluation" + str(index)] == "between":
				isTrue = isTrue + val[0]
				isFalse = isFalse + val[1]						
			else:
				# It's the negative version so reverse the values
				isTrue = isTrue + val[1]
				isFalse = isFalse + val[0]
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 0
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
	
	
	################################################################################
	# DATE CONDITIONS
	################################################################################	
	
	#
	# Evaluate conditions for date/time
	#
	def conditionsDate (self, dev, index):
		ret = []
		isTrue = 0
		isFalse = 0
		
		try:
			d = indigo.server.getTime()
			
			# If we are using a device state date (has devstate as prefix) then use that date instead
			if string.find (dev.pluginProps["condition" + str(index)], 'devstate') > -1:
				devEx = indigo.devices[int(dev.pluginProps["device" + str(index)])]
				d = self.getDevStateDateTime (dev, devEx, index)
				
			# If using a variable
			if string.find (dev.pluginProps["condition" + str(index)], 'var') > -1:
				d = self.getVarDateTime (dev, index)
				
			# Get the comparison
			startDate = self.getDateComparison (dev, index, d, "start")
				
			if dev.pluginProps["evaluation" + str(index)] == "equal" or dev.pluginProps["evaluation" + str(index)] == "notequal":
				self.debugLog ("\tChecking if calculated date of %s is equal to comparison date %s" % (startDate.strftime ("%Y-%m-%d %H:%M"), d.strftime ("%Y-%m-%d %H:%M")))
				
				if startDate == d:
					isTrue = 1
				else:
					isFalse = 1
					
			if dev.pluginProps["evaluation" + str(index)] == "greater":
				self.debugLog ("\tChecking if calculated date of %s is greater than comparison date %s" % (startDate.strftime ("%Y-%m-%d %H:%M"), d.strftime ("%Y-%m-%d %H:%M")))
				
				if startDate > d:
					isTrue = 1
				else:
					isFalse = 1
					
			if dev.pluginProps["evaluation" + str(index)] == "less":
				self.debugLog ("\tChecking if calculated date of %s is less than comparison date %s" % (startDate.strftime ("%Y-%m-%d %H:%M"), d.strftime ("%Y-%m-%d %H:%M")))
				
				if startDate < d:
					isTrue = 1
				else:
					isFalse = 1
					
			if dev.pluginProps["evaluation" + str(index)] == "between" or dev.pluginProps["evaluation" + str(index)] == "notbetween":
				endDate = self.getDateComparison (dev, index, d, "end")
				self.debugLog ("\tChecking if comparison date of %s is between calculated dates of %s to %s" % (d.strftime ("%Y-%m-%d %H:%M"), startDate.strftime ("%Y-%m-%d %H:%M"), endDate.strftime ("%Y-%m-%d %H:%M")))
				
				if d >= startDate and d <= endDate:
					isTrue = 1
				else:
					isFalse = 1
			
		
		except Exception as e:
			eps.printException(e) 
			isTrue = 0
			isFalse = 1
			
		ret.append(isTrue)
		ret.append(isFalse)
		
		return ret
		
	#
	# Get week day iteration for a given month and year
	#
	def getDayIteration (self, year, month, iteration, dow):
		try:
			days = calendar.monthrange(year, month)
			maxDays = days[1]
			
			dow = int(dow)
			iteration = iteration.lower()
			count = 0
			dayidx = 0
			
			for i in range (1, maxDays + 1):
				s = str(year) + "-" + "%02d" % month + "-" + "%02d" % i
				d = datetime.datetime.strptime (s, "%Y-%m-%d")
				
				if int(d.strftime("%w")) == dow:
					count = count + 1
					dayidx = i # the last day that matches our dow
					
					if iteration == "first" and count == 1: return d
					if iteration == "second" and count == 2: return d
					if iteration == "third" and count == 3: return d
					if iteration == "fourth" and count == 4: return d
					
			# If we haven't yet returned then check if it's the last
			if iteration == "last" and count > 0:
				s = str(year) + "-" + "%02d" % month + "-" + "%02d" % dayidx
				d = datetime.datetime.strptime (s, "%Y-%m-%d")
				return d
		
		except Exception as e:
			eps.printException(e) 
	
	
	#
	# Evaluate conditional date against passed date and create a date to compare to
	#
	def getDateComparison (self, dev, index, d, prefix):
		curDate = indigo.server.getTime()
		
		try:
			# For now assume all values are equal to the date passed, this allows for use of "any" as
			# the value, because it's "any" that means that field will always match the comparison date
			year = int(d.strftime("%Y"))
			month = int(d.strftime("%m"))
			day = int(d.strftime("%d"))
			hour = int(d.strftime("%H"))
			minute = int(d.strftime("%M"))
			second = 0 # we never care about seconds
			
			# Evaluate the year
			if dev.pluginProps[prefix + "Year" + str(index)] == "any": 
				year = year # do nothing, the default is already this
				
			elif dev.pluginProps[prefix + "Year" + str(index)] == "current": 
				year = int(curDate.strftime("%Y"))
				
			elif dev.pluginProps[prefix + "Year" + str(index)] == "last": 
				year = int(curDate.strftime("%Y")) - 1
				
			elif dev.pluginProps[prefix + "Year" + str(index)] == "last": 
				year = int(curDate.strftime("%Y")) + 1	
			
			else:
				year = int(dev.pluginProps[prefix + "Year" + str(index)]) # with no other options, they chose an actual year
				
			
			# Evaluate the month
			if dev.pluginProps[prefix + "Month" + str(index)] != "any": month = int(dev.pluginProps[prefix + "Month" + str(index)])
			
			# Evaluate the day
			if dev.pluginProps[prefix + "Day" + str(index)] == "any":
				day = day # do nothing, the default is already this
				
			elif dev.pluginProps[prefix + "Day" + str(index)] == "first" or dev.pluginProps[prefix + "Day" + str(index)] == "second" or dev.pluginProps[prefix + "Day" + str(index)] == "third" or dev.pluginProps[prefix + "Day" + str(index)] == "fourth" or dev.pluginProps[prefix + "Day" + str(index)] == "last":
				newdate = self.getDayIteration(year, month, dev.pluginProps[prefix + "Day" + str(index)], dev.pluginProps[prefix + "Dow" + str(index)])
				year = int(newdate.strftime("%Y"))
				month = int(newdate.strftime("%m"))
				day = int(newdate.strftime("%d"))
				
			elif dev.pluginProps[prefix + "Day" + str(index)] == "lastday":
				day = calendar.monthrange(year, month)
				day = day[1]
				
			else:
				day = int(dev.pluginProps[prefix + "Day" + str(index)]) # they chose a day
				
				
			# Evaluate the time
			if dev.pluginProps[prefix + "Time" + str(index)] == "any":
				hour = hour # do nothing, the default is already this
				
			else:
				time = dev.pluginProps[prefix + "Time" + str(index)]
				time = time.split(":")
				hour = int(time[0])
				minute = int(time[1])
				second = 0
				
			
			# Re-assemble the date and return it
			retstr = str(year) + "-" + "%02d" % month + "-" + "%02d" % day + " " + "%02d" % hour + ":" + "%02d" % minute + ":" + "%02d" % second
			ret = datetime.datetime.strptime (retstr, "%Y-%m-%d %H:%M:%S")
			return ret
			
		except Exception as e:
			eps.printException(e) 
			return curDate
			
		
	################################################################################
	# LIBRARY SPECIFIC METHODS
	################################################################################	
	
	#
	# Get variable date and time in user format
	#
	def getVarDateTime (self, dev, index):
		d = indigo.server.getTime()
		
		try:
			if eps.valueValid (dev.pluginProps, "variable" + str(index), True) and eps.valueValid (dev.pluginProps, "dtFormat" + str(index), True):
				compareString = indigo.variables[int(dev.pluginProps["variable" + str(index)])].value
				self.debugLog ("\tConverting variable '%s' date of '%s' using format '%s'" % (indigo.variables[int(dev.pluginProps["variable" + str(index)])].name, compareString, dev.pluginProps["dtFormat" + str(index)]))
				d = datetime.datetime.strptime (compareString, dev.pluginProps["dtFormat" + str(index)])
				
		except Exception as e:
			eps.printException(e) 
			
		return d	
		
	#
	# Get device state date and time in user format
	#
	def getDevStateDateTime (self, dev, devEx, index):
		d = indigo.server.getTime()
		
		try:
			if eps.valueValid (devEx.states, dev.pluginProps["state" + str(index)]) and eps.valueValid (dev.pluginProps, "dtFormat" + str(index), True):
				compareString = unicode(devEx.states[dev.pluginProps["state" + str(index)]])
				self.debugLog ("\tConverting state '%s' date of '%s' using format '%s'" % (dev.pluginProps["state" + str(index)], compareString, dev.pluginProps["dtFormat" + str(index)]))
				d = datetime.datetime.strptime (compareString, dev.pluginProps["dtFormat" + str(index)])
		
		except Exception as e:
			eps.printException(e) 
			
		return d		
		
	################################################################################
	# UI
	################################################################################
	
	#
	# Validate the UI
	#
	def validateDeviceConfigUi(self, valuesDict, typeId, devId):
		self.debugLog ("Validating conditions on device")
		errorDict = indigo.Dict()
		msg = ""
		
		for i in range (1, self.maxConditions + 1):
			if eps.valueValid (valuesDict, "condition" + str(i), True):
				if valuesDict["condition" + str(i)] == "device" or valuesDict["condition" + str(i)] == "devstatedatetime":
					if valuesDict["state" + str(i)] == "":
						errorDict["state" + str(i)] = "State is required"
						msg += "Condition %i is missing required state.  " % i
			
				if valuesDict["condition" + str(i)] == "variable" or valuesDict["condition" + str(i)] == "vardatetime":
					if valuesDict["variable" + str(i)] == "":
						errorDict["variable" + str(i)] = "Variable is required"
						msg += "Condition %i is missing required variable.  " % i
						
				if valuesDict["condition" + str(i)] == "datetime" or valuesDict["condition" + str(i)] == "devstatedatetime" or valuesDict["condition" + str(i)] == "vardatetime":
					if valuesDict["startDay" + str(i)] == "first" or valuesDict["startDay" + str(i)] == "second" or valuesDict["startDay" + str(i)] == "third" or valuesDict["startDay" + str(i)] == "fourth" or valuesDict["startDay" + str(i)] == "last":
						if valuesDict["startDow" + str(i)] == "any":
							errorDict["startDow" + str(i)] = "Can't use 'any' when using calculations in the day field"
							msg += "Condition %i is using '%s' as the start day but 'any' for the day of the week.\n\n" % (i, valuesDict["startDay" + str(i)])
							
					if valuesDict["endDay" + str(i)] == "first" or valuesDict["endDay" + str(i)] == "second" or valuesDict["endDay" + str(i)] == "third" or valuesDict["endDay" + str(i)] == "fourth" or valuesDict["endDay" + str(i)] == "last":
						if valuesDict["endDow" + str(i)] == "any":
							errorDict["endDow" + str(i)] = "Can't use 'any' when using calculations in the end day field"
							msg += "Condition %i is using '%s' as the end day but 'any' for the day of the week.\n\n" % (i, valuesDict["endDay" + str(i)])
							
					if valuesDict["startYear" + str(i)] == "any" and valuesDict["startMonth" + str(i)] == "any" and valuesDict["startDay" + str(i)] == "any" and valuesDict["startDow" + str(i)] == "any" and valuesDict["startTime" + str(i)] == "any":
						if valuesDict["evaluation" + str(i)] == "between" or valuesDict["evaluation" + str(i)] == "notbetween":
							if valuesDict["endYear" + str(i)] == "any" and valuesDict["endMonth" + str(i)] == "any" and valuesDict["endDay" + str(i)] == "any" and valuesDict["endDow" + str(i)] == "any" and valuesDict["endTime" + str(i)] == "any":
								errorDict["startYear" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["startMonth" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["startDay" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["startDow" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["startTime" + str(i)] = "Catch-all defeats the purpose of a condition"
								
								errorDict["endYear" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["endMonth" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["endDay" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["endDow" + str(i)] = "Catch-all defeats the purpose of a condition"
								errorDict["endTime" + str(i)] = "Catch-all defeats the purpose of a condition"
						
								msg += "Condition %i is using 'any' for all fields, this defeats the purpose of having a condition!  Try changing at least one to something else.\n\n" % (i)
						else:
							errorDict["startYear" + str(i)] = "Catch-all defeats the purpose of a condition"
							errorDict["startMonth" + str(i)] = "Catch-all defeats the purpose of a condition"
							errorDict["startDay" + str(i)] = "Catch-all defeats the purpose of a condition"
							errorDict["startDow" + str(i)] = "Catch-all defeats the purpose of a condition"
							errorDict["startTime" + str(i)] = "Catch-all defeats the purpose of a condition"
							
							msg += "Condition %i is using 'any' for all fields, this defeats the purpose of having a condition!  Try changing at least one to something else.\n\n" % (i)
							
					fields = ["Year", "Month", "Day", "Dow", "Time"]
					for s in fields:
						if valuesDict["evaluation" + str(i)] == "between" or valuesDict["evaluation" + str(i)] == "notbetween":
							if valuesDict["start" + s + str(i)] == "-1":
								errorDict["start" + s + str(i)] = "You must select a value"
								msg += "Condition %i field %s has an invalid value.\n\n" % (i, s)
					
							if valuesDict["end" + s + str(i)] == "-1":
								errorDict["end" + s + str(i)] = "You must select a value"
								msg += "Condition %i field End %s has an invalid value.\n\n" % (i, s)
						else:
							if valuesDict["start" + s + str(i)] == "-1":
								errorDict["start" + s + str(i)] = "You must select a value"
								msg += "Condition %i field %s has an invalid value.\n\n" % (i, s)
				
		if msg != "":
			msg = "There are problems with your conditions:\n\n" + msg
			errorDict["showAlertText"] = msg
			return (False, valuesDict, errorDict)
		
		return (True, valuesDict)
	
	#
	# Return custom list with condition options
	#
	def getConditionDateValues(self, filter="", valuesDict=None, typeId="", targetId=0):
		ret = ui.getDataList (filter, valuesDict, typeId, targetId)
		
		try:
			option = ("any", "any")
			ret.insert(0, option)
			i = 1 # where the line will go
			
			x = string.find (filter, 'monthdays')
			if x > -1:
				options = ["lastday|last day of the month", "first|first week day", "second|second week day", "third|third week day", "fourth|fourth week day", "last|last week day"]
				
				for s in options:
					data = s.split("|")
					option = (data[0], data[1])
					ret.insert(i, option)
					i = i + 1 # move the line
					
			if filter == "years":
				options = ["current|this year", "last|last year", "next|next year"]
				
				for s in options:
					data = s.split("|")
					option = (data[0], data[1])
					ret.insert(i, option)
					i = i + 1 # move the line
			
			option = ("-1", "----------------------------------")
			ret.insert(i, option)
			
		except Exception as e:
			eps.printException(e)
				
		return ret
	
	#
	# Collapse all conditions except for #1 (called from deviceUpdated)
	#
	def collapseAllConditions (self, dev):
		try:
			props = dev.pluginProps
			
			# See if this is a brand new device and if it is then set defaults
			if eps.valueValid (dev.pluginProps, "isNewDevice"):
				if dev.pluginProps["isNewDevice"]:
					#indigo.server.log("%s added, enabling conditions.  You can now re-open the device to use conditions" % dev.name)
					props["conditions"] = "none"
					props["isNewDevice"] = False
					
					for i in range (1, self.maxConditions + 1):
						props = self.setUIDefaults (props, "disabled", "onOffState")
					
					dev.replacePluginPropsOnServer(props)
					return # don't do anything else
									
			# Set up collapse options
			if eps.valueValid (dev.pluginProps, "expandConditions1"): 
				if props["expandConditions1"] == False:
					props["expandConditions1"] = True
					props["currentCondition"] = "1"
					props["noneExpanded"] = False
					
					# Check for multiple conditions to see if we need the padding
					if props["conditions"] != "none":
						for i in range (2, self.maxConditions + 1):
							if eps.valueValid (dev.pluginProps, "expandConditions" + str(i)): 
								props["multiConditions"] = True # gives us extra padding on multiple conditions
								break
							
					props = self.setUIValueVisibility (props, 1)
			else:
				# If we don't have condition 1 then we don't have any
				return
			
			for i in range (2, self.maxConditions + 1):
				if eps.valueValid (dev.pluginProps, "expandConditions" + str(i)): 
					if dev.pluginProps["expandConditions" + str(i)]: 
						props["expandConditions" + str(i)] = False
						props = self.setUIDefaults (props, "disabled", "onOffState")
					
			if props != dev.pluginProps: 
				self.debugLog ("Collapsing all conditions for %s" % dev.name)
				dev.replacePluginPropsOnServer(props)
			
		except Exception as e:
			eps.printException(e)
				
		return
	
	#
	# Add condition to pop up options
	#
	def addUIConditionMenu (self, popupList):
		try:
			if popupList is None:
				popupList = []
				
			evalList = ["none|No conditions", "alltrue|All items are true", "anytrue|Any items are true", "allfalse|All items are false", "anyfalse|Any items are false"]
			
			for s in evalList:
				eval = s.split("|")
				option = (eval[0], eval[1])
				popupList.append (option)
		
		except Exception as e:
			eps.printException(e) 
			
			popupList = []
			option = ("error", "Error in conditions, see Indigo log")
			popupList.append (option)
			
		return popupList
	
	#
	# Add evaluation to pop up options
	#
	def addUIEvals (self, popupList):
		try:
			if popupList is None:
				popupList = []
				
			evalList = ["equal|Equal to", "notequal|Not equal to", "greater|Greater than", "less|Less than", "between|Between", "notbetween|Not between", "contains|Containing", "notcontains|Not containing"]
			
			for s in evalList:
				eval = s.split("|")
				option = (eval[0], eval[1])
				popupList.append (option)
		
		except Exception as e:
			eps.printException(e) 
			
			popupList = []
			option = ("error", "Error in evaluations, see Indigo log")
			popupList.append (option)
			
		return popupList
			
	#
	# Add conditions to pop up options
	#
	def appendUIConditions (self, popupList, type = "device"):
		try:
			type = type.lower()
			
			if popupList is None:
				popupList = []
				
			option = ("disabled", "- CONDITION DISABLED -")
			popupList.append (option)
				
			if type == "device" or type == "all":
				option = ("device", "Device state")
				popupList.append (option)
				
			if type == "variable" or type == "all":
				option = ("variable", "Variable value")
				popupList.append (option)
				
			if type == "datetime" or type == "all":
				option = ("datetime", "Date and time")
				popupList.append (option)
				
			if type == "devstatedate" or type == "all":
				option = ("devstatedatetime", "Date and time from device state")
				popupList.append (option)
								
			if type == "vardate" or type == "all":
				option = ("vardatetime", "Date and time from variable")
				popupList.append (option)
				
				
		except Exception as e:
			eps.printException(e) 
			
			popupList = []
			option = ("error", "Error in conditions, see Indigo log")
			popupList.append (option)
			
		return popupList
	
	#
	# Set up any UI defaults that we need
	#
	def setUIDefaults (self, valuesDict, defaultCondition = "disabled", defaultState = "onOffState"):
		try:
			# Make sure times are defaulted
			if eps.valueValid (valuesDict, "startTime1", True) == False:
				self.debugLog ("Setting default values")
				for i in range (1, self.maxConditions + 1):
					if eps.valueValid (valuesDict, "condition" + str(i)): valuesDict["condition" + str(i)] = defaultCondition
					if eps.valueValid (valuesDict, "evaluation" + str(i)): valuesDict["evaluation" + str(i)] = "equal"
					if eps.valueValid (valuesDict, "state" + str(i)): valuesDict["state" + str(i)] = defaultState
					if eps.valueValid (valuesDict, "startTime" + str(i)): valuesDict["startTime" + str(i)] = "08:00"
					if eps.valueValid (valuesDict, "endTime" + str(i)): valuesDict["endTime" + str(i)] = "09:00"
					if eps.valueValid (valuesDict, "startMonth" + str(i)): valuesDict["startMonth" + str(i)] = "01"
					if eps.valueValid (valuesDict, "endMonth" + str(i)): valuesDict["endMonth" + str(i)] = "02"
					if eps.valueValid (valuesDict, "startDay" + str(i)): valuesDict["startDay" + str(i)] = "01"
					if eps.valueValid (valuesDict, "endDay" + str(i)): valuesDict["endDay" + str(i)] = "15"
					if eps.valueValid (valuesDict, "startDow" + str(i)): valuesDict["startDow" + str(i)] = "0"
					if eps.valueValid (valuesDict, "endDow" + str(i)): valuesDict["endDow" + str(i)] = "6"
					if eps.valueValid (valuesDict, "startYear" + str(i)): valuesDict["startYear" + str(i)] = "any"
					if eps.valueValid (valuesDict, "endYear" + str(i)): valuesDict["endYear" + str(i)] = "any"
			
			valuesDict = self.autoCollapseConditions (valuesDict)
			valuesDict = self.showPlaceholders (valuesDict)
			
			# If everything is collapsed then show the full placeholder if conditions are enabled
			if valuesDict["currentCondition"] == "0" and valuesDict["conditions"] != "none":
				self.debugLog("Current block is 0, setting placeholder")
				valuesDict["noneExpanded"] = True
			else:
				valuesDict["noneExpanded"] = False
			
			
			#indigo.server.log("\n" + unicode(valuesDict))
			return valuesDict
						
		except Exception as e:
			eps.printException(e)
				
		return valuesDict
	
	#
	# Show/hide placeholder blocks for the current condition (largest to base on is device state date/time with between)
	#
	def showPlaceholders (self, valuesDict):
		try:
			if self.enablePlaceholders == False: return valuesDict
			
			cb = valuesDict["currentCondition"]
			currentBlock = int(cb)
			if currentBlock == 0: return valuesDict # nothing to do
						
			# Disable all condition blocks
			valuesDict["isDisabled"] = False
			valuesDict["placeThree"] = False
			valuesDict["placeFour"] = False
			valuesDict["placeFive"] = False
			valuesDict["placeSix"] = False 
			valuesDict["placeSeven"] = False 
			valuesDict["placeNine"] = False 
			valuesDict["placeTen"] = False 
			valuesDict["placeThirteen"] = False
			valuesDict["placeFifteen"] = False 
						
			# If there are no conditions
			if valuesDict["conditions"] == False:
				self.debugLog ("No conditions, current block is 0")
				valuesDict["currentCondition"] = "0" # it's the current condition and got collapsed, meaning all are collapsed
				return valuesDict
			
			# If it's collapsed then show that placeholder and return
			if valuesDict["expandConditions" + cb] == False:
				self.debugLog ("All blocks collapsed, current block is 0")
				valuesDict["currentCondition"] = "0" # it's the current condition and got collapsed, meaning all are collapsed
				return valuesDict
			
			valuesDict["multiConditions"] = False # Always turn it off here, save and close always turns it on

			bt = False # We have a "between" that extends things
			if valuesDict["evaluation" + cb] == "between" or valuesDict["evaluation" + cb] == "notbetween": bt = True
				
			if valuesDict["condition" + cb] == "disabled":
				valuesDict["isDisabled"] = True
				
			elif valuesDict["condition" + cb] == "timeonly" or valuesDict["condition" + cb] == "dow":
				valuesDict["placeThree"] = True
			
			elif (valuesDict["condition" + cb] == "variable" and bt == False) or valuesDict["condition" + cb] == "dateonly":
				valuesDict["placeFour"] = True
				
			elif (valuesDict["condition" + cb] == "device" and bt == False) or (valuesDict["condition" + cb] == "variable" and bt):
				valuesDict["placeFive"] = True
				
			elif (valuesDict["condition" + cb] == "device" and bt):
				valuesDict["placeSix"] = True
				
			elif (valuesDict["condition" + cb] == "datetime" and bt == False):
				valuesDict["placeSeven"] = True	
				
			elif (valuesDict["condition" + cb] == "vardatetime" and bt == False):
				valuesDict["placeNine"] = True	
				
			elif (valuesDict["condition" + cb] == "devstatedatetime" and bt == False):
				valuesDict["placeTen"] = True	
			
			elif (valuesDict["condition" + cb] == "datetime" and bt):
				valuesDict["placeThirteen"] = True	
				
			elif (valuesDict["condition" + cb] == "vardatetime" and bt):
				valuesDict["placeFifteen"] = True	
		
		except Exception as e:
			eps.printException(e)
				
		return valuesDict
	
	#
	# Auto collapse condition blocks based on what was most recently expanded
	#
	def autoCollapseConditions (self, valuesDict):
		try:
			currentBlock = int(valuesDict["currentCondition"])
			
			# Run through all conditions, if any other than the current is checked then update
			for i in range (1, self.maxConditions + 1):	
				if eps.valueValid (valuesDict, "expandConditions" + str(i)):
					if valuesDict["expandConditions" + str(i)] and i != currentBlock:
						currentBlock = i
						break
					
			# Now collapse all but the current block
			for i in range (1, self.maxConditions + 1):	
				if eps.valueValid (valuesDict, "expandConditions" + str(i)):	
					if i != currentBlock: valuesDict["expandConditions" + str(i)] = False
						
			# Hide/show fields for all unexpanded/expanded conditions
			for i in range (1, self.maxConditions + 1):	
				if eps.valueValid (valuesDict, "expandConditions" + str(i)):
					valuesDict = self.setUIValueVisibility (valuesDict, i) # also hide options
					
			# Save the current block
			self.debugLog ("Current condition block set to %i" % currentBlock)
			valuesDict["currentCondition"] = str(currentBlock)
				
		except Exception as e:
			eps.printException(e)
				
		return valuesDict	
		
	#
	# Hide or show the end value or end time
	#
	def setUIValueVisibility (self, valuesDict, index):
		try:
			# Turn off everything, we'll turn it on below
			valuesDict["hasStartValue" + str(index)] = False
			valuesDict["hasStartTime" + str(index)] = False
			valuesDict["hasStartDate" + str(index)] = False
			valuesDict["hasStartDow" + str(index)] = False
					
			valuesDict["hasEndValue" + str(index)] = False
			valuesDict["hasEndTime" + str(index)] = False
			valuesDict["hasEndDate" + str(index)] = False
			valuesDict["hasEndDow" + str(index)] = False
			
			valuesDict["hasPythonFormat" + str(index)] = False
			valuesDict["hasDevice" + str(index)] = False
			valuesDict["hasVariable" + str(index)] = False
			
			if valuesDict["conditions"] == "none": 
				#self.debugLog ("Condition checking has been turned off, disabling all condition fields")
				return valuesDict # nothing more to do, they turned off condition checking
				
			if valuesDict["expandConditions" + str(index)] == False:
				#self.debugLog ("Condition %i is collapsed" % index)
				return valuesDict # nothing more to do, they turned off condition checking
				
			if valuesDict["condition" + str(index)] == "disabled":
				#self.debugLog ("Condition %i is disabled" % index)
				return valuesDict # nothing more to do, they turned off condition checking
			
			# Turn on start values
			if valuesDict["condition" + str(index)] == "device" or valuesDict["condition" + str(index)] == "variable":
				valuesDict["hasStartValue" + str(index)] = True
				if valuesDict["condition" + str(index)] == "device": valuesDict["hasDevice" + str(index)] = True
				if valuesDict["condition" + str(index)] == "variable": valuesDict["hasVariable" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "dateonly":
				valuesDict["hasStartDate" + str(index)] = True
			
			elif valuesDict["condition" + str(index)] == "timeonly":
				valuesDict["hasStartTime" + str(index)] = True
			
			elif valuesDict["condition" + str(index)] == "dow":
				valuesDict["hasStartDow" + str(index)] = True
			
			elif valuesDict["condition" + str(index)] == "datetime":
				valuesDict["hasStartTime" + str(index)] = True
				valuesDict["hasStartDate" + str(index)] = True
			
			elif valuesDict["condition" + str(index)] == "devstatedateonly":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartDate" + str(index)] = True	
				valuesDict["hasDevice" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "devstatetimeonly":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartTime" + str(index)] = True
				valuesDict["hasDevice" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "devstatedatetime":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartTime" + str(index)] = True
				valuesDict["hasStartDate" + str(index)] = True
				valuesDict["hasDevice" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "devstatedow":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartDow" + str(index)] = True
				valuesDict["hasDevice" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "vardateonly":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartDate" + str(index)] = True	
				valuesDict["hasVariable" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "vartimeonly":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartTime" + str(index)] = True
				valuesDict["hasVariable" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "vardatetime":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartTime" + str(index)] = True
				valuesDict["hasStartDate" + str(index)] = True
				valuesDict["hasVariable" + str(index)] = True
				
			elif valuesDict["condition" + str(index)] == "vardow":
				valuesDict["hasPythonFormat" + str(index)] = True
				valuesDict["hasStartDow" + str(index)] = True
				valuesDict["hasVariable" + str(index)] = True
								
			if valuesDict["evaluation" + str(index)] == "between" or valuesDict["evaluation" + str(index)] == "notbetween":
				self.debugLog ("Condition %i requires an end value" % index)
			
				# See if we need to show or hide the end value or date/time contains value
				if valuesDict["condition" + str(index)] == "device" or valuesDict["condition" + str(index)] == "variable":
					valuesDict["hasEndValue" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "devdate" or valuesDict["condition" + str(index)] == "vardate":
					valuesDict["hasEndValue" + str(index)] = True
					valuesDict["hasPythonFormat" + str(index)] = True
									
				elif valuesDict["condition" + str(index)] == "dateonly":
					valuesDict["hasEndDate" + str(index)] = True
										
				elif valuesDict["condition" + str(index)] == "timeonly":
					valuesDict["hasEndTime" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "dow":
					valuesDict["hasEndDow" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "datetime":
					valuesDict["hasEndTime" + str(index)] = True
					valuesDict["hasEndDate" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "devstatedateonly":
					valuesDict["hasEndDate" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "devstatetimeonly":
					valuesDict["hasEndTime" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "devstatedow":
					valuesDict["hasEndDow" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "devstatedatetime":
					valuesDict["hasEndTime" + str(index)] = True
					valuesDict["hasEndDate" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "vardateonly":
					valuesDict["hasEndDate" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "vartimeonly":
					valuesDict["hasEndTime" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "vardow":
					valuesDict["hasEndDow" + str(index)] = True
					
				elif valuesDict["condition" + str(index)] == "vardatetime":
					valuesDict["hasEndTime" + str(index)] = True
					valuesDict["hasEndDate" + str(index)] = True
					
				else:
					indigo.server.log ("Unknown between condition for %i" % index, isError=True)
				
			elif valuesDict["evaluation" + str(index)] == "contains" or valuesDict["evaluation" + str(index)] == "notcontains":
				# Turn off start date fields since they aren't used here
				valuesDict["hasStartTime" + str(index)] = False
				valuesDict["hasStartDate" + str(index)] = False
				valuesDict["hasStartDow" + str(index)] = False
				
				valuesDict["hasEndValue" + str(index)] = False
				valuesDict["hasEndTime" + str(index)] = False
				valuesDict["hasEndDate" + str(index)] = False
				valuesDict["hasEndDow" + str(index)] = False
				valuesDict["hasStartValue" + str(index)] = True
				
		
		except Exception as e:
			eps.printException(e)
				
		return valuesDict	
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		