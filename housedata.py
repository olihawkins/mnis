# -*- coding: utf-8 -*-
# mnis.housedata module

"""
Name: housedata.py
Author: Oliver Hawkins
About: This module provides data on the length of Parliaments and 
dissolution periods for use with the mnis package and mnislib module.
Dissolution dates can be found here:
https://goo.gl/o5xV7g

"""

import datetime

dates = {}

dates['1929'] = {
	'dissolution': datetime.date(1929, 5, 10), 
	'election': datetime.date(1929, 5, 30)
}

dates['1931'] = {
	'dissolution': datetime.date(1931, 10, 8), 
	'election': datetime.date(1931, 10, 27)
}

dates['1935'] = {
	'dissolution': datetime.date(1935, 10, 25), 
	'election': datetime.date(1935, 11, 14)
}

dates['1945'] = {
	'dissolution': datetime.date(1945, 6, 15), 
	'election': datetime.date(1945, 7, 5)
}

dates['1950'] = {
	'dissolution': datetime.date(1950, 2, 3), 
	'election': datetime.date(1950, 2, 23)
}

dates['1951'] = {
	'dissolution': datetime.date(1951, 10, 5), 
	'election': datetime.date(1951, 10, 25)
}

dates['1955'] = {
	'dissolution': datetime.date(1955, 5, 6), 
	'election': datetime.date(1955, 5, 26)
}

dates['1959'] = {
	'dissolution': datetime.date(1959, 9, 18), 
	'election': datetime.date(1959, 10, 8)
}

dates['1964'] = {
	'dissolution': datetime.date(1964, 9, 25), 
	'election': datetime.date(1964, 10, 15)
}

dates['1966'] = {
	'dissolution': datetime.date(1966, 3, 10), 
	'election': datetime.date(1966, 3, 31)
}

dates['1970'] = {
	'dissolution': datetime.date(1970, 5, 29), 
	'election': datetime.date(1970, 6, 18)
}

dates['1974 (Feb)'] = {
	'dissolution': datetime.date(1974, 2, 8), 
	'election': datetime.date(1974, 2, 28)
}

dates['1974 (Oct)'] = {
	'dissolution': datetime.date(1974, 9, 20), 
	'election': datetime.date(1974, 10, 10)
}

dates['1979'] = {
	'dissolution': datetime.date(1979, 4, 7), 
	'election': datetime.date(1979, 5, 3)
}

dates['1983'] = {
	'dissolution': datetime.date(1983, 5, 13), 
	'election': datetime.date(1983, 6, 9)
}

dates['1987'] = {
	'dissolution': datetime.date(1987, 5, 18), 
	'election': datetime.date(1987, 6, 11)
}

dates['1992'] = {
	'dissolution': datetime.date(1992, 3, 16), 
	'election': datetime.date(1992, 4, 9)
}

dates['1997'] = {
	'dissolution': datetime.date(1997, 4, 8), 
	'election': datetime.date(1997, 5, 1)
}

dates['2001'] = {
	'dissolution': datetime.date(2001, 5, 14), 
	'election': datetime.date(2001, 6, 7)
}

dates['2005'] = {
	'dissolution': datetime.date(2005, 4, 11), 
	'election': datetime.date(2005, 5, 5)
}

dates['2010'] = {
	'dissolution': datetime.date(2010, 4, 12), 
	'election': datetime.date(2010, 5, 6)
}

dates['2015'] = {
	'dissolution': datetime.date(2015, 3, 30), 
	'election': datetime.date(2015, 5, 7)
}