"""Functions for extracting contact details from the Members addresses
table"""

import datetime
from typing import Callable

import polars as pl

Date = str | datetime.date | None


def extract_username(url: str) -> str:
    """Extract a username from a social media url.

    The username is the last or penultimate token in the url, ignoring
    query strings.
    """
    url_parts = url.split("/")
    last_token = url_parts[-1]
    if last_token == "" or last_token.startswith("?"):
        username = url_parts[-2]
    elif "?" in last_token:
        username = last_token.split("?")[0]
    else:
        username = last_token
    return username


# Office addresses ------------------------------------------------------------


def fetch_members_office_addresses(
        fetch_members: Callable,
        fetch_addresses: Callable,
        address_func: Callable | None = None,
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> pl.DataFrame:
    """Fetch office addresses for Members."""

    # Fetch members for the given dates
    members = fetch_members(
        from_date=from_date,
        to_date=to_date,
        on_date=on_date).select("mnis_id")

    # Fetch office addresses for members
    offices = (
        fetch_addresses()
        .filter(pl.col("address_is_physical"))
        .filter(pl.col("address_1").is_not_null())
        .select(
            "mnis_id",
            "given_name",
            "family_name",
            "display_name",
            "address_type",
            "address_is_preferred",
            "address_1",
            "address_2",
            "address_3",
            "address_4",
            "address_5",
            "postcode"))

    # Filter office addresses for the given members
    return offices.filter(pl.col("mnis_id").is_in(members["mnis_id"]))


# Email addresses -------------------------------------------------------------


def fetch_members_email_addresses(
        fetch_members: Callable,
        fetch_addresses: Callable,
        address_func: Callable | None = None,
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> pl.DataFrame:
    """Fetch email addresses for Members."""

    # Fetch members for the given dates
    members = fetch_members(
        from_date=from_date,
        to_date=to_date,
        on_date=on_date).select("mnis_id")

    # Fetch email addresses for members
    emails = (
        fetch_addresses()
        .filter(pl.col("address_is_physical"))
        .filter(pl.col("email").is_not_null())
        .select(
            "mnis_id",
            "given_name",
            "family_name",
            "display_name",
            "address_type",
            "email"))

    # Filter email addresses for the given members
    return emails.filter(pl.col("mnis_id").is_in(members["mnis_id"]))


# Phone numbers ---------------------------------------------------------------


def fetch_members_phone_numbers(
        fetch_members: Callable,
        fetch_addresses: Callable,
        address_func: Callable | None = None,
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> pl.DataFrame:
    """Fetch phone numbers for Members."""

    # Fetch members for the given dates
    members = fetch_members(
        from_date=from_date,
        to_date=to_date,
        on_date=on_date).select("mnis_id")

    # Fetch phone numbers for members
    phones = (
        fetch_addresses()
        .filter(pl.col("address_is_physical"))
        .filter(pl.col("phone").is_not_null())
        .select(
            "mnis_id",
            "given_name",
            "family_name",
            "display_name",
            "address_type",
            "phone"))

    # Filter phone numbers for the given members
    return phones.filter(pl.col("mnis_id").is_in(members["mnis_id"]))


# Fax numbers -----------------------------------------------------------------


def fetch_members_fax_numbers(
        fetch_members: Callable,
        fetch_addresses: Callable,
        address_func: Callable | None = None,
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> pl.DataFrame:
    """Fetch fax numbers for Members."""

    # Fetch members for the given dates
    members = fetch_members(
        from_date=from_date,
        to_date=to_date,
        on_date=on_date).select("mnis_id")

    # Fetch fax numbers for members
    faxes = (
        fetch_addresses()
        .filter(pl.col("address_is_physical"))
        .filter(pl.col("fax").is_not_null())
        .select(
            "mnis_id",
            "given_name",
            "family_name",
            "display_name",
            "address_type",
            "fax"))

    # Filter fax numbers for the given members
    return faxes.filter(pl.col("mnis_id").is_in(members["mnis_id"]))


# Websites --------------------------------------------------------------------


def fetch_members_websites(
        fetch_members: Callable,
        fetch_addresses: Callable,
        address_func: Callable | None = None,
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> pl.DataFrame:
    """Fetch websites for Members."""

    # Fetch members for the given dates
    members = fetch_members(
        from_date=from_date,
        to_date=to_date,
        on_date=on_date).select("mnis_id")

    # Fetch websites for members
    websites = (
        fetch_addresses()
        .filter(pl.col("address_type_mnis_id") == "6")
        .filter(pl.col("address_1").is_not_null())
        .select(
            "mnis_id",
            "given_name",
            "family_name",
            "display_name",
            "address_type",
            pl.col("address_1").alias("url")))

    # Filter websites for the given members
    return websites.filter(pl.col("mnis_id").is_in(members["mnis_id"]))


# Blogs -----------------------------------------------------------------------


def fetch_members_blogs(
        fetch_members: Callable,
        fetch_addresses: Callable,
        address_func: Callable | None = None,
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> pl.DataFrame:
    """Fetch blogs for Members."""

    # Fetch members for the given dates
    members = fetch_members(
        from_date=from_date,
        to_date=to_date,
        on_date=on_date).select("mnis_id")

    # Fetch blogs for members
    blogs = (
        fetch_addresses()
        .filter(pl.col("address_type_mnis_id") == "10")
        .filter(pl.col("address_1").is_not_null())
        .select(
            "mnis_id",
            "given_name",
            "family_name",
            "display_name",
            "address_type",
            pl.col("address_1").alias("url")))

    # Filter blogs for the given members
    return blogs.filter(pl.col("mnis_id").is_in(members["mnis_id"]))


# Twitter ---------------------------------------------------------------------


def fetch_members_twitter(
        fetch_members: Callable,
        fetch_addresses: Callable,
        address_func: Callable | None = None,
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> pl.DataFrame:
    """Fetch Twitter accounts for Members."""

    # Fetch members for the given dates
    members = fetch_members(
        from_date=from_date,
        to_date=to_date,
        on_date=on_date).select("mnis_id")

    # Fetch Twitter accounts for members
    accounts = (
        fetch_addresses()
        .filter(pl.col("address_type_mnis_id") == "7")
        .filter(pl.col("address_1").is_not_null())
        .select(
            "mnis_id",
            "given_name",
            "family_name",
            "display_name",
            "address_type",
            pl.col("address_1").alias("url")))

    # Extract username: the last or penultimate token ignoring query strings
    accounts = accounts.with_columns(
        pl.col("url")
        .map_elements(extract_username, return_dtype=pl.String)
        .alias("username"))

    # Filter Twitter accounts for the given members
    return accounts.filter(pl.col("mnis_id").is_in(members["mnis_id"]))


# Instagram -------------------------------------------------------------------


def fetch_members_instagram(
        fetch_members: Callable,
        fetch_addresses: Callable,
        address_func: Callable | None = None,
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> pl.DataFrame:
    """Fetch Instagram accounts for Members."""

    # Fetch members for the given dates
    members = fetch_members(
        from_date=from_date,
        to_date=to_date,
        on_date=on_date).select("mnis_id")

    # Fetch Instagram accounts for members
    accounts = (
        fetch_addresses()
        .filter(pl.col("address_type_mnis_id") == "12")
        .filter(pl.col("address_1").is_not_null())
        .select(
            "mnis_id",
            "given_name",
            "family_name",
            "display_name",
            "address_type",
            pl.col("address_1").alias("url")))

    # Extract username: the last or penultimate token ignoring query strings
    accounts = accounts.with_columns(
        pl.col("url")
        .map_elements(extract_username, return_dtype=pl.String)
        .alias("username"))

    # Filter Instagram accounts for the given members
    return accounts.filter(pl.col("mnis_id").is_in(members["mnis_id"]))


# Facebook --------------------------------------------------------------------


def fetch_members_facebook(
        fetch_members: Callable,
        fetch_addresses: Callable,
        address_func: Callable | None = None,
        from_date: Date = None,
        to_date: Date = None,
        on_date: Date = None) -> pl.DataFrame:
    """Fetch Facebook accounts for Members."""

    # Fetch members for the given dates
    members = fetch_members(
        from_date=from_date,
        to_date=to_date,
        on_date=on_date).select("mnis_id")

    # Fetch Facebook accounts for members
    accounts = (
        fetch_addresses()
        .filter(pl.col("address_type_mnis_id") == "8")
        .filter(pl.col("address_1").is_not_null())
        .select(
            "mnis_id",
            "given_name",
            "family_name",
            "display_name",
            "address_type",
            pl.col("address_1").alias("url")))

    # Extract username: the last or penultimate token ignoring query strings
    accounts = accounts.with_columns(
        pl.col("url")
        .map_elements(extract_username, return_dtype=pl.String)
        .alias("username"))

    # Filter Facebook accounts for the given members
    return accounts.filter(pl.col("mnis_id").is_in(members["mnis_id"]))
