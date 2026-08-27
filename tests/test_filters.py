"""Tests for the filter functions"""

# Imports ---------------------------------------------------------------------

import datetime
import polars as pl
import pytest

from mnis.filters import filter_dates
from mnis.filters import filter_memberships
from mnis.filters import handle_date

# Constants -------------------------------------------------------------------

TARGET_SCHEMA = {
    "mnis_id": pl.String,
    "role_id": pl.String,
    "start": pl.Date,
    "end": pl.Date}

FILTER_SCHEMA = {
    "mnis_id": pl.String,
    "fstart": pl.Date,
    "fend": pl.Date}


# Helpers ---------------------------------------------------------------------


def date(iso: str | None) -> datetime.date | None:
    """Return a date from an ISO 8601 string, or None."""
    return None if iso is None else datetime.date.fromisoformat(iso)


def target(rows: list[tuple]) -> pl.DataFrame:
    """Build a dataframe of target memberships from tuples."""
    return pl.DataFrame(
        [(m, r, date(s), date(e)) for m, r, s, e in rows],
        schema=TARGET_SCHEMA,
        orient="row")


def filters(rows: list[tuple]) -> pl.DataFrame:
    """Build a dataframe of filter memberships from tuples."""
    return pl.DataFrame(
        [(m, date(s), date(e)) for m, s, e in rows],
        schema=FILTER_SCHEMA,
        orient="row")


def filter_target(tm: pl.DataFrame, fm: pl.DataFrame) -> pl.DataFrame:
    """Filter target memberships with filter memberships."""
    return filter_memberships(
        tm, fm, "start", "end", "fstart", "fend", "mnis_id")


# Test handle_date ------------------------------------------------------------


class TestHandleDate:

    def test_returns_none_for_none(self):
        assert handle_date(None) is None

    def test_returns_a_date_unchanged(self):
        given = datetime.date(2020, 1, 1)
        assert handle_date(given) == given

    def test_parses_an_iso_string(self):
        assert handle_date("2020-01-01") == datetime.date(2020, 1, 1)

    @pytest.mark.parametrize("given", [
        "2020-13-01",
        "2020-01-32",
        "01-01-2020",
        "2020/01/01",
        "not a date",
        ""])
    def test_rejects_an_invalid_date_string(self, given):
        with pytest.raises(ValueError):
            handle_date(given)

    @pytest.mark.parametrize("given", [20200101, 2020.0, [2020, 1, 1], {}])
    def test_rejects_a_value_which_is_not_a_date(self, given):
        with pytest.raises(ValueError):
            handle_date(given)


# Test filter_dates -----------------------------------------------------------


class TestFilterDates:

    def frame(self) -> pl.DataFrame:
        """Return a dataframe with one activity in each of three years."""
        return pl.DataFrame(
            [
                (date("2000-01-01"), date("2000-12-31")),
                (date("2010-01-01"), date("2010-12-31")),
                (date("2020-01-01"), None)],
            schema={"s": pl.Date, "e": pl.Date},
            orient="row")

    def test_returns_all_rows_when_no_dates_given(self):
        assert filter_dates(self.frame(), "s", "e").height == 3

    def test_from_date_keeps_activity_which_is_still_open(self):
        result = filter_dates(self.frame(), "s", "e", from_date="2015-01-01")
        assert result["s"].to_list() == [date("2020-01-01")]

    def test_to_date_excludes_activity_which_began_later(self):
        result = filter_dates(self.frame(), "s", "e", to_date="2005-01-01")
        assert result["s"].to_list() == [date("2000-01-01")]

    def test_filtering_is_inclusive_of_the_boundary_dates(self):
        result = filter_dates(
            self.frame(), "s", "e",
            from_date="2010-12-31", to_date="2010-12-31")
        assert result["s"].to_list() == [date("2010-01-01")]

    def test_accepts_dates_as_well_as_strings(self):
        result = filter_dates(
            self.frame(), "s", "e", from_date=datetime.date(2015, 1, 1))
        assert result.height == 1

    def test_rejects_a_to_date_before_the_from_date(self):
        with pytest.raises(ValueError):
            filter_dates(
                self.frame(), "s", "e",
                from_date="2020-01-01", to_date="2010-01-01")

    @pytest.mark.parametrize("start_col, end_col", [
        ("nope", "e"),
        ("s", "nope")])
    def test_rejects_a_column_which_does_not_exist(self, start_col, end_col):
        with pytest.raises(ValueError):
            filter_dates(
                self.frame(), start_col, end_col, from_date="2020-01-01")

    # An empty dataframe used to be returned before the arguments were
    # checked, so an invalid argument passed silently

    def test_checks_arguments_when_the_dataframe_is_empty(self):
        empty = self.frame().head(0)
        with pytest.raises(ValueError):
            filter_dates(empty, "s", "e", from_date="not a date")

    def test_checks_date_order_when_the_dataframe_is_empty(self):
        empty = self.frame().head(0)
        with pytest.raises(ValueError):
            filter_dates(
                empty, "s", "e", from_date="2020-01-01", to_date="2010-01-01")

    def test_checks_columns_when_the_dataframe_is_empty(self):
        empty = self.frame().head(0)
        with pytest.raises(ValueError):
            filter_dates(empty, "nope", "e", from_date="2020-01-01")

    def test_returns_an_empty_dataframe_when_the_arguments_are_valid(self):
        empty = self.frame().head(0)
        result = filter_dates(empty, "s", "e", from_date="2020-01-01")
        assert result.height == 0


