"""Functions for downloading raw query data"""

import polars as pl

from polars import DataFrame

from mnis.cache import cache
from mnis.constants import CACHE_COMMONS_MEMBERSHIPS_RAW
from mnis.constants import CACHE_COMMONS_PARTY_MEMBERSHIPS_RAW
from mnis.constants import CACHE_MPS_ADDRESSES_RAW
from mnis.constants import CACHE_MPS_CONTESTED_ELECTIONS_RAW
from mnis.constants import CACHE_MPS_GOVERNMENT_ROLES_RAW
from mnis.constants import CACHE_MPS_MAIDEN_SPEECHES_RAW
from mnis.constants import CACHE_MPS_OPPOSITION_ROLES_RAW
from mnis.constants import CACHE_MPS_OTHER_PARLIAMENTS_RAW
from mnis.constants import CACHE_MPS_PARLIAMENTARY_ROLES_RAW
from mnis.constants import CACHE_MPS_RAW
from mnis.constants import COLUMNS_ADDRESSES
from mnis.constants import COLUMNS_COMMONS_MEMBERSHIPS
from mnis.constants import COLUMNS_CONTESTED_ELECTIONS
from mnis.constants import COLUMNS_MAIDEN_SPEECHES
from mnis.constants import COLUMNS_MPS
from mnis.constants import COLUMNS_OTHER_PARLIAMENTS
from mnis.constants import COLUMNS_PARTY_MEMBERSHIPS
from mnis.constants import COLUMNS_POSTS
from mnis.constants import HOUSE_COMMONS
from mnis import utility
from mnis.utility import convert_date_column
from mnis.utility import extract_data_output
from mnis.utility import process_mps_output
from mnis.utility import scalar

# Raw MP queries --------------------------------------------------------------

def fetch_mps_raw() -> DataFrame:
    """Fetch key details: MPs."""

    # Fetch raw
    mps_raw = utility.fetch_query_data(
        house=HOUSE_COMMONS, data_output="BasicDetails")

    # Extract data
    rows = [
        {
            "mnis_id": member["@Member_Id"],
            "given_name": scalar(member["BasicDetails"].get("GivenForename")),
            "family_name": scalar(member["BasicDetails"].get("GivenSurname")),
            "display_name": scalar(member.get("DisplayAs")),
            "full_title": scalar(member.get("FullTitle")),
            "current_status": scalar(member["CurrentStatus"].get("Name")),
            "current_status_reason": scalar(
                member["CurrentStatus"].get("Reason")),
            "gender": scalar(member.get("Gender")),
            "date_of_death": scalar(member.get("DateOfDeath")),
        }
        for member in mps_raw
    ]

    # Tidy
    mps = pl.from_dicts(
        rows,
        schema={column: pl.String for column in COLUMNS_MPS})
    mps = convert_date_column(mps, "date_of_death")

    # Cache
    cache[CACHE_MPS_RAW] = mps

    # Return
    return mps


def fetch_commons_memberships_raw() -> DataFrame:
    """Fetch memberships: MPs."""

    # Fetch raw
    memberships_raw = utility.fetch_query_data(
        house=HOUSE_COMMONS, data_output="Constituencies")

    # Remove NULL
    memberships_raw = [
        member for member in memberships_raw
        if member.get("Constituencies") is not None
    ]

    # Extract data
    rows = []
    for member in memberships_raw:
        mnis_id = member["@Member_Id"]
        entries = member["Constituencies"]["Constituency"]
        if isinstance(entries, dict):
            entries = [entries]
        for entry in entries:
            rows.append({
                "constituency_mnis_id": scalar(entry.get("@Id")),
                "constituency_name": scalar(entry.get("Name")),
                "seat_incumbency_start_date": scalar(entry.get("StartDate")),
                "seat_incumbency_end_date": scalar(entry.get("EndDate")),
                "mnis_id": mnis_id,
            })

    # Tidy
    memberships = pl.from_dicts(
        rows,
        schema={column: pl.String for column in COLUMNS_COMMONS_MEMBERSHIPS})
    memberships = convert_date_column(
        memberships, "seat_incumbency_start_date")
    memberships = convert_date_column(memberships, "seat_incumbency_end_date")

    # Combine
    memberships = process_mps_output(memberships)

    # Cache
    cache[CACHE_COMMONS_MEMBERSHIPS_RAW] = memberships

    # Return
    return memberships


