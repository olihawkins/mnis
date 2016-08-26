# -*- coding: utf-8 -*-
# mnis unit testing module

import unittest
import datetime
import requests
import json
import os
import csv
import mnis.mnislib as mnislib

print("Running tests: Note that the tests require two downloads and can take up to 20 seconds ...")

def downloadMembersForTesting():

	"""Downloads data using a fixed URL for testing against library output."""

	# Set http request parameters for members at GE2015 
	headers = {'content-type': 'application/json'}
	url = 'http://data.parliament.uk/membersdataplatform/' \
		'services/mnis/members/query/House=Commons|Membership=all|' \
		'commonsmemberbetween=2015-05-07and2015-05-07/Constituencies|' \
		'Parties|HouseMemberships'

	# Make request
	response = requests.get(url, headers=headers)
	
	# Get response text
	responseText = response.text
	
	# Parse JSON (cutting off the byte order marker at the start)
	members = json.loads(responseText[1:])
	members = members['Members']['Member']

	# Sort members to ensure they appear in list name alphabetical order
	members.sort(key=lambda member: member['ListAs'])

	return members


# A global module variable used to store downloaded data on members. This data 
# is used for testing functions that work with downloaded data.
correctMembers = downloadMembersForTesting() 


def mockGetCommonsMembers(urlParameters, outputParameters):

	"""
	Mocks getCommonsMembers() and returns the parameters it uses to request 
	data from the MNIS API. This mock is used to test all functions that get 
	Commons members that wrap getCommonsMembers() itself. It simply checks 
	that they construct and pass on the correct parameters given their inputs.
	"""

	return urlParameters, outputParameters


class testGetCurrentCommonsMembers(unittest.TestCase):

	"""
	Tests getCurrentCommonsMembers by mocking getCommonsMembers
	and checking that the parameters passed to it are correct.
	"""

	def setUp(self):

		self.realGetCommonsMembers = mnislib.getCommonsMembers
		mnislib.getCommonsMembers = mockGetCommonsMembers

	def tearDown(self):

		mnislib.getCommonsMembers = self.realGetCommonsMembers

	def testGetCurrentCommonsMembers(self):

		d = datetime.date.today()
		ds = '{0}-{1}-{2}'.format(d.year, d.month, d.day)
		urlParameters = 'commonsmemberbetween={0}and{1}'.format(ds, ds)
		outputParameters = ['Constituencies', 'Parties', 'HouseMemberships']

		# Test with the default output parameters
		up, op = mnislib.getCurrentCommonsMembers()
		self.assertEqual(up, urlParameters)
		self.assertEqual(op, outputParameters)

		# Test with user defined output parameters
		up, op = mnislib.getCurrentCommonsMembers(['Parameter'])
		self.assertEqual(up, urlParameters)
		self.assertEqual(op, ['Parameter'])


class testGetCommonsMembersOn(unittest.TestCase):

	"""
	Tests getCommonsMembersOn by mocking getCommonsMembers
	and checking that the parameters passed to it are correct.
	"""

	def setUp(self):

		self.realGetCommonsMembers = mnislib.getCommonsMembers
		mnislib.getCommonsMembers = mockGetCommonsMembers


	def tearDown(self):

		mnislib.getCommonsMembers = self.realGetCommonsMembers


	def testGetCommonsMembersOn(self):

		d = datetime.date.today()
		ds = '{0}-{1}-{2}'.format(d.year, d.month, d.day)
		urlParameters = 'commonsmemberbetween={0}and{1}'.format(ds, ds)
		outputParameters = ['Constituencies', 'Parties', 'HouseMemberships']

		# Test with the default output parameters
		up, op = mnislib.getCommonsMembersOn(d)
		self.assertEqual(up, urlParameters)
		self.assertEqual(op, outputParameters)

		# Test with user defined output parameters
		up, op = mnislib.getCommonsMembersOn(d, ['Parameter'])
		self.assertEqual(up, urlParameters)
		self.assertEqual(op, ['Parameter'])


