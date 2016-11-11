# -*- coding: utf-8 -*-
# mnis.mnislib module

"""
Name: mnislib.py
Author: Oliver Hawkins
About: A library of ad-hoc functions for downloading data from 
the Members Names Information Service (MNIS) at data.parliament.uk. 

A description of the MNIS API can be found here:
http://data.parliament.uk/membersdataplatform/memberquery.aspx
http://data.parliament.uk/membersdataplatform/fixedscope.aspx

OData API links
http://data.parliament.uk/membersdataplatform/open.aspx
http://data.parliament.uk/membersdataplatform/schema/main.html
http://stackoverflow.com/questions/10112376/how-to-consume-odata-service-with-html-javascript

"""

import datetime
import requests
import json
import csv
import mnis.housedata as housedata

# Package Exceptions ---------------------------------------------------------

class Error(Exception):
	
	"""Base class for exceptions in this module."""	
	pass

class ParameterError(Error):
	"""Exception raised for errors with request parameters."""	
	pass

class ElectionIdError(ParameterError):
	"""Exception raised for invalid election ids."""	
	pass

class MembershipError(Error):
	"""Exception raised when membership data from MNIS is nonsensical."""
	pass


# Functions which return a list of members -----------------------------------

def getCurrentCommonsMembers(outputParameters= \
	['Constituencies', 'Parties', 'HouseMemberships']):

	"""Returns all Commons members on the current date."""

	return getCommonsMembersOn(datetime.date.today(), outputParameters)


def getCommonsMembersOn(date, outputParameters= \
	['Constituencies', 'Parties', 'HouseMemberships']):

	"""
	Returns all Commons members on a given date, which must be
	an instance of datetime.date.
	"""
	
	return getCommonsMembersBetween(date, date, outputParameters)


def getCommonsMembersBetween(startDate, endDate, outputParameters= \
	['Constituencies', 'Parties', 'HouseMemberships']):

	"""
	Returns all Commons members between startDate and endDate,
	which must be instances of datetime.date.
	"""

	s = '{0}-{1}-{2}'.format(startDate.year, startDate.month, startDate.day)
	e = '{0}-{1}-{2}'.format(endDate.year, endDate.month, endDate.day)
	urlParameters = 'commonsmemberbetween={0}and{1}'.format(s, e)
	
	return getCommonsMembers(urlParameters, outputParameters)


def getCommonsMembersAtElection(generalElectionId, outputParameters= \
	['Constituencies', 'Parties', 'HouseMemberships']):

	"""
	Returns all Commons members elected at a given general election.
	The MNIS system holds complete data on general elections since 1983. 
	The generalElectionId must be one of the following strings: 1983, 1987, 
	1992, 1997, 2001, 2005, 2010, 2015.
	"""

	validElectionIds = [ \
		'1983', '1987', '1992', '1997', '2001', '2005', '2010', '2015']

	if generalElectionId not in validElectionIds:
		raise ElectionIdError("Invalid id in getCommonsMembersAtElection")

	urlParameters = 'returnedatelection={0}' \
		'%20General%20Election'.format(generalElectionId)

	return getCommonsMembers(urlParameters, outputParameters)


def buildMnisUrl(urlParameters, outputParameters):

	"""
	Builds a valid MNIS URL for the given parameters. The function raises a
	parameter error if more than three output parameters are passed as the
	API only allows up to three output parameters per request.
	"""

	if len(outputParameters) > 3:
		raise ParameterError( \
			"More than three output parameters in buildMnisUrl")

	url = 'http://data.parliament.uk/membersdataplatform/services/' \
		'mnis/members/query/House=Commons|Membership=all|{0}/{1}' \
		.format(urlParameters, '|'.join(outputParameters))

	return url


def getCommonsMembers(urlParameters, outputParameters= \
	['Constituencies', 'Parties', 'HouseMemberships']):

	"""
	Returns all commons members with the given URL paramemters. The 
	"house=Commons" parameter is not necessary as it is provided by 
	buildMnisUrl. The output parameters specify what additional information 
	about MPs the API should return. The API only allows up to three 
	output parameters per request.
	"""

	# Set http request parameters 
	headers = {'content-type': 'application/json'}
	url = buildMnisUrl(urlParameters, outputParameters)

	# Make request
	response = requests.get(url, headers=headers)
	
	# Get response text
	responseText = response.text
	
	# Parse JSON (cutting off the byte order marker at the start)
	members = json.loads(responseText[1:])
	members = members['Members']['Member']

	return members


# Functions that retrieve and process data for members ----------------------

def getIdForMember(member):

	""" 
	Returns the member's unique id as a string.
	"""

	return member['@Member_Id']


def getListNameForMember(member):

	""" 
	Returns the member's list namex, which has the format:
	"surname, (title) firstname", with title being optional.
	"""

	return member['ListAs']