def fetch_mps_party_memberships_raw() -> DataFrame:
    """Fetch party memberships: MPs."""

    # Fetch raw party membership data
    party_memberships_raw = utility.fetch_query_data(
        house=HOUSE_COMMONS, data_output="Parties")

    # Remove NULL
    party_memberships_raw = [
        member for member in party_memberships_raw
        if member.get("Parties") is not None
    ]

    # Extract data output for each MP
    rows = []
    for member in party_memberships_raw:
        mnis_id = member["@Member_Id"]
        entries = member["Parties"]["Party"]
        if isinstance(entries, dict):
            entries = [entries]
        for entry in entries:
            rows.append({
                "party_mnis_id": scalar(entry.get("@Id")),
                "party_name": scalar(entry.get("Name")),
                "party_membership_start_date": scalar(entry.get("StartDate")),
                "party_membership_end_date": scalar(entry.get("EndDate")),
                "mnis_id": mnis_id,
            })

    # Tidy
    memberships = pl.from_dicts(
        rows,
        schema={column: pl.String for column in COLUMNS_PARTY_MEMBERSHIPS})
    memberships = convert_date_column(
        memberships, "party_membership_start_date")
    memberships = convert_date_column(
        memberships, "party_membership_end_date")

    # Combine
    memberships = process_mps_output(memberships)

    # Cache memberships
    cache[CACHE_COMMONS_PARTY_MEMBERSHIPS_RAW] = memberships

    # Return
    return memberships


def fetch_mps_other_parliaments_raw() -> DataFrame:
    """Fetch other parliaments: MPs."""

    # Fetch raw
    other_parliaments_raw = utility.fetch_query_data(
        house=HOUSE_COMMONS, data_output="OtherParliaments")

    # Remove NULL
    other_parliaments_raw = [
        member for member in other_parliaments_raw
        if member.get("OtherParliaments") is not None
    ]

    # Extract data
    rows = []
    for member in other_parliaments_raw:
        mnis_id = member["@Member_Id"]
        entries = member["OtherParliaments"]["OtherParliament"]
        if isinstance(entries, dict):
            entries = [entries]
        for entry in entries:
            rows.append({
                "other_parliaments_mnis_id": scalar(entry.get("@Id")),
                "other_parliaments_name": scalar(entry.get("Name")),
                "other_parliaments_incumbency_start_date": scalar(
                    entry.get("StartDate")),
                "other_parliaments_incumbency_end_date": scalar(
                    entry.get("EndDate")),
                "mnis_id": mnis_id,
            })

    # Tidy
    other_parliaments = pl.from_dicts(
        rows,
        schema={column: pl.String for column in COLUMNS_OTHER_PARLIAMENTS})
    other_parliaments = convert_date_column(
        other_parliaments, "other_parliaments_incumbency_start_date")
    other_parliaments = convert_date_column(
        other_parliaments, "other_parliaments_incumbency_end_date")

    # Combine
    other_parliaments = process_mps_output(other_parliaments)

    # Cache
    cache[CACHE_MPS_OTHER_PARLIAMENTS_RAW] = other_parliaments

    # Return
    return other_parliaments


def fetch_mps_contested_elections_raw() -> DataFrame:
    """Fetch contested elections: MPs."""

    # Fetch raw
    contested_elections_raw = utility.fetch_query_data(
        house=HOUSE_COMMONS, data_output="ElectionsContested")

    # Remove NULL
    contested_elections_raw = [
        member for member in contested_elections_raw
        if member.get("ElectionsContested") is not None
    ]

    # Extract data
    rows = []
    for member in contested_elections_raw:
        mnis_id = member["@Member_Id"]
        entries = member["ElectionsContested"]["ElectionContested"]
        if isinstance(entries, dict):
            entries = [entries]
        for entry in entries:
            rows.append({
                "contested_election_mnis_id": scalar(
                    entry["Election"].get("@Id")),
                "contested_election_name": scalar(
                    entry["Election"].get("Name")),
                "contested_election_date": scalar(
                    entry["Election"].get("Date")),
                "contested_election_type": scalar(
                    entry["Election"].get("Type")),
                "contested_election_constituency": scalar(
                    entry.get("Constituency")),
                "mnis_id": mnis_id,
            })

    # Tidy
    contested_elections = pl.from_dicts(
        rows,
        schema={column: pl.String for column in COLUMNS_CONTESTED_ELECTIONS})
    contested_elections = convert_date_column(
        contested_elections, "contested_election_date")

    # Combine
    contested_elections = process_mps_output(contested_elections)

    # Cache
    cache[CACHE_MPS_CONTESTED_ELECTIONS_RAW] = contested_elections

    # Return
    return contested_elections