class testGetCommonsMembersBetween(unittest.TestCase):

	"""
	Tests getCommonsMembersBetween by mocking getCommonsMembers
	and checking that the parameters passed to it are correct.
	"""

	def setUp(self):

		self.realGetCommonsMembers = mnislib.getCommonsMembers
		mnislib.getCommonsMembers = mockGetCommonsMembers


	def tearDown(self):

		mnislib.getCommonsMembers = self.realGetCommonsMembers


	def testGetCommonsMembersBetween(self):

		ed = datetime.date.today()
		eds = '{0}-{1}-{2}'.format(ed.year, ed.month, ed.day)
		sd = ed - datetime.timedelta(days=1)
		sds = '{0}-{1}-{2}'.format(sd.year, sd.month, sd.day)
		urlParameters = 'commonsmemberbetween={0}and{1}'.format(sds, eds)
		outputParameters = ['Constituencies', 'Parties', 'HouseMemberships']
		
		# Test with the default output parameters
		up, op = mnislib.getCommonsMembersBetween(sd, ed)
		self.assertEqual(up, urlParameters)
		self.assertEqual(op, outputParameters)

		# Test with user defined output parameters
		up, op = mnislib.getCommonsMembersBetween(sd, ed, ['Parameter'])
		self.assertEqual(up, urlParameters)
		self.assertEqual(op, ['Parameter'])


class testGetCommonsMembersAtElection(unittest.TestCase):

	"""
	Tests getCommonsMembersAtElection by mocking getCommonsMembers
	and checking that the parameters passed to it are correct.
	"""

	def setUp(self):

		self.realGetCommonsMembers = mnislib.getCommonsMembers
		mnislib.getCommonsMembers = mockGetCommonsMembers


	def tearDown(self):

		mnislib.getCommonsMembers = self.realGetCommonsMembers


	def testGetCommonsMembersAtElection(self):

		electionIds = [ \
			'1983', '1987', '1992', '1997', '2001', '2005', '2010', '2015']
		
		outputParameters = ['Constituencies', 'Parties', 'HouseMemberships']

		for electionId in electionIds:

			urlParameters = 'returnedatelection={0}' \
				'%20General%20Election'.format(electionId)

			# Test with the default output parameters
			up, op = mnislib.getCommonsMembersAtElection(electionId)
			self.assertEqual(up, urlParameters)
			self.assertEqual(op, outputParameters)

			# Test with user defined output parameters
			up, op = mnislib.getCommonsMembersAtElection( \
				electionId, ['Parameter'])
			self.assertEqual(up, urlParameters)
			self.assertEqual(op, ['Parameter'])


	def testCommonsMembersAtElectionFails(self):

		self.assertRaises(mnislib.ElectionIdError, \
			mnislib.getCommonsMembersAtElection, '1979')


class testBuildMnisUrl(unittest.TestCase):

	"""
	Tests buildMnisUrl and checks it buildMnisUrl the correct MNIS URL for 
	various combinations of parameters. The parameters are based on those 
	used by the various functions that get Commons members.
	"""

	def testBuildMnisUrlCommonsMemberBetween(self):

		# Test commonsmemberbetween url parameter
		urlParameters = 'commonsmemberbetween=2010-05-06and2015-05-07'
		outputParameters = ['ParameterA', 'ParameterB', 'ParameterC']
		
		correctUrl = 'http://data.parliament.uk/membersdataplatform/' \
			'services/mnis/members/query/House=Commons|Membership=all|' \
			'commonsmemberbetween=2010-05-06and2015-05-07/ParameterA|' \
			'ParameterB|ParameterC'

		returnedUrl = mnislib.buildMnisUrl(urlParameters, outputParameters)
		self.assertEqual(returnedUrl, correctUrl)


	def testBuildMnisUrlReturnedAtElection(self):

		# Test returnedatelection url parameter
		urlParameters = 'returnedatelection=2001%20General%20Election'
		outputParameters = ['ParameterA', 'ParameterB', 'ParameterC']
		
		correctUrl = 'http://data.parliament.uk/membersdataplatform/' \
			'services/mnis/members/query/House=Commons|Membership=all|' \
			'returnedatelection=2001%20General%20Election/ParameterA|' \
			'ParameterB|ParameterC'

		returnedUrl = mnislib.buildMnisUrl(urlParameters, outputParameters)
		self.assertEqual(returnedUrl, correctUrl)


	def testBuildMnisUrlFails(self):

		# Test buildMnisUrl fails with more than three output parameters
		self.assertRaises(mnislib.ParameterError, mnislib.buildMnisUrl, '', \
			['ParameterA', 'ParameterB', 'ParameterC', 'ParameterD'])


