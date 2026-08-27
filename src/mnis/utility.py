"""Utility functions used across the package"""

# Imports ---------------------------------------------------------------------

import datetime
import json
import math
import polars as pl
import re
import requests

from polars import DataFrame

from mnis.constants import MNIS_API
from mnis.errors import check_query_status
from mnis.errors import date_format_error

# API query functions ---------------------------------------------------------


def create_query(house: str, data_output: str) -> str:
    """Create query string."""
    return f"{MNIS_API}House={house}|Membership=all/{data_output}"


def fetch_query_data(house: str, data_output: str) -> list[dict]:
    """Fetch data from MNIS based on given query."""

    # Create query
    query = create_query(house, data_output)

    # Fetch data
    response = requests.get(query, headers={"Accept": "application/json"})
    check_query_status(response.status_code)
    query_data = json.loads(response.content.decode("utf-8-sig"))
    return query_data["Members"]["Member"]


# Missing data functions ------------------------------------------------------

XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"


def process_missing_values(data: list[dict], column: str) -> list[dict]:
    """Convert values representing missing data in a column to None.

    The MNIS API represents missing values with an XML nil object, which
    appears as a dict after parsing the JSON. This function operates on the
    rows of extracted data before they are converted to a dataframe: rows
    whose value in the given column is the bare XML schema namespace are
    removed, and values which are nil objects (or the residual string "true")
    are replaced with None. This mirrors the behaviour of the equivalent
    function in the R package, which operates on R's deparsed representation
    of the same nil objects.
    """
    rows = [row for row in data if row.get(column) != XSI_NAMESPACE]
    for row in rows:
        value = row.get(column)
        if value == "true" or isinstance(value, dict):
            row[column] = None
    return rows


# Data handling functions -----------------------------------------------------


def process_member_age(
        from_date: datetime.date,
        to_date: datetime.date | None) -> int:
    """Calculate current age of member."""

    def decimal_date(d: datetime.date) -> float:
        year_start = datetime.date(d.year, 1, 1)
        next_year_start = datetime.date(d.year + 1, 1, 1)
        year_length = (next_year_start - year_start).days
        return d.year + (d - year_start).days / year_length

    if to_date is None:
        to_date = datetime.date.today()
    return math.floor(decimal_date(to_date) - decimal_date(from_date))


def extract_data_output(
        data_output: list[dict],
        col_section_a: str,
        col_section_b: str) -> DataFrame:
    """Extract data output.

    Takes the list of member data returned from the API and extracts the
    entries nested under the two given keys for each member, returning one
    row per entry with the member's id in a column called mnis_id. Values
    which are nil objects are converted to None.
    """
    rows = []
    columns = []
    for member in data_output:
        mnis_id = member["@Member_Id"]
        entries = member[col_section_a][col_section_b]
        if isinstance(entries, dict):
            entries = [entries]
        for entry in entries:
            row = {
                key: None if isinstance(value, dict) else value
                for key, value in entry.items()
            }
            row["mnis_id"] = mnis_id
            for key in row:
                if key not in columns:
                    columns.append(key)
            rows.append(row)
    schema = {column: pl.String for column in columns}
    return pl.from_dicts(rows, schema=schema)


def process_mps_output(output_table: DataFrame) -> DataFrame:
    """Combine basic MP data with output table."""

    from mnis.raw_mps import fetch_mps_raw

    # Fetch basic details
    mps = fetch_mps_raw().select(
        "mnis_id",
        "given_name",
        "family_name",
        "display_name")

    # Join tables and tidy
    output = output_table.join(
        mps, on="mnis_id", how="left", maintain_order="left")
    first_columns = ["mnis_id", "given_name", "family_name", "display_name"]
    other_columns = [c for c in output.columns if c not in first_columns]
    return output.select(first_columns + other_columns)


def process_lords_output(output_table: DataFrame) -> DataFrame:
    """Combine basic Lords data with output table."""

    from mnis.raw_lords import fetch_lords_raw

    # Fetch basic details
    lords = fetch_lords_raw().select(
        "mnis_id",
        "given_name",
        "family_name",
        "display_name")

    # Join tables and tidy
    output = output_table.join(
        lords, on="mnis_id", how="left", maintain_order="left")
    first_columns = ["mnis_id", "given_name", "family_name", "display_name"]
    other_columns = [c for c in output.columns if c not in first_columns]
    return output.select(first_columns + other_columns)


# Date handling functions -----------------------------------------------------


def cast_date(date_num: float | None) -> datetime.date | None:
    """Cast a numeric value to a date."""
    if date_num is None:
        return None
    try:
        return datetime.date(1970, 1, 1) + datetime.timedelta(days=date_num)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Could not cast numeric to date")


def parse_date(date_str: str) -> datetime.date:
    """Parse an ISO 8601 date from a string."""

    valid_pattern = r"^\d{4}\-(0[1-9]|1[012])\-(0[1-9]|[12][0-9]|3[01])$"
    if not re.match(valid_pattern, date_str):
        raise ValueError(date_format_error(date_str))

    try:
        return datetime.date.fromisoformat(date_str)
    except ValueError:
        raise ValueError(date_format_error(date_str))


def convert_date_column(df: DataFrame, column: str) -> DataFrame:
    """Convert a column of date strings to dates.

    Equivalent to calling as.Date on a character column in R: the date is
    parsed from the leading YYYY-MM-DD portion of the string and values
    which cannot be parsed become null.
    """
    return df.with_columns(
        pl.col(column).str.slice(0, 10).str.to_date("%Y-%m-%d", strict=False))
