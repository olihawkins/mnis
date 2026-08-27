"""Filter functions"""

# Imports ---------------------------------------------------------------------

import datetime
import polars as pl

from polars import DataFrame

from mnis.errors import date_format_error
from mnis.errors import missing_column_error
from mnis.utility import parse_date

# Filter dates ----------------------------------------------------------------


def filter_dates(
        df: DataFrame,
        start_col: str,
        end_col: str,
        from_date: str | datetime.date | None = None,
        to_date: str | datetime.date | None = None) -> DataFrame:
    """Filter a dataframe of data based on the given from and to dates.

    filter_dates takes a dataframe which contains data on a time bound
    activity and returns the subset of rows where that activity took place
    within a given period. The dataframe must contain two columns of dates,
    which record the start and end dates of an activity. The from and to
    dates provided are used to find all rows where some part of the period
    of activity took place within the period of filtering. The filtering
    process is inclusive: as long as at least one day of activity falls
    within the filtering period, the row is returned.

    :param df: A dataframe containing data on a time bound activity.
    :param start_col: The name of the column that contains the start date
        for the activity.
    :param end_col: The name of the column that contains the end date for
        the activity.
    :param from_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the from_date.
    :param to_date: A string or date representing a date. If a string is
        used it should specify the date in ISO 8601 date format e.g.
        '2000-12-31'. The default value is None, which means no records are
        excluded on the basis of the to_date.
    :return: A dataframe with the same structure as the input df containing
        the rows that meet the filtering criteria.
    """

    # Check the start and end columns exist
    if start_col not in df.columns:
        raise ValueError(missing_column_error(start_col))

    if end_col not in df.columns:
        raise ValueError(missing_column_error(end_col))

    # Check there are dates to filter
    if from_date is None and to_date is None:
        return df

    # Handle from and to dates
    from_date = handle_date(from_date)
    to_date = handle_date(to_date)

    # Check from date is before to date
    if from_date is not None and to_date is not None and from_date > to_date:
        raise ValueError("to_date is before from_date")

    # Check the dataframe has rows. This follows the checks above so that
    # invalid arguments are reported whether or not there is data to filter
    if df.height == 0:
        return df

    # Set default values
    from_after_end = pl.lit(False)
    to_before_start = pl.lit(False)

    # Get matching rows
    if from_date is not None:
        from_after_end = (
            pl.col(end_col).is_not_null() &
            (pl.lit(from_date) > pl.col(end_col)))

    if to_date is not None:
        to_before_start = (
            pl.col(start_col).is_not_null() &
            (pl.lit(to_date) < pl.col(start_col)))

    return df.filter(~(from_after_end | to_before_start))


def handle_date(d: str | datetime.date | None) -> datetime.date | None:
    """Take a date which may be a string or a date and return a date.

    handle_date takes a date which may be a datetime.date or an ISO 8601
    date string, checks it is valid, and returns the date as a
    datetime.date. None values are returned unmodified. This function
    raises an error if it is unable to handle the date.
    """
    if d is None:
        return d
    elif isinstance(d, datetime.date):
        return d
    elif isinstance(d, str):
        return parse_date(d)
    else:
        raise ValueError(date_format_error(d))


# Filter memberships ----------------------------------------------------------