def getGenderForMember(member):

	""" Returns the member's gender as a string: 'F' or 'M'. """

	return member['Gender']


def getDateOfBirthForMember(member):

	""" Returns the member's date of birth as a datetime.date. """

	if isinstance(member['DateOfBirth'], str):
		
		return convertMnisDatetime(member['DateOfBirth'])

	else:

		return ''


def getConstituencyForMember(member, onDate):

	"""
	Returns a member's constituency on a given date. If the member was not an 
	MP on the given date the function returns a string indicating the member 
	was not serving on the specified date. The member must be a member object
	returned by one of the getCommonsMembers functions, and must contain data
	on constituency memberships which is requested with the output parameter 
	for 'Constituencies'. This parameter is one of the defaults for the 
	getCommonsMembers functions. The onDate should be a datetime.date.
	"""

	# Get the data on historic constituency memberships
	constituencyMembership = member['Constituencies']['Constituency']
	constituencyName = 'Not serving on {0}'.format(onDate)

	# Constituency memberships are in a list if there is more than one
	if isinstance(constituencyMembership, list):

		for membership in constituencyMembership:

			if isDateInMembership(membership, onDate):

				constituencyName = membership['Name']
				break

	# Otherwise the membership is accessed directly
	else:
		
		membership = constituencyMembership

		if isDateInMembership(membership, onDate):
			constituencyName = membership['Name']

	return constituencyName


def getPartyForMember(member, onDate):

	"""
	Returns a member's party on a given date. If the member was not an MP on
	the given date the function returns a string indicating the member was not 
	serving on the specified date. The member must be a member object returned 
	by one of the getCommonsMembers functions, and must contain data on party 
	memberships which is requested with the output parameter for 'Parties'. 
	This parameter is one of the defaults for the getCommonsMembers functions. 
	The onDate should be a datetime.date.
	"""

	# Get the data on historic party memberships
	partyMembership = member['Parties']['Party']
	partyName = 'Not serving on {0}'.format(onDate)

	# Party memberships are in a list if there is more than one
	if isinstance(partyMembership, list):

		for membership in partyMembership:

			if isDateInMembership(membership, onDate):

				partyName = membership['Name']
				break

	# Otherwise the membership is accessed directly
	else:
		
		membership = partyMembership

		if isDateInMembership(membership, onDate):
			partyName = membership['Name']

	return partyName


def isDateInMembership(membership, onDate):

	""" Checks whether a date falls within a given membership. """

	# Set the start date to the membership start date
	startDate = convertMnisDatetime(membership['StartDate'])

	# Assume the membership is open and set the end date to today's date
	endDate = datetime.date.today()

	# If the membership is closed set the end date to the membership end date
	if isinstance(membership['EndDate'], str):
		endDate = convertMnisDatetime(membership['EndDate'])	

	return isDateInRange(onDate, startDate, endDate)


def getServiceDataForMember(member, onDate):

	"""
	Returns the date a member first became an MP and the total number of days 
	a member has served up to the given date, excluding periods when the House
	is in dissolution. The member must be a	member object returned by one of 
	the getCommonsMembers functions, and must contain data on House memberships 
	which is requested with the output parameter for 'HouseMemberships'. This 
	parameter is one of the defaults for the getCommonsMembers functions. The 
	onDate should be a datetime.date.
	"""

	# Get Commons memberships to calculate length of service in days
	houseMembership = member['HouseMemberships']['HouseMembership']
	serviceDays = 0
	startDates = []

	# House memberships are in a list if there is more than one
	if isinstance(houseMembership, list):

		for membership in houseMembership:

			if membership['House'] == 'Commons':

				daysService = getMembershipDays(membership, onDate)
				serviceDays += daysService
				startDates.append(convertMnisDatetime(membership['StartDate']))

	# Otherwise the membership is accessed directly
	else:

		if houseMembership['House'] == 'Commons':

			membership = houseMembership
			daysService = getMembershipDays(membership, onDate)
			serviceDays += daysService
			startDates.append(convertMnisDatetime(membership['StartDate']))

	startDates.sort()
	startDate = startDates[0]

	return startDate, serviceDays


