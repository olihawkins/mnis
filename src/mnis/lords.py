"""Functions for downloading and analysing data on Lords"""

# Imports ---------------------------------------------------------------------

import datetime
import polars as pl
import polars.selectors as cs

from polars import DataFrame

from mnis.combine import combine_party_memberships
from mnis.constants import CACHE_LORDS_ADDRESSES_RAW
from mnis.constants import CACHE_LORDS_CONTESTED_ELECTIONS_RAW
from mnis.constants import CACHE_LORDS_GOVERNMENT_ROLES_RAW
from mnis.constants import CACHE_LORDS_MAIDEN_SPEECHES_RAW
from mnis.constants import CACHE_LORDS_MEMBERSHIPS_RAW
from mnis.constants import CACHE_LORDS_OPPOSITION_ROLES_RAW
from mnis.constants import CACHE_LORDS_OTHER_PARLIAMENTS_RAW
from mnis.constants import CACHE_LORDS_PARLIAMENTARY_ROLES_RAW
from mnis.constants import CACHE_LORDS_PARTY_MEMBERSHIPS_RAW
from mnis.constants import cache
from mnis.filters import filter_dates
from mnis.filters import filter_memberships
from mnis.raw_lords import fetch_lords_addresses_raw
from mnis.raw_lords import fetch_lords_contested_elections_raw
from mnis.raw_lords import fetch_lords_government_roles_raw
from mnis.raw_lords import fetch_lords_maiden_speeches_raw
from mnis.raw_lords import fetch_lords_memberships_raw
from mnis.raw_lords import fetch_lords_opposition_roles_raw
from mnis.raw_lords import fetch_lords_other_parliaments_raw
from mnis.raw_lords import fetch_lords_parliamentary_roles_raw
from mnis.raw_lords import fetch_lords_party_memberships_raw
from mnis.raw_lords import fetch_lords_raw

# Constants -------------------------------------------------------------------

Date = str | datetime.date | None

# Fetch functions -------------------------------------------------------------