class testGetCommonsMembers(unittest.TestCase):

	"""
	Tests getCommonsMebers to check it properly downloads data from the MNIS
	API. The returned members are stored in a global variable and are used
	in subsequent tests to check functions which handle the returned data.
	"""

	def testGetCommonsMembers(self):
		
		# Get Commons members at GE2015		
		members = mnislib.getCommonsMembers( \
			'commonsmemberbetween=2015-05-07and2015-05-07', \
			['Constituencies', 'Parties', 'HouseMemberships'])

		# Sort members to ensure they appear in list name alphabetical order
		members.sort(key=lambda member: member['ListAs'])

		# Test the downloaded data is correct
		self.assertEqual(members, correctMembers)


class testGetIdForMember(unittest.TestCase):

	"""Tests getIdForMember and checks it returns the correct id."""

	def testGetIdForMember(self):

		# Check first member listed alphabetically: Diane Abbott
		g = mnislib.getIdForMember(correctMembers[0])
		self.assertEqual(g, '172')

		# Check last member listed alphabetically: Daniel Zeichner
		g = mnislib.getIdForMember(correctMembers[649])
		self.assertEqual(g, '4382')


class testGetListNameForMember(unittest.TestCase):

	"""Tests getListNameForMember and checks it returns the correct name."""

	def testGetListNameForMember(self):

		# Check first member listed alphabetically: Diane Abbott
		ln = mnislib.getListNameForMember(correctMembers[0])
		self.assertEqual(ln, 'Abbott, Ms Diane')

		# Check last member listed alphabetically: Daniel Zeichner
		ln = mnislib.getListNameForMember(correctMembers[649])
		self.assertEqual(ln, 'Zeichner, Daniel')


class testGetGenderForMember(unittest.TestCase):

	"""Tests getGenderForMember and checks it returns the correct gender."""

	def testGetGenderForMember(self):

		# Check first member listed alphabetically: Diane Abbott
		g = mnislib.getGenderForMember(correctMembers[0])
		self.assertEqual(g, 'F')

		# Check last member listed alphabetically: Daniel Zeichner
		g = mnislib.getGenderForMember(correctMembers[649])
		self.assertEqual(g, 'M')


class testGetDateOfBirthForMember(unittest.TestCase):

	"""Tests getDateOfBirthForMember and checks it returns the correct DoB."""

	def testGetDateOfBirthForMember(self):

		# Check first member listed alphabetically: Diane Abbott
		dob = mnislib.getDateOfBirthForMember(correctMembers[0])
		d = datetime.date(1953, 9, 27)
		self.assertEqual(dob, d)

		# Check last member listed alphabetically: Daniel Zeichner
		dob = mnislib.getDateOfBirthForMember(correctMembers[649])
		d = datetime.date(1956, 11, 9)
		self.assertEqual(dob, d)


class testGetConstituencyForMember(unittest.TestCase):

	"""Tests getConstituencyForMember and checks it returns the correct one."""

	def testGetConstituencyForMember(self):

		# Set onDate to GE2015 for the latest constituency in the test data
		d = datetime.date(2015, 5, 7)

		# Check first member listed alphabetically: Diane Abbott
		con = mnislib.getConstituencyForMember(correctMembers[0], d)
		self.assertEqual(con, 'Hackney North and Stoke Newington')

		# Check last member listed alphabetically: Daniel Zeichner
		con = mnislib.getConstituencyForMember(correctMembers[649], d)
		self.assertEqual(con, 'Cambridge')

		# Check Boris Johnson for constituency as at GE2015
		con = mnislib.getConstituencyForMember(correctMembers[319], d)
		self.assertEqual(con, 'Uxbridge and South Ruislip')

		# Check Boris Johnson for constituency as at GE2001
		d = datetime.date(2001, 6, 7)
		con = mnislib.getConstituencyForMember(correctMembers[319], d)
		self.assertEqual(con, 'Henley')