def getMembershipDays(membership, onDate, houseDates=housedata.dates):

	"""
	Returns the number of days service in a membership up to the given date,
	excluding periods when the House is in dissolution. The onDate is a
	datetime.date.
	"""

	# Set the start date to the membership start date
	startDate = convertMnisDatetime(membership['StartDate'])

	# Assume the membership is open and set the end date to the onDate
	endDate = onDate

	# If the membership is closed set the end date to the membership end date
	if isinstance(membership['EndDate'], str):
		endDate = convertMnisDatetime(membership['EndDate'])

	# If the membership starts on or after the onDate return zero days
	if startDate >= onDate: return 0

	# If the membership ends after the onDate set it to the onDate
	if endDate > onDate: endDate = onDate

	# If membership ends before it starts raise an error
	if startDate > endDate:
		raise MembershipError("startDate after endDate in getMembershipDays")

	# Set initial service length as the number of days from start to end
	serviceDelta = endDate - startDate
	serviceDays = serviceDelta.days

	# Then remove dissolution periods that fall within the membership
	elections = sorted(houseDates.keys())

	for e in elections:

		election = houseDates[e]['election']
		dissolution = houseDates[e]['dissolution']

		if dissolution >= startDate:

			if dissolution < endDate:

				if election <= endDate:

					# remove entire dissolution and continue
					delta = election - dissolution
					serviceDays -= delta.days
					continue

				else:

					# remove endDate - dissolution
					delta = endDate - dissolution
					serviceDays -= delta.days
					continue
			else:

				# dissolution is after membership so do nothing
				pass

		elif dissolution < startDate:

			if election > startDate:

				if election <= endDate:

					# remove election - startDate
					delta = election - startDate
					serviceDays -= delta.days
					continue

				else:

					# remove whole membership and continue
					delta = endDate - startDate
					serviceDays -= delta.days
					continue

			else:

					# election is before membership so do nothing
					pass

		else:

			# This should not be able to happen
			raise MembershipError("Shouldn't happen in getMembershipDays")

	return serviceDays


# Functions for summarising data on a list of members ------------------------

def getSummaryDataForMembers(members, onDate):

	"""
	Takes a list of members, produces a set of summary data for each member 
	in the list, and returns it as a list of dictionaries. The data returned 
	for a member is determined by the onDate, which should be a datetime.date.
	The data downloaded for each member is:

	- member id
	- listed name
	- constituency
	- party
	- date of birth
	- gender
	- date first became an mp
	- number of days service

	In order to produce this data the members passed to the function must
	contain outputs that are requested with output parameters for:
	
	- Constituencies
	- Parties
	- HouseMemberships

	These are the default output parameters for getCommonsMembers functions.
	"""

	summary = []

	for member in members:

		memberData = {}
		memberData['member_id']	= getIdForMember(member)	
		memberData['list_name'] = getListNameForMember(member)
		memberData['constituency'] = getConstituencyForMember(member, onDate)
		memberData['party'] = getPartyForMember(member, onDate)
		memberData['date_of_birth'] = getDateOfBirthForMember(member)
		memberData['gender'] = getGenderForMember(member)
		memberData['first_start_date'], memberData['days_service'] = \
			getServiceDataForMember(member, onDate)
		summary.append(memberData)

	return summary


def saveSummaryDataForMembers(summaryData, csvName):

	"""
	Takes a list of summary data for each member from getSummaryDataForMembers
	and writes the data to file as a csv with the given filename. The data 
	downloaded for each member is:

	- member id
	- listed name
	- constituency
	- party
	- date of birth
	- gender
	- date first became an mp
	- number of days service

	In order to produce this data the members passed to the function must 
	contain outputs that are requested with output parameters for: 
	
	- Constituencies
	- Parties
	- HouseMemberships

	These are the default output parameters for getCommonsMembers functions.
	"""

	with open(csvName, 'w') as csvFile:
		
		fieldnames = ['member_id', 'list_name', 'constituency', 'party', \
			'date_of_birth', 'gender', 'first_start_date', 'days_service']

		writer = csv.DictWriter(csvFile, fieldnames=fieldnames)
		writer.writeheader()
		
		for summary in summaryData:
			writer.writerow(summary)


def downloadMembers(onDate, csvName):

	"""
	Downloads summary data on members serving in the House of Commons on a 
	given date and saves it as a csv. The onDate should be a datetime.date.
	The csvName is the file into which the data will be saved. The data 
	downloaded for each member is:

	- member id
	- listed name
	- constituency
	- party
	- date of birth
	- gender
	- date first became an mp
	- number of days service

	The data shows information about each members on the given date, so the
	constituency, party, and number of days service is as at the onDate. 
	"""

	members = getCommonsMembersOn(onDate)
	summaryData = getSummaryDataForMembers(members, onDate)
	saveSummaryDataForMembers(summaryData, csvName)


# Utility functions ----------------------------------------------------------

def convertMnisDatetime(mnisDatetime):

	"""
	Takes a string representing a datetime in MNIS data and returns it
	as a datetime.date.
	"""

	mnisDate = mnisDatetime[:10]
	convertedDate = datetime.datetime.strptime(mnisDate, '%Y-%m-%d').date()
	return convertedDate


def isDateInRange(onDate, startDate, endDate):

	"""
	Checks whether a onDate falls between startDate an endDate. The test is 
	inclusive: it passes if onDate is equal to startDate or endDate. All dates
	are datetime.dates. An error is raised if startDate is later than endDate.
	"""

	if startDate > endDate:
		raise MembershipError("startDate later than endDate in isDateInRange")

	if onDate >= startDate and onDate <= endDate:
		return True
	else:
		return False