def fetch_lords(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch key details for all Lords.

    fetch_lords fetches data from the Members Names platform showing key
    details about each Lord, with one row per Lord.

    The from_date and to_date arguments can be used to filter Lords
    returned based on the dates of their Lords memberships. The on_date
    argument is a convenience that sets the from_date and to_date to the
    same given date. The on_date has priority: if the on_date is set, the
    from_date and to_date are ignored.

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
    :return: A dataframe of key details for each Lord, with one row per
        Lord.
    """

    # Set from_date and to_date to on_date if set
    if on_date is not None:
        from_date = on_date
        to_date = on_date

    # Fetch key details
    lords = fetch_lords_raw()

    # Filter on dates if requested
    if from_date is not None or to_date is not None:
        lords_memberships = fetch_lords_memberships()
        matching_memberships = filter_dates(
            lords_memberships,
            start_col="seat_incumbency_start_date",
            end_col="seat_incumbency_end_date",
            from_date=from_date,
            to_date=to_date)
        lords = lords.filter(
            pl.col("mnis_id").is_in(matching_memberships["mnis_id"]))

    # Tidy up and return
    return (
        lords
        .sort("family_name", nulls_last=True, maintain_order=True)
        .with_columns(cs.string().str.strip_chars()))


def fetch_lords_memberships(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch Lords memberships for all Lords.

    fetch_lords_memberships fetches data from the Members Names platform
    showing Lords memberships for each Lord. The memberships are processed
    to impose consistent rules on the start and end dates for memberships.
    A membership with a None end date is still open.

    The from_date and to_date arguments can be used to filter the
    memberships returned. The on_date argument is a convenience that sets
    the from_date and to_date to the same given date. The on_date has
    priority: if the on_date is set, the from_date and to_date are ignored.

    The filtering is inclusive: a membership is returned if any part of it
    falls within the period specified with the from and to dates.

    Note that a membership with a None end date is still open.

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
    :return: A dataframe of Lords memberships for each Lord, with one row
        per Lords membership.
    """

    # Set from_date and to_date to on_date if set
    if on_date is not None:
        from_date = on_date
        to_date = on_date

    # Check cache
    if CACHE_LORDS_MEMBERSHIPS_RAW not in cache:
        lords_memberships = fetch_lords_memberships_raw()
    else:
        lords_memberships = cache[CACHE_LORDS_MEMBERSHIPS_RAW]

    # Filter on dates if requested
    if from_date is not None or to_date is not None:
        lords_memberships = filter_dates(
            lords_memberships,
            start_col="seat_incumbency_start_date",
            end_col="seat_incumbency_end_date",
            from_date=from_date,
            to_date=to_date)

    # Tidy up and return
    return (
        lords_memberships
        .sort(
            ["family_name", "seat_incumbency_start_date"],
            nulls_last=True,
            maintain_order=True)
        .with_columns(cs.string().str.strip_chars()))


def fetch_lords_party_memberships(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None,
        while_lord: bool = True,
        collapse: bool = False) -> DataFrame:
    """Fetch party memberships for all Lords.

    fetch_lords_party_memberships fetches data from the Members Names
    platform showing party memberships for each Lord.

    The from_date and to_date arguments can be used to filter the
    memberships returned. The on_date argument is a convenience that sets
    the from_date and to_date to the same given date. The on_date has
    priority: if the on_date is set, the from_date and to_date are ignored.

    The while_lord argument can be used to filter the memberships to
    include only those that occurred during the period when each individual
    was a Lord.

    The filtering is inclusive: a membership is returned if any part of it
    falls within the period specified with the from and to dates.

    The collapse argument controls whether memberships are combined so that
    there is only one row for each period of continuous membership within
    the same party. Combining the memberships in this way means that party
    membership ids from the data platform are not included in the dataframe
    returned.

    Note that a membership with a None end date is still open.

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
    :param while_lord: A boolean indicating whether to filter the party
        membership to include only those memberships that were held while
        each individual was serving as a Lord. The default value is True.
    :param collapse: A boolean which determines whether to collapse
        consecutive memberships within the same party into a single period
        of continuous party membership. Setting this to True means that
        party membership ids are not returned in the dataframe. The default
        value is False.
    :return: A dataframe of party memberships for each Lord, with one row
        per party membership.
    """

    # Set from_date and to_date to on_date if set
    if on_date is not None:
        from_date = on_date
        to_date = on_date

    # Check cache
    if CACHE_LORDS_PARTY_MEMBERSHIPS_RAW not in cache:
        party_memberships = fetch_lords_party_memberships_raw()
    else:
        party_memberships = cache[CACHE_LORDS_PARTY_MEMBERSHIPS_RAW]

    # Filter on dates if requested
    if from_date is not None or to_date is not None:
        party_memberships = filter_dates(
            party_memberships,
            start_col="party_membership_start_date",
            end_col="party_membership_end_date",
            from_date=from_date,
            to_date=to_date)

    # Filter on memberships if requested
    if while_lord:
        lords_memberships = fetch_lords_memberships()
        party_memberships = filter_memberships(
            tm=party_memberships,
            fm=lords_memberships,
            tm_id_col="party_mnis_id",
            tm_start_col="party_membership_start_date",
            tm_end_col="party_membership_end_date",
            fm_start_col="seat_incumbency_start_date",
            fm_end_col="seat_incumbency_end_date",
            join_col="mnis_id")

    # Collapse consecutive memberships if requested
    if collapse:
        party_memberships = combine_party_memberships(party_memberships)

    # Tidy up and return
    return (
        party_memberships
        .sort(
            ["family_name", "party_membership_start_date"],
            nulls_last=True,
            maintain_order=True)
        .with_columns(cs.string().str.strip_chars()))


def fetch_lords_other_parliaments(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch other parliament memberships for all Lords.

    fetch_lords_other_parliaments fetches data from the Members Names
    platform showing other parliamentary memberships for each Lord.

    The from_date and to_date arguments can be used to filter the
    memberships returned. The on_date argument is a convenience that sets
    the from_date and to_date to the same given date. The on_date has
    priority: if the on_date is set, the from_date and to_date are ignored.

    The filtering is inclusive: an other parliamentary membership is
    returned if the date of it falls within the period specified with the
    from and to dates.

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
    :return: A dataframe of other parliamentary incumbencies for each Lord,
        with one row per membership.
    """

    # Set from_date and to_date to on_date if set
    if on_date is not None:
        from_date = on_date
        to_date = on_date

    # Check cache
    if CACHE_LORDS_OTHER_PARLIAMENTS_RAW not in cache:
        other_parliaments = fetch_lords_other_parliaments_raw()
    else:
        other_parliaments = cache[CACHE_LORDS_OTHER_PARLIAMENTS_RAW]

    # Filter on dates if requested
    if from_date is not None or to_date is not None:
        other_parliaments = filter_dates(
            other_parliaments,
            start_col="other_parliaments_incumbency_start_date",
            end_col="other_parliaments_incumbency_end_date",
            from_date=from_date,
            to_date=to_date)

    # Tidy up and return
    return (
        other_parliaments
        .sort(
            ["family_name", "other_parliaments_incumbency_start_date"],
            nulls_last=True,
            maintain_order=True)
        .with_columns(cs.string().str.strip_chars()))


def fetch_lords_contested_elections(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch contested elections for all Lords.

    fetch_lords_contested_elections fetches data from the Members Names
    platform showing contested elections for each Lord.

    The from_date and to_date arguments can be used to filter the contested
    elections returned. The on_date argument is a convenience that sets the
    from_date and to_date to the same given date. The on_date has priority:
    if the on_date is set, the from_date and to_date are ignored.

    The filtering is inclusive: a contested election is returned if the
    date of it falls within the period specified with the from and to
    dates.

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
    :return: A dataframe of contested elections for each Lord, with one row
        per contested election.
    """

    # Set from_date and to_date to on_date if set
    if on_date is not None:
        from_date = on_date
        to_date = on_date

    # Check cache
    if CACHE_LORDS_CONTESTED_ELECTIONS_RAW not in cache:
        contested_elections = fetch_lords_contested_elections_raw()
    else:
        contested_elections = cache[CACHE_LORDS_CONTESTED_ELECTIONS_RAW]

    # Filter on dates if requested
    if from_date is not None or to_date is not None:
        contested_elections = filter_dates(
            contested_elections,
            start_col="contested_election_date",
            end_col="contested_election_date",
            from_date=from_date,
            to_date=to_date)

    # Tidy up and return
    return (
        contested_elections
        .sort(
            ["family_name", "contested_election_date"],
            nulls_last=True,
            maintain_order=True)
        .with_columns(cs.string().str.strip_chars()))


def fetch_lords_government_roles(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None,
        while_lord: bool = True) -> DataFrame:
    """Fetch government roles for all Lords.

    fetch_lords_government_roles fetches data from the Members Names
    platform showing government roles for each Lord.

    The from_date and to_date arguments can be used to filter the roles
    returned. The on_date argument is a convenience that sets the from_date
    and to_date to the same given date. The on_date has priority: if the
    on_date is set, the from_date and to_date are ignored.

    The while_lord argument can be used to filter the roles to include only
    those that occurred during the period when each individual was a Lord.

    The filtering is inclusive: a role is returned if any part of it falls
    within the period specified with the from and to dates.

    Note that a role with a None end date is still open.

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
    :param while_lord: A boolean indicating whether to filter the
        government roles to include only those roles that were held while
        each individual was serving as a Lord. The default value is True.
    :return: A dataframe of government roles for each Lord, with one row
        per government role.
    """

    # Set from_date and to_date to on_date if set
    if on_date is not None:
        from_date = on_date
        to_date = on_date

    # Check cache
    if CACHE_LORDS_GOVERNMENT_ROLES_RAW not in cache:
        government_roles = fetch_lords_government_roles_raw()
    else:
        government_roles = cache[CACHE_LORDS_GOVERNMENT_ROLES_RAW]

    # Filter on dates if requested
    if from_date is not None or to_date is not None:
        government_roles = filter_dates(
            government_roles,
            start_col="government_role_incumbency_start_date",
            end_col="government_role_incumbency_end_date",
            from_date=from_date,
            to_date=to_date)

    # Filter on memberships if requested
    if while_lord:
        lords_memberships = fetch_lords_memberships()
        government_roles = filter_memberships(
            tm=government_roles,
            fm=lords_memberships,
            tm_id_col="government_role_mnis_id",
            tm_start_col="government_role_incumbency_start_date",
            tm_end_col="government_role_incumbency_end_date",
            fm_start_col="seat_incumbency_start_date",
            fm_end_col="seat_incumbency_end_date",
            join_col="mnis_id")

    # Tidy up and return
    return (
        government_roles
        .sort(
            ["family_name", "government_role_incumbency_start_date"],
            nulls_last=True,
            maintain_order=True)
        .with_columns(cs.string().str.strip_chars()))


def fetch_lords_opposition_roles(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None,
        while_lord: bool = True) -> DataFrame:
    """Fetch opposition roles for all Lords.

    fetch_lords_opposition_roles fetches data from the Members Names
    platform showing opposition roles for each Lord.

    The from_date and to_date arguments can be used to filter the roles
    returned. The on_date argument is a convenience that sets the from_date
    and to_date to the same given date. The on_date has priority: if the
    on_date is set, the from_date and to_date are ignored.

    The while_lord argument can be used to filter the roles to include only
    those that occurred during the period when each individual was a Lord.

    The filtering is inclusive: a role is returned if any part of it falls
    within the period specified with the from and to dates.

    Note that a role with a None end date is still open.

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
    :param while_lord: A boolean indicating whether to filter the
        opposition roles to include only those roles that were held while
        each individual was serving as a Lord. The default value is True.
    :return: A dataframe of opposition roles for each Lord, with one row
        per opposition role.
    """

    # Set from_date and to_date to on_date if set
    if on_date is not None:
        from_date = on_date
        to_date = on_date

    # Check cache
    if CACHE_LORDS_OPPOSITION_ROLES_RAW not in cache:
        opposition_roles = fetch_lords_opposition_roles_raw()
    else:
        opposition_roles = cache[CACHE_LORDS_OPPOSITION_ROLES_RAW]

    # Filter on dates if requested
    if from_date is not None or to_date is not None:
        opposition_roles = filter_dates(
            opposition_roles,
            start_col="opposition_role_incumbency_start_date",
            end_col="opposition_role_incumbency_end_date",
            from_date=from_date,
            to_date=to_date)

    # Filter on memberships if requested
    if while_lord:
        lords_memberships = fetch_lords_memberships()
        opposition_roles = filter_memberships(
            tm=opposition_roles,
            fm=lords_memberships,
            tm_id_col="opposition_role_mnis_id",
            tm_start_col="opposition_role_incumbency_start_date",
            tm_end_col="opposition_role_incumbency_end_date",
            fm_start_col="seat_incumbency_start_date",
            fm_end_col="seat_incumbency_end_date",
            join_col="mnis_id")

    # Tidy up and return
    return (
        opposition_roles
        .sort(
            ["family_name", "opposition_role_incumbency_start_date"],
            nulls_last=True,
            maintain_order=True)
        .with_columns(cs.string().str.strip_chars()))


def fetch_lords_parliamentary_roles(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None,
        while_lord: bool = True) -> DataFrame:
    """Fetch parliamentary roles for all Lords.

    fetch_lords_parliamentary_roles fetches data from the Members Names
    platform showing parliamentary roles for each Lord.

    The from_date and to_date arguments can be used to filter the roles
    returned. The on_date argument is a convenience that sets the from_date
    and to_date to the same given date. The on_date has priority: if the
    on_date is set, the from_date and to_date are ignored.

    The while_lord argument can be used to filter the roles to include only
    those that occurred during the period when each individual was a Lord.

    The filtering is inclusive: a role is returned if any part of it falls
    within the period specified with the from and to dates.

    Note that a role with a None end date is still open.

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
    :param while_lord: A boolean indicating whether to filter the
        parliamentary roles to include only those roles that were held
        while each individual was serving as a Lord. The default value is
        True.
    :return: A dataframe of parliamentary roles for each Lord, with one row
        per parliamentary role.
    """

    # Set from_date and to_date to on_date if set
    if on_date is not None:
        from_date = on_date
        to_date = on_date

    # Check cache
    if CACHE_LORDS_PARLIAMENTARY_ROLES_RAW not in cache:
        parliamentary_roles = fetch_lords_parliamentary_roles_raw()
    else:
        parliamentary_roles = cache[CACHE_LORDS_PARLIAMENTARY_ROLES_RAW]

    # Filter on dates if requested
    if from_date is not None or to_date is not None:
        parliamentary_roles = filter_dates(
            parliamentary_roles,
            start_col="parliamentary_role_incumbency_start_date",
            end_col="parliamentary_role_incumbency_end_date",
            from_date=from_date,
            to_date=to_date)

    # Filter on memberships if requested
    if while_lord:
        lords_memberships = fetch_lords_memberships()
        parliamentary_roles = filter_memberships(
            tm=parliamentary_roles,
            fm=lords_memberships,
            tm_id_col="parliamentary_role_mnis_id",
            tm_start_col="parliamentary_role_incumbency_start_date",
            tm_end_col="parliamentary_role_incumbency_end_date",
            fm_start_col="seat_incumbency_start_date",
            fm_end_col="seat_incumbency_end_date",
            join_col="mnis_id")

    # Tidy up and return
    return (
        parliamentary_roles
        .sort(
            ["family_name", "parliamentary_role_incumbency_start_date"],
            nulls_last=True,
            maintain_order=True)
        .with_columns(cs.string().str.strip_chars()))


def fetch_lords_maiden_speeches(
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> DataFrame:
    """Fetch maiden speeches for all Lords.

    fetch_lords_maiden_speeches fetches data from the Members Names
    platform showing maiden speeches for each Lord.

    The from_date and to_date arguments can be used to filter the speeches
    returned. The on_date argument is a convenience that sets the from_date
    and to_date to the same given date. The on_date has priority: if the
    on_date is set, the from_date and to_date are ignored.

    The filtering is inclusive: a speech is returned if the date of it
    falls within the period specified with the from and to dates.

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
    :return: A dataframe of maiden speeches for each Lord, with one row per
        maiden speech.
    """

    # Set from_date and to_date to on_date if set
    if on_date is not None:
        from_date = on_date
        to_date = on_date

    # Check cache
    if CACHE_LORDS_MAIDEN_SPEECHES_RAW not in cache:
        maiden_speeches = fetch_lords_maiden_speeches_raw()
    else:
        maiden_speeches = cache[CACHE_LORDS_MAIDEN_SPEECHES_RAW]

    # Filter on dates if requested
    if from_date is not None or to_date is not None:
        maiden_speeches = filter_dates(
            maiden_speeches,
            start_col="maiden_speech_date",
            end_col="maiden_speech_date",
            from_date=from_date,
            to_date=to_date)

    # Tidy up and return
    return (
        maiden_speeches
        .sort(
            ["family_name", "maiden_speech_date"],
            nulls_last=True,
            maintain_order=True)
        .with_columns(cs.string().str.strip_chars()))


def fetch_lords_addresses() -> DataFrame:
    """Fetch addresses for all Lords.

    fetch_lords_addresses fetches data from the Members Names platform
    showing contact details for each Lord.

    Addresses can represent contact information of different types,
    including physical addresses, phone, fax, email, website, and social
    media. These addresses are not time bound in MNIS so date filtering is
    not available for this function.

    :return: A dataframe of addresses for each Lord, with one row per
        address.
    """

    # Check cache
    if CACHE_LORDS_ADDRESSES_RAW not in cache:
        addresses = fetch_lords_addresses_raw()
    else:
        addresses = cache[CACHE_LORDS_ADDRESSES_RAW]

    # Tidy up and return
    return (
        addresses
        .sort(
            ["family_name", "address_type_mnis_id"],
            nulls_last=True,
            maintain_order=True)
        .with_columns(cs.string().str.strip_chars()))
