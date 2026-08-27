"""Functions for extracting contact details for Lords"""

import datetime

from polars import DataFrame

from mnis.contacts import fetch_members_email_addresses
from mnis.contacts import fetch_members_fax_numbers
from mnis.contacts import fetch_members_facebook
from mnis.contacts import fetch_members_instagram
from mnis.contacts import fetch_members_office_addresses
from mnis.contacts import fetch_members_phone_numbers
from mnis.contacts import fetch_members_twitter
from mnis.contacts import fetch_members_websites
from mnis.lords import fetch_lords
from mnis.lords import fetch_lords_addresses

Date = str | datetime.date | None


def fetch_lords_office_addresses(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch office addresses for Lords.

    fetch_lords_office_addresses fetches data from the Members Names
    platform on office addresses for each Lord, with one row per
    combination of Lord and office address.

    The from_date and to_date arguments can be used to filter the Lords
    based on the dates of their Lords memberships. The on_date argument is
    a convenience that sets the from_date and to_date to the same given
    date. The on_date has priority: if the on_date is set, the from_date
    and to_date are ignored.

    The filtering is inclusive: a Lord is returned if any part of one of
    their Lords memberships falls within the period specified with the from
    and to dates.

    :param from_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the from_date.
    :param to_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the to_date.
    :param on_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the on_date.
    :return: A dataframe of known office addresses for each Lord, with one
        row per combination of Lord and office address.
    """
    return fetch_members_office_addresses(
        fetch_lords,
        fetch_lords_addresses,
        from_date=from_date,
        to_date=to_date,
        on_date=on_date)


def fetch_lords_email_addresses(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch email addresses for Lords.

    fetch_lords_email_addresses fetches data from the Members Names
    platform on email addresses for each Lord, with one row per combination
    of Lord and email address.

    The from_date and to_date arguments can be used to filter the Lords
    based on the dates of their Lords memberships. The on_date argument is
    a convenience that sets the from_date and to_date to the same given
    date. The on_date has priority: if the on_date is set, the from_date
    and to_date are ignored.

    The filtering is inclusive: a Lord is returned if any part of one of
    their Lords memberships falls within the period specified with the from
    and to dates.

    :param from_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the from_date.
    :param to_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the to_date.
    :param on_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the on_date.
    :return: A dataframe of known email addresses for each Lord, with one
        row per combination of Lord and email address.
    """
    return fetch_members_email_addresses(
        fetch_lords,
        fetch_lords_addresses,
        from_date=from_date,
        to_date=to_date,
        on_date=on_date)


def fetch_lords_phone_numbers(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch phone numbers for Lords.

    fetch_lords_phone_numbers fetches data from the Members Names platform
    on phone numbers for each Lord, with one row per combination of Lord
    and phone number.

    The from_date and to_date arguments can be used to filter the Lords
    based on the dates of their Lords memberships. The on_date argument is
    a convenience that sets the from_date and to_date to the same given
    date. The on_date has priority: if the on_date is set, the from_date
    and to_date are ignored.

    The filtering is inclusive: a Lord is returned if any part of one of
    their Lords memberships falls within the period specified with the from
    and to dates.

    :param from_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the from_date.
    :param to_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the to_date.
    :param on_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the on_date.
    :return: A dataframe of known phone numbers for each Lord, with one row
        per combination of Lord and phone number.
    """
    return fetch_members_phone_numbers(
        fetch_lords,
        fetch_lords_addresses,
        from_date=from_date,
        to_date=to_date,
        on_date=on_date)


def fetch_lords_fax_numbers(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch fax numbers for Lords.

    fetch_lords_fax_numbers fetches data from the Members Names platform on
    fax numbers for each Lord, with one row per combination of Lord and fax
    number.

    The from_date and to_date arguments can be used to filter the Lords
    based on the dates of their Lords memberships. The on_date argument is
    a convenience that sets the from_date and to_date to the same given
    date. The on_date has priority: if the on_date is set, the from_date
    and to_date are ignored.

    The filtering is inclusive: a Lord is returned if any part of one of
    their Lords memberships falls within the period specified with the from
    and to dates.

    :param from_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the from_date.
    :param to_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the to_date.
    :param on_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the on_date.
    :return: A dataframe of known fax numbers for each Lord, with one row
        per combination of Lord and fax number.
    """
    return fetch_members_fax_numbers(
        fetch_lords,
        fetch_lords_addresses,
        from_date=from_date,
        to_date=to_date,
        on_date=on_date)


def fetch_lords_websites(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch websites for Lords.

    fetch_lords_websites fetches data from the Members Names platform on
    websites for each Lord, with one row per combination of Lord and
    website.

    The from_date and to_date arguments can be used to filter the Lords
    based on the dates of their Lords memberships. The on_date argument is
    a convenience that sets the from_date and to_date to the same given
    date. The on_date has priority: if the on_date is set, the from_date
    and to_date are ignored.

    The filtering is inclusive: a Lord is returned if any part of one of
    their Lords memberships falls within the period specified with the from
    and to dates.

    :param from_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the from_date.
    :param to_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the to_date.
    :param on_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the on_date.
    :return: A dataframe of known websites for each Lord, with one row per
        combination of Lord and website.
    """
    return fetch_members_websites(
        fetch_lords,
        fetch_lords_addresses,
        from_date=from_date,
        to_date=to_date,
        on_date=on_date)


def fetch_lords_twitter(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch Twitter accounts for Lords.

    fetch_lords_twitter fetches data from the Members Names platform on
    Twitter accounts for each Lord, with one row per combination of Lord
    and Twitter account.

    The from_date and to_date arguments can be used to filter the Lords
    based on the dates of their Lords memberships. The on_date argument is
    a convenience that sets the from_date and to_date to the same given
    date. The on_date has priority: if the on_date is set, the from_date
    and to_date are ignored.

    The filtering is inclusive: a Lord is returned if any part of one of
    their Lords memberships falls within the period specified with the from
    and to dates.

    :param from_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the from_date.
    :param to_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the to_date.
    :param on_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the on_date.
    :return: A dataframe of known Twitter accounts for each Lord, with one
        row per combination of Lord and Twitter account.
    """
    return fetch_members_twitter(
        fetch_lords,
        fetch_lords_addresses,
        from_date=from_date,
        to_date=to_date,
        on_date=on_date)


def fetch_lords_instagram(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch Instagram accounts for Lords.

    fetch_lords_instagram fetches data from the Members Names platform on
    Instagram accounts for each Lord, with one row per combination of Lord
    and Instagram account.

    The from_date and to_date arguments can be used to filter the Lords
    based on the dates of their Lords memberships. The on_date argument is
    a convenience that sets the from_date and to_date to the same given
    date. The on_date has priority: if the on_date is set, the from_date
    and to_date are ignored.

    The filtering is inclusive: a Lord is returned if any part of one of
    their Lords memberships falls within the period specified with the from
    and to dates.

    :param from_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the from_date.
    :param to_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the to_date.
    :param on_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the on_date.
    :return: A dataframe of known Instagram accounts for each Lord, with
        one row per combination of Lord and Instagram account.
    """
    return fetch_members_instagram(
        fetch_lords,
        fetch_lords_addresses,
        from_date=from_date,
        to_date=to_date,
        on_date=on_date)


def fetch_lords_facebook(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch Facebook accounts for Lords.

    fetch_lords_facebook fetches data from the Members Names platform on
    Facebook accounts for each Lord, with one row per combination of Lord
    and Facebook account.

    The from_date and to_date arguments can be used to filter the Lords
    based on the dates of their Lords memberships. The on_date argument is
    a convenience that sets the from_date and to_date to the same given
    date. The on_date has priority: if the on_date is set, the from_date
    and to_date are ignored.

    The filtering is inclusive: a Lord is returned if any part of one of
    their Lords memberships falls within the period specified with the from
    and to dates.

    :param from_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the from_date.
    :param to_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the to_date.
    :param on_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the on_date.
    :return: A dataframe of known Facebook accounts for each Lord, with one
        row per combination of Lord and Facebook account.
    """
    return fetch_members_facebook(
        fetch_lords,
        fetch_lords_addresses,
        from_date=from_date,
        to_date=to_date,
        on_date=on_date)
