# mnis
mnis is a small Python library that makes it easy to download data on UK Members of Parliament from the [Members Names Information Service][mnisapi].

The MNIS API is the public interface to the UK Parliament's Members Names database, a comprehensive database of all MPs elected to Parliament since 1983. The API is fexible and powerful, but not very easy to use. The mnis library is a toolkit that makes it easier to download and manipulate useful data from the API.

At the most basic level, mnis allows you to download key data on all MPs who were serving on a given date to a csv with a single line of code. It is just as easy to obtain the same summary data on MPs as a list of Python dictionaries, or alternatively to get the full data for each MP returned by the API. The library allows you to customise the parameters sent to the API through a simple interface and makes possible quite sophisticated analysis of MPs careers.

The key summary data on MPs that the library's higher level functions provide by default are:

  - Name
  - Constituency
  - Party
  - Gender
  - Date of Birth
  - Date became an MP
  - Number of days service (excluding dissolution periods)

Further data can be easily requested from the API through the mnis library's core functions for retrieving data.

The mnis library is unofficial. I use it to help with my work and it is shared "as is" in case it is useful to others.

### Python requirements
The library is written in Python 3 and has been tested on Python 3.4 and 3.5. It requires the [requests][requests] package.

### Installation
The easiest way to install the package is with pip. 
```sh
pip install mnis
``` 
Alternatively install the package by cloning the repository into a folder called `mnis`, making sure its parent directory is in the PYTHONPATH.

### Tests
Run `python test_mnis.py` to run the unit tests.

### Downloading data on MPs
To download summary data on all MPs serving on a given date to a csv, pass a `datetime.date` object to the downloadMembers function. The constituency, party, and number of days served shown for each MP is as at the given date. 
```python
import mnis
import datetime

# Download data on current MPs into members.csv
mnis.downloadMembers(datetime.date.today(), "members.csv")

# Download data on MPs serving on a given date (1 Aug 2016) into members.csv
mnis.downloadMembers(datetime.date(2016, 8, 1), "members.csv")
```
To do exactly the same thing step by step, giving you access to all the available data at each stage, do the following.
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
saveSummaryDataForMembers(sd, "members.csv")
```
Note that a date is passed to both the functions for getting member data - in this case getCommonsMembersOn - and to the functions for extracting summary data - getSummaryDataForMembers and saveSummaryDataForMembers. This is because the functions that extract summary data for each MP from their full record need to return the party, constituency, and number of days served *for a particular date*. 

In most cases the date used to get members will be the same as the date used to extract summary data about those members, **but it doesn't have to be**. This means you can get all MPs serving on a particular date, or between particular dates, and then find out which parties and constituencies they were representing on a diffrent date. If an MP was not serving on the date used for summarising the data, the summary data will report that they weren't serving on that date. This means you can do things like find out which of a group of MPs serving on one date were still serving at a later date.

To give an example, the following code gets all MPs who served during the 2010-15 Parliament, including those elected at by-elections. If the date passed to getSummaryDataForMembers is the same as the start of the Parliament then Douglas Carswell MP is shown as a members of the Conservative Party. But if the date passed to getSummaryDataForMembers is the same as at the end of the Parliament, his party is the UK Independence Party.
```python
import mnis
import datetime

# Create dates for the start and end of the 2010-15 Parliament
startDate = datetime.date(2010, 5, 7)
endDate = datetime.date(2015, 3, 30)

# Download the full data for MPs serving between the given dates as a list
members = mnis.getCommonsMembersBetween(startDate, endDate)

# Get the summary data for these members on the startDate:
sd = mnis.getSummaryDataForMembers(members, startDate)

# Douglas Carswell's party is "Conservative"
print(sd[103]['list_name'], '-', sd[103]['party'])

# Get the summary data for these members on the endDate:
sd = mnis.getSummaryDataForMembers(members, endDate)

# Douglas Carswell's party is "UK Independence Party"
print(sd[103]['list_name'], '-', sd[103]['party'])
```
A deeper dive into the the library and the API will appear on my blog shortly, showing how to use the library to further customise API requests, and how to extend it to write your own data extraction functions. I will update this readme with the link as soon as it is posted.

[mnisapi]: <http://data.parliament.uk/membersdataplatform/memberquery.aspx>
[requests]: <http://docs.python-requests.org/en/master/>