def filter_memberships(
        tm: DataFrame,
        fm: DataFrame,
        tm_start_col: str,
        tm_end_col: str,
        fm_start_col: str,
        fm_end_col: str,
        join_col: str) -> DataFrame:
    """Filter a dataframe of memberships to include only the rows whose
    period of membership intersects with those in another dataframe of
    memberships.

    filter_memberships is a function to find all memberships in one
    dataframe that intersect with those in another dataframe for each
    person, or other entity. This function lets you find things like all
    committee memberships for Commons Members during the period they have
    served as an MP, or all government roles held by Members of the House of
    Lords while they have served in the Lords.

    :param tm: A dataframe containing the target memberships. These are the
        memberships to be filtered.
    :param fm: A dataframe containing the filter memberships. These are the
        memberships that are used to filter the target memberships.
    :param tm_start_col: The name of the column in target memberships that
        contains the start date for the membership.
    :param tm_end_col: The name of the column in target memberships that
        contains the end date for the membership.
    :param fm_start_col: The name of the column in filter memberships that
        contains the start date for the membership.
    :param fm_end_col: The name of the column in filter memberships that
        contains the end date for the membership.
    :param join_col: The name of the column in both the target and filter
        memberships that contains the id of the entity that is common to
        both tables. Where the entity is a person this will be the person
        id.
    :return: A dataframe with the same structure as the input tm containing
        the rows that meet the filtering criteria.
    """

    # Check the columns exist in each dataframe
    if tm_start_col not in tm.columns:
        raise ValueError(missing_column_error(tm_start_col))

    if tm_end_col not in tm.columns:
        raise ValueError(missing_column_error(tm_end_col))

    if join_col not in tm.columns:
        raise ValueError(missing_column_error(join_col))

    if fm_start_col not in fm.columns:
        raise ValueError(missing_column_error(fm_start_col))

    if fm_end_col not in fm.columns:
        raise ValueError(missing_column_error(fm_end_col))

    if join_col not in fm.columns:
        raise ValueError(missing_column_error(join_col))

    # Check the target dataframe has rows. This follows the checks above so
    # that invalid arguments are reported whether or not there is data to
    # filter
    if tm.height == 0:
        return tm

    # Number the target memberships so that the match status calculated
    # below can be attached back to the row it was calculated from. The
    # target membership id is not sufficient for this: ids identify things
    # like posts and parties, which the same person can hold more than once
    # and which are sometimes missing from the data
    tmn = tm.with_row_index("tm_row")

    # Create abstract copies of tm and fm
    tma = tmn.select(
        "tm_row",
        pl.col(join_col).alias("join_col"),
        pl.col(tm_start_col).alias("tm_start_col"),
        pl.col(tm_end_col).alias("tm_end_col"))

    fma = fm.select(
        pl.col(join_col).alias("join_col"),
        pl.col(fm_start_col).alias("fm_start_col"),
        pl.col(fm_end_col).alias("fm_end_col"))

    # Join the target memberships with the filter membership dates on
    # join_col. The join is inner so that an entity with no filter
    # memberships contributes no rows: such an entity has no period of
    # membership for its target memberships to fall within, so all of them
    # are excluded by the filtering below
    tm_fm = tma.join(fma, on="join_col", how="inner", maintain_order="left")

    # Test if each target membership and filter membership intersect
    tm_start_after_fm_end = (
        pl.col("tm_start_col").is_not_null() &
        pl.col("fm_end_col").is_not_null() &
        (pl.col("tm_start_col") > pl.col("fm_end_col")))

    tm_end_before_fm_start = (
        pl.col("tm_end_col").is_not_null() &
        pl.col("fm_start_col").is_not_null() &
        (pl.col("tm_end_col") < pl.col("fm_start_col")))

    tm_fm = tm_fm.with_columns(
        (~(tm_start_after_fm_end | tm_end_before_fm_start))
        .alias("in_membership"))

    # Summarise the match status for each target membership: the join above
    # produces one row for each combination of target membership and filter
    # membership, so a target membership is within a membership if it
    # intersects with any of that entity's filter memberships
    match_status = (
        tm_fm
        .group_by("tm_row")
        .agg(pl.col("in_membership").any()))

    # Join the match status with the original target memberships data
    tm_fm_status = tmn.join(
        match_status,
        on="tm_row",
        how="left",
        maintain_order="left")

    # Set the match status explicitly for any target membership that has no
    # status after the join. These belong to entities with no filter
    # memberships at all, which the inner join above discards, so there is
    # nothing to summarise for them. Such an entity has no period of
    # membership for its target memberships to fall within, so none of them
    # are within a membership. Stating this here means the filter below
    # never has to depend on how it treats a null
    tm_fm_status = tm_fm_status.with_columns(
        pl.col("in_membership").fill_null(False))

    # Return the target memberships after filtering
    return (
        tm_fm_status
        .filter(pl.col("in_membership"))
        .drop("tm_row", "in_membership"))