class testGetPartyForMember(unittest.TestCase):

	"""Tests getPartyForMember and checks it returns the correct one."""

	def testGetPartyForMember(self):

		# Set onDate to GE2015 for the latest party in the test data
		d = datetime.date(2015, 5, 7)

		# Check first member listed alphabetically: Diane Abbott
		p = mnislib.getPartyForMember(correctMembers[0], d)
		self.assertEqual(p, 'Labour')

		# Check last member listed alphabetically: Daniel Zeichner
		p = mnislib.getPartyForMember(correctMembers[649], d)
		self.assertEqual(p, 'Labour')

		# Check Douglas Carswell for party as at GE2015
		p = mnislib.getPartyForMember(correctMembers[91], d)
		self.assertEqual(p, 'UK Independence Party')

		# Check Douglas Carswell for party as at GE2010
		d = datetime.date(2010, 5, 6)
		p = mnislib.getPartyForMember(correctMembers[91], d)
		self.assertEqual(p, 'Conservative')


class testIsDateInMembership(unittest.TestCase):

	"""Tests isDateInMembership and checks it returns the correct booleans."""

	def testOpenMembership(self):

		# Mock open membership
		openMembershipJson = '{"EndDate": {"@xmlns:xsi": ' + \
			'"http://www.w3.org/2001/XMLSchema-instance", ' + \
			'"@xsi:nil": "true"}, "StartDate": "2015-05-07T00:00:00"}'

		openMembership = json.loads(openMembershipJson)

		# Check date at start of membership
		self.assertTrue(mnislib.isDateInMembership( \
			openMembership, datetime.date(2015, 5, 7)))

		# Check date inside membership
		self.assertTrue(mnislib.isDateInMembership( \
			openMembership, datetime.date(2016, 1, 1)))

		# Check current date: should be true
		self.assertTrue(mnislib.isDateInMembership( \
			openMembership, datetime.date.today()))

		# Check date before membership
		self.assertFalse(mnislib.isDateInMembership( \
			openMembership, datetime.date(2015, 5, 6)))

		# Check date after membership
		self.assertFalse(mnislib.isDateInMembership( \
			openMembership, datetime.date(2017, 1, 1)))


	def testClosedMembership(self):

		# Mock closed membership
		closedMembershipJson = '{"EndDate": "2015-03-30T00:00:00", ' + \
			'"StartDate": "2010-05-06T00:00:00"}'

		closedMembership = json.loads(closedMembershipJson)

		# Check date at start of membership
		self.assertTrue(mnislib.isDateInMembership( \
			closedMembership, datetime.date(2010, 5, 6)))

		# Check date inside membership
		self.assertTrue(mnislib.isDateInMembership( \
			closedMembership, datetime.date(2013, 1, 1)))

		# Check date at end of membership
		self.assertTrue(mnislib.isDateInMembership( \
			closedMembership, datetime.date(2015, 3, 30)))

		# Check date before membership
		self.assertFalse(mnislib.isDateInMembership( \
			closedMembership, datetime.date(2010, 5, 5)))

		# Check date after membership
		self.assertFalse(mnislib.isDateInMembership( \
			closedMembership, datetime.date(2015, 3, 31)))