def fetch_mps_government_roles_raw() -> DataFrame:
    """Fetch government roles: MPs."""

    # Fetch raw
    government_roles_raw = utility.fetch_query_data(
        house=HOUSE_COMMONS, data_output="GovernmentPosts")

    # Remove NULL
    government_roles_raw = [
        member for member in government_roles_raw
        if member.get("GovernmentPosts") is not None
    ]

    # Extract data
    government_roles = extract_data_output(
        government_roles_raw,
        "GovernmentPosts",
        "GovernmentPost",
        COLUMNS_POSTS).select(
        "mnis_id",
        pl.col("@Id").alias("government_role_mnis_id"),
        pl.col("Name").alias("government_role_name"),
        pl.col("StartDate").alias("government_role_incumbency_start_date"),
        pl.col("EndDate").alias("government_role_incumbency_end_date"),
        pl.col("IsUnpaid").alias("government_role_unpaid"))

    # Tidy
    government_roles = convert_date_column(
        government_roles, "government_role_incumbency_start_date")
    government_roles = convert_date_column(
        government_roles, "government_role_incumbency_end_date")

    # Combine
    government_roles = process_mps_output(government_roles)

    # Cache
    cache[CACHE_MPS_GOVERNMENT_ROLES_RAW] = government_roles

    # Return
    return government_roles


def fetch_mps_opposition_roles_raw() -> DataFrame:
    """Fetch opposition roles: MPs."""

    # Fetch raw
    opposition_roles_raw = utility.fetch_query_data(
        house=HOUSE_COMMONS, data_output="OppositionPosts")

    # Remove NULL
    opposition_roles_raw = [
        member for member in opposition_roles_raw
        if member.get("OppositionPosts") is not None
    ]

    # Extract data
    opposition_roles = extract_data_output(
        opposition_roles_raw,
        "OppositionPosts",
        "OppositionPost",
        COLUMNS_POSTS).select(
        "mnis_id",
        pl.col("@Id").alias("opposition_role_mnis_id"),
        pl.col("Name").alias("opposition_role_name"),
        pl.col("StartDate").alias("opposition_role_incumbency_start_date"),
        pl.col("EndDate").alias("opposition_role_incumbency_end_date"),
        pl.col("IsUnpaid").alias("opposition_role_unpaid"))

    # Tidy
    opposition_roles = convert_date_column(
        opposition_roles, "opposition_role_incumbency_start_date")
    opposition_roles = convert_date_column(
        opposition_roles, "opposition_role_incumbency_end_date")

    # Combine
    opposition_roles = process_mps_output(opposition_roles)

    # Cache
    cache[CACHE_MPS_OPPOSITION_ROLES_RAW] = opposition_roles

    # Return
    return opposition_roles


