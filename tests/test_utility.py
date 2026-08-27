"""Tests for the utility functions"""

# Imports ---------------------------------------------------------------------

import datetime
import polars as pl
import pytest

from mnis.utility import cast_date
from mnis.utility import convert_date_column
from mnis.utility import create_query
from mnis.utility import extract_data_output
from mnis.utility import parse_date
from mnis.utility import scalar

# Constants -------------------------------------------------------------------

NIL = {
    "@xsi:nil": "true",
    "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"}

COLUMNS = ["mnis_id", "@Id", "Name", "IsUnpaid"]


# Helpers ---------------------------------------------------------------------


def member(mnis_id: str, entries) -> dict:
    """Build one member's data output from its entries."""
    return {"@Member_Id": mnis_id, "Posts": {"Post": entries}}


# Test create_query -----------------------------------------------------------


class TestCreateQuery:

    def test_builds_a_query_for_a_house_and_data_output(self):
        query = create_query("Commons", "BasicDetails")
        assert query.endswith("House=Commons|Membership=all/BasicDetails")


# Test scalar -----------------------------------------------------------------


class TestScalar:

    def test_converts_a_nil_object_to_none(self):
        assert scalar(NIL) is None

    def test_converts_any_object_to_none(self):
        assert scalar({}) is None

    @pytest.mark.parametrize("value", ["text", "", "1970-01-01", None])
    def test_returns_any_other_value_unchanged(self, value):
        assert scalar(value) == value


# Test extract_data_output ----------------------------------------------------


class TestExtractDataOutput:

    def test_extracts_one_row_for_each_entry(self):
        data = [member("1", [
            {"@Id": "9", "Name": "First"},
            {"@Id": "8", "Name": "Second"}])]
        result = extract_data_output(data, "Posts", "Post", COLUMNS)
        assert result.height == 2
        assert result["mnis_id"].to_list() == ["1", "1"]

    def test_treats_a_single_entry_given_as_an_object_as_one_row(self):
        data = [member("1", {"@Id": "9", "Name": "Only"})]
        result = extract_data_output(data, "Posts", "Post", COLUMNS)
        assert result.height == 1
        assert result["Name"].to_list() == ["Only"]

    def test_converts_nil_values_to_null(self):
        data = [member("1", {"@Id": "9", "Name": NIL})]
        result = extract_data_output(data, "Posts", "Post", COLUMNS)
        assert result["Name"].to_list() == [None]

    def test_returns_the_given_columns_in_the_given_order(self):
        data = [member("1", {"@Id": "9", "Name": "First"})]
        result = extract_data_output(data, "Posts", "Post", COLUMNS)
        assert result.columns == COLUMNS

    def test_ignores_fields_which_are_not_given_as_columns(self):
        data = [member("1", {"@Id": "9", "Name": "First", "Extra": "x"})]
        result = extract_data_output(data, "Posts", "Post", COLUMNS)
        assert "Extra" not in result.columns

    # The columns are given rather than taken from the data so that the
    # dataframe has the same structure whatever the API returns

    def test_includes_a_column_absent_from_every_entry(self):
        data = [
            member("1", {"@Id": "9", "Name": "First"}),
            member("2", {"@Id": "8", "Name": "Second"})]
        result = extract_data_output(data, "Posts", "Post", COLUMNS)
        assert result["IsUnpaid"].to_list() == [None, None]

    def test_includes_a_column_absent_from_only_some_entries(self):
        data = [
            member("1", {"@Id": "9", "Name": "First", "IsUnpaid": "True"}),
            member("2", {"@Id": "8", "Name": "Second"})]
        result = extract_data_output(data, "Posts", "Post", COLUMNS)
        assert result["IsUnpaid"].to_list() == ["True", None]

    def test_returns_the_given_columns_when_there_are_no_members(self):
        result = extract_data_output([], "Posts", "Post", COLUMNS)
        assert result.height == 0
        assert result.columns == COLUMNS

    def test_returns_string_columns(self):
        data = [member("1", {"@Id": "9", "Name": "First"})]
        result = extract_data_output(data, "Posts", "Post", COLUMNS)
        assert set(result.schema.values()) == {pl.String}


# Test parse_date -------------------------------------------------------------


class TestParseDate:

    def test_parses_an_iso_date(self):
        assert parse_date("2020-06-15") == datetime.date(2020, 6, 15)

    @pytest.mark.parametrize("given", [
        "2020-13-01",
        "2020-00-01",
        "2020-01-32",
        "2020-01-00",
        "20-01-01",
        "2020-1-1",
        "2020-01-01T00:00:00",
        ""])
    def test_rejects_an_invalid_date(self, given):
        with pytest.raises(ValueError):
            parse_date(given)


# Test cast_date --------------------------------------------------------------


class TestCastDate:

    def test_returns_none_for_none(self):
        assert cast_date(None) is None

    def test_casts_zero_to_the_epoch(self):
        assert cast_date(0) == datetime.date(1970, 1, 1)

    def test_casts_a_number_of_days_to_a_date(self):
        assert cast_date(1) == datetime.date(1970, 1, 2)

    @pytest.mark.parametrize("given", ["text", [1]])
    def test_rejects_a_value_which_is_not_a_number(self, given):
        with pytest.raises(ValueError):
            cast_date(given)


# Test convert_date_column ----------------------------------------------------


class TestConvertDateColumn:

    def frame(self, values: list) -> pl.DataFrame:
        """Return a dataframe with one string column of dates."""
        return pl.DataFrame({"d": values}, schema={"d": pl.String})

    def test_converts_a_date_string_to_a_date(self):
        result = convert_date_column(self.frame(["2020-06-15"]), "d")
        assert result["d"].to_list() == [datetime.date(2020, 6, 15)]

    def test_reads_the_date_from_the_start_of_a_timestamp(self):
        result = convert_date_column(self.frame(["2020-06-15T00:00:00"]), "d")
        assert result["d"].to_list() == [datetime.date(2020, 6, 15)]

    @pytest.mark.parametrize("given", [None, "", "not a date", "2020-13-40"])
    def test_converts_a_value_which_cannot_be_parsed_to_null(self, given):
        result = convert_date_column(self.frame([given]), "d")
        assert result["d"].to_list() == [None]

    def test_returns_a_date_column(self):
        result = convert_date_column(self.frame(["2020-06-15"]), "d")
        assert result.schema["d"] == pl.Date