class testGetServiceDataForMember(unittest.TestCase):

	"""Tests getServiceDataForMember and checks it returns correct data."""

	def testGetServiceDataForMember(self):

		# Set onDate to GE2015 to match the test data
		d = datetime.date(2015, 5, 7)

		# Check first member listed alphabetically: Diane Abbott
		sd = mnislib.getServiceDataForMember(correctMembers[0], d)
		self.assertEqual(sd, (datetime.date(1987, 6, 11), 10035))

		# Check last member listed alphabetically: Daniel Zeichner
		sd = mnislib.getServiceDataForMember(correctMembers[649], d)
		self.assertEqual(sd, (datetime.date(2015, 5, 7), 0))

		# Check Boris Johnson as member with interrupted membership
		sd = mnislib.getServiceDataForMember(correctMembers[319], d)
		self.assertEqual(sd, (datetime.date(2001, 6, 7), 2530))


class testGetMembershipDays(unittest.TestCase):

	"""Tests getMembershipDays and checks it returns correct counts."""

	def testGetMembershipDays(self):

		# Mock a membership that spans a number of elections
		membershipJson = '{"EndDate": "2015-03-30T00:00:00", ' + \
			'"StartDate": "1987-06-11T00:00:00"}'

		membership = json.loads(membershipJson)

		# Test with an onDate after the end of the membership
		d = datetime.date.today()
		self.assertEqual(mnislib.getMembershipDays(membership, d), 10035)

		# Test with an onDate halfway through the membership
		d = datetime.date(1997, 4, 8)
		self.assertEqual(mnislib.getMembershipDays(membership, d), 3565)	

		# Test with an onDate before the membership
		d = datetime.date(1987, 6, 10)
		self.assertEqual(mnislib.getMembershipDays(membership, d), 0)


	def testGetMembershipDaysFails(self):

		# Mock a membership with invalid data
		membershipJson = '{"EndDate": "2015-03-30T00:00:00", ' + \
			'"StartDate": "2015-05-07T00:00:00"}'

		membership = json.loads(membershipJson)

		# Test with an onDate after the end of the membership
		d = datetime.date.today()

		self.assertRaises(mnislib.MembershipError, \
			mnislib.getMembershipDays, membership, d)


class testGetSummaryDataForMembers(unittest.TestCase):

	"""Tests getSummaryDataForMembers and checks it returns correct data."""

	def testGetSummaryDataForMembers(self):

		# Set onDate to GE2015 to match the test data
		d = datetime.date(2015, 5, 7)

		# Get summary data
		sd = mnislib.getSummaryDataForMembers(correctMembers, d)

		# Check first member listed alphabetically: Diane Abbott
		self.assertEqual(sd[0]['member_id'], '172')
		self.assertEqual(sd[0]['list_name'], 'Abbott, Ms Diane')
		self.assertEqual(sd[0]['constituency'], \
			'Hackney North and Stoke Newington')
		self.assertEqual(sd[0]['party'], 'Labour')
		self.assertEqual(sd[0]['date_of_birth'], datetime.date(1953, 9, 27))
		self.assertEqual(sd[0]['gender'], 'F')
		self.assertEqual(sd[0]['first_start_date'], datetime.date(1987, 6, 11))
		self.assertEqual(sd[0]['days_service'], 10035)

		# Check last member listed alphabetically: Daniel Zeichner
		self.assertEqual(sd[649]['member_id'], '4382')
		self.assertEqual(sd[649]['list_name'], 'Zeichner, Daniel')
		self.assertEqual(sd[649]['constituency'], 'Cambridge')
		self.assertEqual(sd[649]['party'], 'Labour')
		self.assertEqual(sd[649]['date_of_birth'], datetime.date(1956, 11, 9))
		self.assertEqual(sd[649]['gender'], 'M')
		self.assertEqual(sd[649]['first_start_date'], datetime.date(2015, 5, 7))
		self.assertEqual(sd[649]['days_service'], 0)