def fetch_mps_parliamentary_roles_raw() -> DataFrame:
    """Fetch parliamentary roles: MPs."""

    # Fetch raw
    parliamentary_roles_raw = utility.fetch_query_data(
        house=HOUSE_COMMONS, data_output="ParliamentaryPosts")

    # Remove NULL
    parliamentary_roles_raw = [
        member for member in parliamentary_roles_raw
        if member.get("ParliamentaryPosts") is not None
    ]

    # Extract data
    parliamentary_roles = extract_data_output(
        parliamentary_roles_raw,
        "ParliamentaryPosts",
        "ParliamentaryPost",
        COLUMNS_POSTS).select(
        "mnis_id",
        pl.col("@Id").alias("parliamentary_role_mnis_id"),
        pl.col("Name").alias("parliamentary_role_name"),
        pl.col("StartDate").alias("parliamentary_role_incumbency_start_date"),
        pl.col("EndDate").alias("parliamentary_role_incumbency_end_date"),
        pl.col("IsUnpaid").alias("parliamentary_role_unpaid"))

    # Tidy
    parliamentary_roles = convert_date_column(
        parliamentary_roles, "parliamentary_role_incumbency_start_date")
    parliamentary_roles = convert_date_column(
        parliamentary_roles, "parliamentary_role_incumbency_end_date")

    # Combine
    parliamentary_roles = process_mps_output(parliamentary_roles)

    # Cache
    cache[CACHE_MPS_PARLIAMENTARY_ROLES_RAW] = parliamentary_roles

    # Return
    return parliamentary_roles


def fetch_mps_maiden_speeches_raw() -> DataFrame:
    """Fetch maiden speeches: MPs."""

    # Fetch raw
    maiden_speeches_raw = utility.fetch_query_data(
        house=HOUSE_COMMONS, data_output="MaidenSpeeches")

    # Remove NULL
    maiden_speeches_raw = [
        member for member in maiden_speeches_raw
        if member.get("MaidenSpeeches") is not None
    ]

    # Extract data
    maiden_speeches = extract_data_output(
        maiden_speeches_raw,
        "MaidenSpeeches",
        "MaidenSpeech",
        COLUMNS_MAIDEN_SPEECHES).select(
        "mnis_id",
        pl.col("House").alias("maiden_speech_house"),
        pl.col("SpeechDate").alias("maiden_speech_date"),
        pl.col("Hansard").alias("maiden_speech_hansard_reference"),
        pl.col("Subject").alias("maiden_speech_subject"))

    # Tidy
    maiden_speeches = convert_date_column(
        maiden_speeches, "maiden_speech_date")
    maiden_speeches = maiden_speeches.filter(
        pl.col("maiden_speech_house") == "Commons")

    # Combine
    maiden_speeches = process_mps_output(maiden_speeches)

    # Cache
    cache[CACHE_MPS_MAIDEN_SPEECHES_RAW] = maiden_speeches

    # Return
    return maiden_speeches


def fetch_mps_addresses_raw() -> DataFrame:
    """Fetch addresses: MPs."""

    # Fetch raw
    addresses_raw = utility.fetch_query_data(
        house=HOUSE_COMMONS, data_output="Addresses")

    # Remove NULL
    addresses_raw = [
        member for member in addresses_raw
        if member.get("Addresses") is not None
    ]

    # Extract data
    addresses = extract_data_output(
        addresses_raw,
        "Addresses",
        "Address",
        COLUMNS_ADDRESSES).select(
        "mnis_id",
        pl.col("@Type_Id").alias("address_type_mnis_id"),
        pl.col("Type").alias("address_type"),
        pl.col("IsPreferred").alias("address_is_preferred"),
        pl.col("IsPhysical").alias("address_is_physical"),
        pl.col("Note").alias("address_note"),
        pl.col("Address1").alias("address_1"),
        pl.col("Address2").alias("address_2"),
        pl.col("Address3").alias("address_3"),
        pl.col("Address4").alias("address_4"),
        pl.col("Address5").alias("address_5"),
        pl.col("Postcode").alias("postcode"),
        pl.col("Phone").alias("phone"),
        pl.col("Fax").alias("fax"),
        pl.col("Email").alias("email"),
        pl.col("OtherAddress").alias("address_other"))

    # Tidy
    as_logical = {
        "T": True, "TRUE": True, "true": True, "True": True,
        "F": False, "FALSE": False, "false": False, "False": False}
    addresses = addresses.with_columns(
        pl.col("address_is_preferred").replace_strict(
            as_logical, default=None, return_dtype=pl.Boolean),
        pl.col("address_is_physical").replace_strict(
            as_logical, default=None, return_dtype=pl.Boolean))

    # Combine
    addresses = process_mps_output(addresses)

    # Cache
    cache[CACHE_MPS_ADDRESSES_RAW] = addresses

    # Return
    return addresses