# Test filter_memberships -----------------------------------------------------


class TestFilterMemberships:

    def test_keeps_a_membership_which_intersects(self):
        tm = target([("1", "a", "2020-01-01", "2021-01-01")])
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        assert filter_target(tm, fm).height == 1

    def test_excludes_a_membership_which_ended_before(self):
        tm = target([("1", "a", "2010-01-01", "2011-01-01")])
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        assert filter_target(tm, fm).height == 0

    def test_excludes_a_membership_which_began_after(self):
        tm = target([("1", "a", "2030-01-01", "2031-01-01")])
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        assert filter_target(tm, fm).height == 0

    def test_keeps_an_open_membership_which_intersects(self):
        tm = target([("1", "a", "2020-01-01", None)])
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        assert filter_target(tm, fm).height == 1

    def test_keeps_a_membership_within_an_open_filter_membership(self):
        tm = target([("1", "a", "2020-01-01", "2021-01-01")])
        fm = filters([("1", "2019-01-01", None)])
        assert filter_target(tm, fm).height == 1

    def test_intersection_is_inclusive_of_a_single_shared_day(self):
        tm = target([("1", "a", "2019-01-01", "2020-01-01")])
        fm = filters([("1", "2020-01-01", "2021-01-01")])
        assert filter_target(tm, fm).height == 1

    def test_preserves_the_columns_of_the_target_memberships(self):
        tm = target([("1", "a", "2020-01-01", "2021-01-01")])
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        assert filter_target(tm, fm).columns == tm.columns

    # An entity with no filter memberships has no period of membership for
    # its target memberships to fall within, so all of them are excluded

    def test_excludes_memberships_of_an_entity_with_no_filters(self):
        tm = target([
            ("1", "a", "2020-01-01", "2021-01-01"),
            ("2", "b", "2020-01-01", "2021-01-01")])
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        assert filter_target(tm, fm)["mnis_id"].to_list() == ["1"]

    def test_excludes_everything_when_there_are_no_filters(self):
        tm = target([("1", "a", "2020-01-01", "2021-01-01")])
        fm = filters([]).head(0)
        assert filter_target(tm, fm).height == 0

    # A membership id identifies something like a post or a party, which
    # can be held by many people and by the same person more than once, so
    # it cannot identify a row

    def test_keeps_the_memberships_of_other_holders_of_a_shared_id(self):
        tm = target([
            ("1", "same", "2020-01-01", "2021-01-01"),
            ("2", "same", "2020-01-01", "2021-01-01")])
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        assert filter_target(tm, fm)["mnis_id"].to_list() == ["1"]

    def test_filters_repeated_memberships_of_the_same_id_separately(self):
        tm = target([
            ("1", "15", "2001-01-01", "2005-01-01"),
            ("1", "15", "2012-01-01", None)])
        fm = filters([("1", "2012-01-01", None)])
        result = filter_target(tm, fm)
        assert result["start"].to_list() == [date("2012-01-01")]

    def test_keeps_a_membership_with_a_null_id_which_intersects(self):
        tm = target([("1", None, "2020-01-01", "2021-01-01")])
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        assert filter_target(tm, fm).height == 1

    def test_excludes_a_null_id_which_does_not_intersect(self):
        tm = target([("1", None, "2010-01-01", "2011-01-01")])
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        assert filter_target(tm, fm).height == 0

    # Arguments are checked before the target memberships are inspected

    def test_returns_empty_target_memberships_unchanged(self):
        tm = target([]).head(0)
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        assert filter_target(tm, fm).height == 0

    def test_checks_arguments_when_the_target_memberships_are_empty(self):
        tm = target([]).head(0)
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        with pytest.raises(ValueError):
            filter_memberships(
                tm, fm, "nope", "end", "fstart", "fend", "mnis_id")

    @pytest.mark.parametrize("columns", [
        ("nope", "end", "fstart", "fend", "mnis_id"),
        ("start", "nope", "fstart", "fend", "mnis_id"),
        ("start", "end", "nope", "fend", "mnis_id"),
        ("start", "end", "fstart", "nope", "mnis_id"),
        ("start", "end", "fstart", "fend", "nope")])
    def test_rejects_a_column_which_does_not_exist(self, columns):
        tm = target([("1", "a", "2020-01-01", "2021-01-01")])
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        with pytest.raises(ValueError):
            filter_memberships(tm, fm, *columns)

    def test_rejects_a_join_column_missing_from_the_target_memberships(self):
        tm = target([("1", "a", "2020-01-01", "2021-01-01")]).drop("mnis_id")
        fm = filters([("1", "2019-01-01", "2022-01-01")])
        with pytest.raises(ValueError):
            filter_target(tm, fm)
