"""Tests for the raw fetch functions against awkward API responses

The raw fetch functions turn one data output into a dataframe. These tests
check they cope with the shapes the API can return: a member with no
entries at all, a member with one entry given as a bare object rather than
a list, a field which is missing from every entry, and a response with no
members in it.
"""

# Imports ---------------------------------------------------------------------

import polars as pl
import pytest

from conftest import load_payload

from mnis import raw_lords
from mnis import raw_mps
from mnis.constants import HOUSE_COMMONS
from mnis.constants import HOUSE_LORDS

# Constants -------------------------------------------------------------------

# Each raw fetch function, with the House and data output it reads, and the
# key of the entries within that data output

EXTRACTORS = [
    (raw_mps.fetch_mps_raw,
        HOUSE_COMMONS, "BasicDetails", None),
    (raw_mps.fetch_commons_memberships_raw,
        HOUSE_COMMONS, "Constituencies", "Constituency"),
    (raw_mps.fetch_mps_party_memberships_raw,
        HOUSE_COMMONS, "Parties", "Party"),
    (raw_mps.fetch_mps_other_parliaments_raw,
        HOUSE_COMMONS, "OtherParliaments", "OtherParliament"),
    (raw_mps.fetch_mps_contested_elections_raw,
        HOUSE_COMMONS, "ElectionsContested", "ElectionContested"),
    (raw_mps.fetch_mps_government_roles_raw,
        HOUSE_COMMONS, "GovernmentPosts", "GovernmentPost"),
    (raw_mps.fetch_mps_opposition_roles_raw,
        HOUSE_COMMONS, "OppositionPosts", "OppositionPost"),
    (raw_mps.fetch_mps_parliamentary_roles_raw,
        HOUSE_COMMONS, "ParliamentaryPosts", "ParliamentaryPost"),
    (raw_mps.fetch_mps_maiden_speeches_raw,
        HOUSE_COMMONS, "MaidenSpeeches", "MaidenSpeech"),
    (raw_mps.fetch_mps_addresses_raw,
        HOUSE_COMMONS, "Addresses", "Address"),
    (raw_lords.fetch_lords_raw,
        HOUSE_LORDS, "BasicDetails", None),
    (raw_lords.fetch_lords_memberships_raw,
        HOUSE_LORDS, "HouseMemberships", "HouseMembership"),
    (raw_lords.fetch_lords_party_memberships_raw,
        HOUSE_LORDS, "Parties", "Party"),
    (raw_lords.fetch_lords_other_parliaments_raw,
        HOUSE_LORDS, "OtherParliaments", "OtherParliament"),
    (raw_lords.fetch_lords_contested_elections_raw,
        HOUSE_LORDS, "ElectionsContested", "ElectionContested"),
    (raw_lords.fetch_lords_government_roles_raw,
        HOUSE_LORDS, "GovernmentPosts", "GovernmentPost"),
    (raw_lords.fetch_lords_opposition_roles_raw,
        HOUSE_LORDS, "OppositionPosts", "OppositionPost"),
    (raw_lords.fetch_lords_parliamentary_roles_raw,
        HOUSE_LORDS, "ParliamentaryPosts", "ParliamentaryPost"),
    (raw_lords.fetch_lords_maiden_speeches_raw,
        HOUSE_LORDS, "MaidenSpeeches", "MaidenSpeech"),
    (raw_lords.fetch_lords_addresses_raw,
        HOUSE_LORDS, "Addresses", "Address")]

# The functions which read a data output with entries nested inside it

NESTED = [e for e in EXTRACTORS if e[3] is not None]

IDS = [f"{e[1].lower()}_{e[2].lower()}" for e in EXTRACTORS]
NESTED_IDS = [f"{e[1].lower()}_{e[2].lower()}" for e in NESTED]


# Helpers ---------------------------------------------------------------------


def entries(member: dict, section: str, key: str) -> list[dict]:
    """Return a member's entries in a section as a list."""
    value = member.get(section)
    if value is None:
        return []
    found = value[key]
    return found if isinstance(found, list) else [found]


# Test the raw fetch functions ------------------------------------------------


@pytest.mark.parametrize(
    "fetch, house, data_output, key", EXTRACTORS, ids=IDS)
class TestEveryExtractor:

    def test_returns_a_dataframe_from_the_saved_payload(
            self, api, fetch, house, data_output, key):
        assert isinstance(fetch(), pl.DataFrame)

    def test_returns_the_expected_columns_when_there_are_no_members(
            self, api, fetch, house, data_output, key):
        columns = fetch().columns
        api.set_handler(lambda house, data_output: [])
        assert fetch().columns == columns

    def test_returns_no_rows_when_there_are_no_members(
            self, api, fetch, house, data_output, key):
        api.set_handler(lambda house, data_output: [])
        assert fetch().height == 0

    def test_every_row_has_a_member_id(
            self, api, fetch, house, data_output, key):
        result = fetch()
        assert result["mnis_id"].null_count() == 0


@pytest.mark.parametrize(
    "fetch, house, data_output, key", NESTED, ids=NESTED_IDS)
class TestNestedExtractor:

    def test_ignores_a_member_whose_section_is_null(
            self, api, fetch, house, data_output, key):
        payload = load_payload(house, data_output)
        for member in payload:
            member[data_output] = None
        api.set_data(house, data_output, payload)
        assert fetch().height == 0

    def test_keeps_the_members_whose_section_is_not_null(
            self, api, fetch, house, data_output, key):
        payload = load_payload(house, data_output)
        others = {m["@Member_Id"] for m in payload[1:]}
        payload[0][data_output] = None
        api.set_data(house, data_output, payload)

        result = fetch()
        found = set(result["mnis_id"].to_list())
        assert payload[0]["@Member_Id"] not in found
        assert found <= others

    # The API returns a bare object rather than a list when a member has
    # only one entry. Both shapes have to produce the same rows.

    def test_reads_a_single_entry_given_as_an_object(
            self, api, fetch, house, data_output, key):
        payload = load_payload(house, data_output)

        # Keep the first entry of each member, given as a bare object
        objects = [dict(member) for member in payload]
        for member in objects:
            found = entries(member, data_output, key)
            member[data_output] = {key: found[0]} if found else None

        # Keep the same entry, given as a list of one
        lists = [dict(member) for member in payload]
        for member in lists:
            found = entries(member, data_output, key)
            member[data_output] = {key: [found[0]]} if found else None

        api.set_data(house, data_output, objects)
        from_object = fetch()
        api.set_data(house, data_output, lists)
        from_list = fetch()

        assert from_object.equals(from_list)
