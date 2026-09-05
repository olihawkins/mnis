"""Utility functions used across the package"""

# Imports ---------------------------------------------------------------------

import datetime
import json
import polars as pl
import re
import requests
import time

from polars import DataFrame

from mnis.cache import cache
from mnis.constants import API_RETRIES
from mnis.constants import API_RETRY_BACKOFF
from mnis.constants import API_RETRY_STATUSES
from mnis.constants import CACHE_LORDS_RAW
from mnis.constants import CACHE_MPS_RAW
from mnis.constants import MNIS_API
from mnis.errors import check_query_status
from mnis.errors import date_format_error
from mnis.errors import retry_error
from mnis.settings import get_timeout

# API query functions ---------------------------------------------------------

def create_query(house: str, data_output: str) -> str:
    """Create query string."""
    return f"{MNIS_API}House={house}|Membership=all/{data_output}"


def fetch_query_response(query: str) -> requests.Response:
    """Send a query to MNIS and return the response.

    Each request waits for the number of seconds given by the timeout
    setting, which can be changed with set_timeout. A request which fails
    because it timed out, because the connection failed, or because the API
    returned a status indicating a temporary problem, is retried after a
    wait which doubles with each attempt. A request which fails for any
    other reason is returned to the caller without being retried, as
    repeating it cannot change the outcome.

    :param query: The query to send to the API.
    """
    reason = ""

    for attempt in range(API_RETRIES + 1):

        # Wait before retrying
        if attempt > 0:
            time.sleep(API_RETRY_BACKOFF[attempt - 1])

        # Send the query
        try:
            response = requests.get(
                query,
                headers={"Accept": "application/json"},
                timeout=get_timeout())
        except requests.exceptions.RequestException as error:
            reason = str(error)
            continue

        # Return the response unless the status means try again
        if response.status_code not in API_RETRY_STATUSES:
            return response

        reason = f"the API returned status {response.status_code}"

    raise RuntimeError(retry_error(API_RETRIES + 1, reason))


def fetch_query_data(house: str, data_output: str) -> list[dict]:
    """Fetch data from MNIS based on given query."""

    # Create query
    query = create_query(house, data_output)

    # Fetch data
    response = fetch_query_response(query)
    check_query_status(response.status_code)
    query_data = json.loads(response.content.decode("utf-8-sig"))
    return query_data["Members"]["Member"]

# Missing data functions ------------------------------------------------------

def scalar(value: object) -> object:
    """Convert a raw JSON value to a scalar, mapping nil objects to None.

    The MNIS API represents a missing value with an XML nil object, which
    appears as a dict after parsing the JSON. Values taken from the parsed
    JSON are passed through this function so that a missing value becomes
    None.

    :param value: The value taken from the parsed JSON.
    """
    return None if isinstance(value, dict) else value

# Data handling functions -----------------------------------------------------

def extract_data_output(
        data_output: list[dict],
        col_section_a: str,
        col_section_b: str,
        columns: list[str]) -> DataFrame:
    """Extract data output.

    Takes the list of member data returned from the API and extracts the
    entries nested under the two given keys for each member, returning one
    row per entry with the member's id in a column called mnis_id. Values
    which are nil objects are converted to None.

    The columns of the dataframe returned are those given in columns, which
    are the field names used by MNIS for the given data output, together
    with mnis_id. The columns are specified rather than taken from the data
    so that the dataframe has the same structure whatever the API returns:
    a field which is absent from every record in a response, or a response
    with no records at all, still produces the expected columns.

    :param data_output: The list of member data returned from the API.
    :param col_section_a: The key of the section containing the entries.
    :param col_section_b: The key of the entries within that section.
    :param columns: The names of the columns of the data output.
    """
    rows = []
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
            rows.append(row)
    schema = {column: pl.String for column in columns}
    return pl.from_dicts(rows, schema=schema)


def process_mps_output(output_table: DataFrame) -> DataFrame:
    """Combine basic MP data with output table."""

    from mnis.raw_mps import fetch_mps_raw

    # Check cache
    if CACHE_MPS_RAW not in cache:
        mps = fetch_mps_raw()
    else:
        mps = cache[CACHE_MPS_RAW]

    # Select basic details
    mps = mps.select(
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

    # Check cache
    if CACHE_LORDS_RAW not in cache:
        lords = fetch_lords_raw()
    else:
        lords = cache[CACHE_LORDS_RAW]

    # Select basic details
    lords = lords.select(
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