class testSaveSummaryDataForMembers(unittest.TestCase):

	"""Tests saveSummaryDataForMembers and checks it writes correct data."""

	def setUp(self):

		# Set filename for testing
		self.filename = "unittest.csv"

		# Set onDate to GE2015 to match the test data
		d = datetime.date(2015, 5, 7)

		# getthe summaryData for the members
		sd = mnislib.getSummaryDataForMembers(correctMembers, d)

		# Write member data to disk as csv
		mnislib.saveSummaryDataForMembers(sd, self.filename)

	def tearDown(self):

		if os.path.exists(self.filename):
			os.remove(self.filename)

	def testSaveSummaryDataForMembers(self):

		# Test if the file has been written to disk
		self.assertTrue(os.path.exists(self.filename))

		# Try reading the file in as a csv
		with open(self.filename) as csvFile:
			reader = csv.reader(csvFile)
			rows = list(reader)

			header = [ \
				'member_id', \
				'list_name', \
				'constituency', \
				'party', \
				'date_of_birth', \
				'gender', \
				'first_start_date', \
				'days_service'\
			]

			self.assertEqual(rows[0], header)

			firstMember = [ \
				'172', \
				'Abbott, Ms Diane', \
				'Hackney North and Stoke Newington', \
				'Labour', \
				'1953-09-27', \
				'F', \
				'1987-06-11', \
				'10035' \
			]

			self.assertEqual(rows[1], firstMember)

			lastMember = [ \
				'4382', \
				'Zeichner, Daniel', \
				'Cambridge', \
				'Labour', \
				'1956-11-09', \
				'M', \
				'2015-05-07', \
				'0' \
			]

			self.assertEqual(rows[650], lastMember)


class testDownloadMembers(unittest.TestCase):

	"""
	Tests downloadMembers and checks it writes correct data. 

	For now this test is empty as the function is a very simple wrapper around 
	getCommonsMembersOn(), getSummaryDataForMembers(), 
	and saveSummaryDataForMembers(), each of which are tested elsewhere. 
	Retesting the combined functionality here would only add another download 
	to the test suite and unduly increase the time it takes to run the tests. 
	If this function becomes more complex in future a test should be added.
	"""

	def testDownloadMembers(self):

		pass


class testConvertMnisDatetime(unittest.TestCase):

	"""Tests convertMnisDatetime and checks it converts dates correctly."""

	def testConvertMnisDatetime(self):

		exampleDatetimes = [ \
			'1992-04-09T00:00:00', \
			'1997-05-01T00:00:00', \
			'2001-06-07T00:00:00', \
			'2005-05-05T00:00:00', \
			'2010-05-06T00:00:00', \
			'2015-05-07T00:00:00', \
		]

		convertedDatetimes = [ \
			datetime.date(1992, 4, 9), \
			datetime.date(1997, 5, 1), \
			datetime.date(2001, 6, 7), \
			datetime.date(2005, 5, 5), \
			datetime.date(2010, 5, 6), \
			datetime.date(2015, 5, 7), \
		]

		for i in range(len(exampleDatetimes)):

			d = mnislib.convertMnisDatetime(exampleDatetimes[i])
			self.assertEqual(d, convertedDatetimes[i])


class testIsDateInRange(unittest.TestCase):

	"""Tests isDateInRange and checks it returns the correct boolean."""

	def testIsDateInRange(self):

		dates = [ \
			datetime.date(2015, 5, 6), \
			datetime.date(2015, 5, 7), \
			datetime.date(2015, 5, 8), \
		]

		# Test where onDate, startDate and endDate are equal
		self.assertTrue(mnislib.isDateInRange(dates[0], dates[0], dates[0]))

		# Test where onDate equals startDate, and endDate is later
		self.assertTrue(mnislib.isDateInRange(dates[0], dates[0], dates[1]))

		# Test where onDate equals endDate, and startDate is earlier
		self.assertTrue(mnislib.isDateInRange(dates[1], dates[0], dates[1]))

		# Test where onDate is after startDate and before endDate
		self.assertTrue(mnislib.isDateInRange(dates[1], dates[0], dates[2]))

		# Test where onDate is befpre startDate and endDate
		self.assertFalse(mnislib.isDateInRange(dates[0], dates[1], dates[2]))

		# Test where onDate is after startDate and endDate
		self.assertFalse(mnislib.isDateInRange(dates[2], dates[0], dates[1]))



if __name__ == '__main__':
	unittest.main()