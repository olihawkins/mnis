"""Tests which call the live MNIS API

These tests are deselected by default. They check the package against the
API as it is now rather than against saved payloads, so they fail when MNIS
changes as well as when the package is wrong. Run them when you want to know
whether the API has moved:

    pytest -m live

They assert what should hold whatever the data says. They do not assert
counts, which change continually, so a count is only ever reported.
"""

# Imports ---------------------------------------------------------------------

import polars as pl
import pytest

import mnis

from mnis import constants
from mnis import utility
from mnis.constants import HOUSE_COMMONS
from mnis.constants import HOUSE_LORDS

# Constants -------------------------------------------------------------------

pytestmark = pytest.mark.live

NOT_DATA_FUNCTIONS = ["clear_cache", "get_timeout", "set_timeout"]

DATA_FUNCTIONS = [n for n in mnis.__all__ if n not in NOT_DATA_FUNCTIONS]

# Each data output handled by extract_data_output, with the constant naming
# the columns the package takes from it

DECLARED_COLUMNS = [
    (HOUSE_COMMONS, "GovernmentPosts", "GovernmentPost",
        constants.COLUMNS_POSTS),
    (HOUSE_COMMONS, "OppositionPosts", "OppositionPost",
        constants.COLUMNS_POSTS),
    (HOUSE_COMMONS, "ParliamentaryPosts", "ParliamentaryPost",
        constants.COLUMNS_POSTS),
    (HOUSE_COMMONS, "MaidenSpeeches", "MaidenSpeech",
        constants.COLUMNS_MAIDEN_SPEECHES),
    (HOUSE_COMMONS, "Addresses", "Address",
        constants.COLUMNS_ADDRESSES),
    (HOUSE_LORDS, "GovernmentPosts", "GovernmentPost",
        constants.COLUMNS_POSTS),
    (HOUSE_LORDS, "OppositionPosts", "OppositionPost",
        constants.COLUMNS_POSTS),
    (HOUSE_LORDS, "ParliamentaryPosts", "ParliamentaryPost",
        constants.COLUMNS_POSTS),
    (HOUSE_LORDS, "MaidenSpeeches", "MaidenSpeech",
        constants.COLUMNS_MAIDEN_SPEECHES),
    (HOUSE_LORDS, "Addresses", "Address",
        constants.COLUMNS_ADDRESSES)]

DECLARED_IDS = [f"{h.lower()}_{o.lower()}" for h, o, _, _ in DECLARED_COLUMNS]


# Helpers ---------------------------------------------------------------------


def fields(house: str, data_output: str, key: str) -> set:
    """Return every field name the API returns for a data output."""
    data = utility.fetch_query_data(house=house, data_output=data_output)
    found = set()

    for member in data:
        section = member.get(data_output)
        if section is None:
            continue
        entries = section[key]
        for entry in entries if isinstance(entries, list) else [entries]:
            found |= set(entry.keys())

    return found


# Test that every function works against the live API -------------------------


class TestLiveFunctions:

    @pytest.mark.parametrize("name", DATA_FUNCTIONS)
    def test_the_function_returns_data(self, name):
        result = getattr(mnis, name)()
        assert result is not None

    @pytest.mark.parametrize("name", DATA_FUNCTIONS)
    def test_the_function_returns_the_recorded_columns(self, name):
        import json
        from conftest import SCHEMAS
        schemas = json.loads(SCHEMAS.read_text())
        if name not in schemas:
            pytest.skip(f"{name} does not return a dataframe")
        result = getattr(mnis, name)()
        actual = [[c, str(t)] for c, t in result.schema.items()]
        assert actual == schemas[name]


# Test the data the API returns -----------------------------------------------


class TestLiveData:

    def test_members_are_returned(self):
        assert mnis.fetch_mps().height > 0
        assert mnis.fetch_lords().height > 0

    def test_each_member_appears_once(self):
        mps = mnis.fetch_mps()
        assert mps["mnis_id"].n_unique() == mps.height

    def test_every_member_has_a_name(self):
        mps = mnis.fetch_mps()
        assert mps["display_name"].null_count() == 0

    def test_every_membership_belongs_to_a_member(self):
        members = set(mnis.fetch_mps()["mnis_id"].to_list())
        memberships = mnis.fetch_commons_memberships()
        assert set(memberships["mnis_id"].to_list()) <= members

    def test_every_party_membership_belongs_to_a_member(self):
        members = set(mnis.fetch_mps()["mnis_id"].to_list())
        parties = mnis.fetch_mps_party_memberships(while_mp=False)
        assert set(parties["mnis_id"].to_list()) <= members

    def test_memberships_do_not_end_before_they_start(self):
        memberships = mnis.fetch_commons_memberships()
        assert memberships.filter(
            pl.col("seat_incumbency_end_date").is_not_null() &
            (pl.col("seat_incumbency_end_date") <
                pl.col("seat_incumbency_start_date"))).height == 0

    def test_some_members_are_currently_serving(self):
        memberships = mnis.fetch_commons_memberships()
        assert memberships.filter(
            pl.col("seat_incumbency_end_date").is_null()).height > 0


# Test the columns the package declares against the API -----------------------


class TestLiveColumns:

    # The package names the columns it takes from each data output rather
    # than reading them from the response. A column which the API no longer
    # returns is a change the package has to be told about.

    @pytest.mark.parametrize(
        "house, data_output, key, columns",
        DECLARED_COLUMNS, ids=DECLARED_IDS)
    def test_every_declared_column_is_returned_by_the_api(
            self, house, data_output, key, columns):
        found = fields(house, data_output, key) | {"mnis_id"}
        missing = [c for c in columns if c not in found]
        assert missing == []

    # A field the API returns which the package does not declare is not an
    # error, but it is worth knowing about, so it is reported rather than
    # asserted against.

    @pytest.mark.parametrize(
        "house, data_output, key, columns",
        DECLARED_COLUMNS, ids=DECLARED_IDS)
    def test_report_fields_the_package_does_not_use(
            self, house, data_output, key, columns):
        found = fields(house, data_output, key)
        unused = sorted(f for f in found if f not in columns)
        print(f"\n{house} {data_output} fields not used: {unused}")


# Test fetching over HTTP -----------------------------------------------------


class TestLiveRequests:

    def test_the_api_answers_a_query(self):
        data = utility.fetch_query_data(
            house=HOUSE_COMMONS, data_output="BasicDetails")
        assert len(data) > 0
        assert "@Member_Id" in data[0]

    def test_a_query_for_a_data_output_which_does_not_exist_raises(self):
        with pytest.raises(RuntimeError):
            utility.fetch_query_data(
                house=HOUSE_COMMONS, data_output="NoSuchDataOutput")
