"""Tests for the shape of the package as a whole

These tests check the things which are easy to break without noticing: the
columns each function returns, the agreement between what the package
exports and what the README documents, and the agreement between the column
constants and the code which builds the rows.
"""

# Imports ---------------------------------------------------------------------

import json
import pathlib
import pytest
import re
import warnings

from conftest import SCHEMAS

import mnis

from mnis import constants
from mnis import raw_lords
from mnis import raw_mps

# Constants -------------------------------------------------------------------

README = pathlib.Path(__file__).parents[1] / "README.md"

NOT_DATA_FUNCTIONS = ["clear_cache", "get_timeout", "set_timeout"]

# get_general_elections_list returns a dict rather than a dataframe, so
# it has no schema to record

NOT_FRAME_FUNCTIONS = NOT_DATA_FUNCTIONS + ["get_general_elections_list"]

DATA_FUNCTIONS = [n for n in mnis.__all__ if n not in NOT_FRAME_FUNCTIONS]

RAW_FUNCTIONS = (
    [n for n in dir(raw_mps) if n.endswith("_raw")] +
    [n for n in dir(raw_lords) if n.endswith("_raw")])

# The column constants, with the function which builds the rows they
# describe, so that the two can be checked against each other

ROW_COLUMNS = [
    (constants.COLUMNS_MPS, raw_mps.fetch_mps_raw),
    (constants.COLUMNS_COMMONS_MEMBERSHIPS,
        raw_mps.fetch_commons_memberships_raw),
    (constants.COLUMNS_PARTY_MEMBERSHIPS,
        raw_mps.fetch_mps_party_memberships_raw),
    (constants.COLUMNS_OTHER_PARLIAMENTS,
        raw_mps.fetch_mps_other_parliaments_raw),
    (constants.COLUMNS_CONTESTED_ELECTIONS,
        raw_mps.fetch_mps_contested_elections_raw),
    (constants.COLUMNS_LORDS, raw_lords.fetch_lords_raw),
    (constants.COLUMNS_LORDS_MEMBERSHIPS,
        raw_lords.fetch_lords_memberships_raw)]

# fetch_lords_memberships_raw reads house_name to keep the Lords
# memberships and drops it once it has, so the column it builds is not
# in the dataframe it returns

DROPPED = {"fetch_lords_memberships_raw": ["house_name"]}


# Helpers ---------------------------------------------------------------------


def load_schemas() -> dict:
    """Load the recorded schemas."""
    return json.loads(SCHEMAS.read_text())


def documented() -> set:
    """Return the names of the functions documented in the README."""
    return set(re.findall(r"^__(\w+)__$", README.read_text(), re.M))


# Test the recorded schemas ---------------------------------------------------


class TestSchemas:

    def test_every_data_function_has_a_recorded_schema(self):
        schemas = load_schemas()
        assert set(DATA_FUNCTIONS) <= set(schemas)

    def test_every_raw_function_has_a_recorded_schema(self):
        schemas = load_schemas()
        assert set(RAW_FUNCTIONS) <= set(schemas)

    @pytest.mark.parametrize("name", DATA_FUNCTIONS)
    def test_a_data_function_returns_the_recorded_columns(self, api, name):
        expected = load_schemas()[name]
        result = getattr(mnis, name)()
        actual = [[c, str(t)] for c, t in result.schema.items()]
        assert actual == expected

    @pytest.mark.parametrize("name", RAW_FUNCTIONS)
    def test_a_raw_function_returns_the_recorded_columns(self, api, name):
        expected = load_schemas()[name]
        module = raw_mps if hasattr(raw_mps, name) else raw_lords
        result = getattr(module, name)()
        actual = [[c, str(t)] for c, t in result.schema.items()]
        assert actual == expected


# Test the column constants ---------------------------------------------------


class TestColumnConstants:

    # A column named in a constant but never built, or built but never
    # named, is a mistake in one place or the other. Polars drops a key
    # which is not in the schema without raising, so a column added to the
    # rows but not to the constant would otherwise disappear silently.

    @pytest.mark.parametrize(
        "columns, fetch", ROW_COLUMNS,
        ids=[f.__name__ for _, f in ROW_COLUMNS])
    def test_the_constant_names_every_column_the_rows_hold(
            self, api, columns, fetch):
        result = fetch()
        dropped = DROPPED.get(fetch.__name__, [])
        for column in columns:
            if column not in dropped:
                assert column in result.columns

    def test_every_column_constant_is_a_list_of_unique_names(self):
        names = [n for n in dir(constants) if n.startswith("COLUMNS_")]
        assert len(names) > 0
        for name in names:
            columns = getattr(constants, name)
            assert len(columns) == len(set(columns))

    def test_every_column_constant_names_the_member_id(self):
        names = [n for n in dir(constants) if n.startswith("COLUMNS_")]
        for name in names:
            assert "mnis_id" in getattr(constants, name)


# Test that the package does not use deprecated behaviour ---------------------


class TestDeprecations:

    # Filtering one dataframe by the ids in another is done throughout the
    # package. Passing a series to is_in without imploding it first is
    # ambiguous to polars and deprecated, so no function may do it.
    #
    # The warnings are recorded and counted rather than turned into errors
    # with the filterwarnings mark. Polars raises this particular warning
    # from inside its own code and does not let the exception escape, so
    # turning warnings into errors does not fail the test.

    @pytest.mark.parametrize("name", DATA_FUNCTIONS)
    def test_a_data_function_gives_no_deprecation_warning(self, api, name):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            getattr(mnis, name)()

        deprecations = [
            f"{w.filename}:{w.lineno} {w.message}"
            for w in caught
            if issubclass(w.category, DeprecationWarning)]

        assert deprecations == []


# Test the documented interface -----------------------------------------------


class TestInterface:

    def test_every_exported_name_exists(self):
        for name in mnis.__all__:
            assert hasattr(mnis, name)

    def test_every_exported_name_is_callable(self):
        for name in mnis.__all__:
            assert callable(getattr(mnis, name))

    def test_the_exported_names_are_sorted(self):
        assert mnis.__all__ == sorted(mnis.__all__)

    def test_every_exported_function_is_documented(self):
        assert set(mnis.__all__) <= documented()

    def test_every_documented_function_is_exported(self):
        assert documented() <= set(mnis.__all__)
