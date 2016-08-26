# mnis
mnis is a small Python library that makes it easy to download data on UK Members of Parliament from the [Members Names Information Service][mnisapi].

The MNIS API is the public interface to the UK Parliament's Members Names database, a comprehensive database of all MPs elected to Parliament since 1983. The API is flexible and powerful, but it's not very easy to use. The mnis library is a toolkit that makes it easier to download and manipulate useful data from the API.

At the most basic level, the mnis library allows you to download key data on all MPs who were serving on a given date to a csv with a single line of code. It makes it easy to obtain the same summary data for MPs as a list of Python dictionaries, or alternatively to get the full data for each MP returned by the API. The library allows you to customise the parameters sent to the API through a simple interface and makes possible quite sophisticated analysis of MPs' careers.

The library's summary functions provide the following data on MPs by default:

  - Member ID
  - Name
  - Constituency
  - Party
  - Date of Birth
  - Gender
  - Date first became an MP
  - Number of days service (excluding dissolution periods)

The mnis library is **unofficial**. It is shared "as is" in case it is useful.

### Python requirements
The library is written in Python 3 and has been tested on Python 3.4 and 3.5. It requires the [requests][requests] package, which pip will install automatically if it is not already present.

### Installation
The easiest way to install the package is with pip:
```sh
pip install mnis
``` 
Alternatively, install the package by cloning the repository into a folder called `mnis`, making sure its parent directory is in the PYTHONPATH.

### Tests
Run `python test_mnis.py` to run the unit tests.

### Downloading data on MPs
To download summary data on all MPs serving on a given date to a csv, pass a `datetime.date` object to the *downloadMembers* function. The constituency, party, and number of days served shown for each MP is as at the given date. 
```python
import mnis
import datetime

# Download data on current MPs into members.csv
mnis.downloadMembers(datetime.date.today(), 'members.csv')

# Download data on MPs serving on a given date (1 Aug 2016) into members.csv
mnis.downloadMembers(datetime.date(2016, 8, 1), 'members.csv')
```
To do exactly the same thing step by step, giving you access to all the available data at each stage, do the following:
```python
import mnis
import datetime

# Create a date for the analysis
d = datetime.date.today()

# Download the full data for MPs serving on the given date as a list
members = mnis.getCommonsMembersOn(d)

# Get the summary data for these members as a list
sd = mnis.getSummaryDataForMembers(members, d)

# Save the summary data into members.csv
mnis.saveSummaryDataForMembers(sd, 'members.csv')
```
Note that a date is passed both to functions for downloading member data (in this case *getCommonsMembersOn*) and to functions for extracting summary data (*getSummaryDataForMembers*). This is because the functions that extract summary data for each MP from their full record need to return the party, constituency, and number of days served for a particular date.

In many cases the date used to get members will be the same as the date used to extract summary data about those members, **but it doesn't have to be**. This means you can get all MPs serving on a particular date, or between particular dates, and then find out which parties and constituencies they were representing on a different date. If an MP was not serving on the date used for summarising the data, the summary data will report that they weren't serving on that date. This means you can do things like find out which of a group of MPs serving on one date were still serving at a later date.

To give an example, the following code gets all MPs who served during the 2010-15 Parliament, including those elected at by-elections. If the date passed to *getSummaryDataForMembers* is for the start of the Parliament, Douglas Carswell MP is shown as a member of the Conservative Party; but if the date passed to *getSummaryDataForMembers* is for the end of the Parliament, his party is shown as the UK Independence Party.
```python
import mnis
import datetime

# Create dates for the start and end of the 2010-15 Parliament
startDate = datetime.date(2010, 5, 7)
endDate = datetime.date(2015, 3, 30)

# Download the full data for MPs serving between the given dates as a list
members = mnis.getCommonsMembersBetween(startDate, endDate)

# Get the summary data for these members on the startDate
sd = mnis.getSummaryDataForMembers(members, startDate)

# Douglas Carswell's party is Conservative
print(sd[103]['list_name'], '-', sd[103]['party'])

# Get the summary data for these members on the endDate
sd = mnis.getSummaryDataForMembers(members, endDate)

# Douglas Carswell's party is UK Independence Party
print(sd[103]['list_name'], '-', sd[103]['party'])
```

### API gotchas

The Members Names database is an administrative system as well as a record of historical data, and there are some inconsistencies in recording practices to look out for. In particular, in some cases MPs are listed as serving up to the date of the general election at which they were defeated or stepped down, while in others they are listed as serving up to the date of dissolution before the general election at which they were defeated or stepped down. 

This does not affect the calculation of the number of days served by a member, which excludes any period of dissolution irrespective of how the memberships are recorded. However, it does affect the MPs returned by date-based API requests. 

For example, requesting all members serving on the date of the 2010 General Election with *getCommonsMembersOn* returns the 650 MPs elected on that date *and* the 225 MPs who were either defeated or stood down at that election. This is not the case for the 2015 General Election: a date-based request for members serving on the date of that election returns just those elected on that day.

There are two simple solutions to this problem. First, if you are only interested in MPs returned at a particular general election you can use the *getCommonsMembersAtElection* function, which uses a different API call and only returns those MPs elected on that date. The function takes the year of the general election as a string and will return records for any general election since 1983.

```python
members = mnis.getCommonsMembersAtElection('2010')
```

Alternatively, if you want to request MPs based on a date range starting at a general election, use the day *after* the general election as the start date. The membership hasn't changed between election day and the following day at any of the general elections since 1983, so requesting the MPs serving on the day following a general election is equivalent to asking for the MPs elected at that election. This is how the data was requested in the above example showing Douglas Carswell's change of party.

A less simple solution, which provides the most fine-grained control, is to request the full data for all members with a date-based request and then filter the list using the dates of their House memberships. In most cases this sort of approach is not necessary, but it is wise to check the data returned by the API before automating any analysis.

[mnisapi]: <http://data.parliament.uk/membersdataplatform/memberquery.aspx>
[requests]: <http://docs.python-requests.org/en/master/>

