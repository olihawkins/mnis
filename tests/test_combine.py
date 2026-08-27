"""Tests for combining consecutive party memberships"""

# Imports ---------------------------------------------------------------------

import datetime
import polars as pl
import pytest

from mnis.combine import combine_party_memberships

# Constants -------------------------------------------------------------------

SCHEMA = {
    "mnis_id": pl.String,
    "given_name": pl.String,
    "family_name": pl.String,
    "display_name": pl.String,
    "party_mnis_id": pl.String,
    "party_name": pl.String,
    "party_membership_start_date": pl.Date,
    "party_membership_end_date": pl.Date}


# Helpers ---------------------------------------------------------------------


def date(iso: str | None) -> datetime.date | None:
    """Return a date from an ISO 8601 string, or None."""
    return None if iso is None else datetime.date.fromisoformat(iso)


def memberships(rows: list[tuple]) -> pl.DataFrame:
    """Build a dataframe of party memberships from tuples.

    Each tuple gives the member id, family name, party id, party name,
    start date and end date of one party membership.
    """
    return pl.DataFrame(
        [
            (mnis_id, "A", family_name, f"A {family_name}",
             party_id, party_name, date(start), date(end))
            for mnis_id, family_name, party_id, party_name, start, end in rows
        ],
        schema=SCHEMA,
        orient="row")


def spells(result: pl.DataFrame, mnis_id: str) -> list[tuple]:
    """Return the party and dates of each membership for one member."""
    rows = result.filter(pl.col("mnis_id") == mnis_id).sort(
        "party_membership_start_date", nulls_last=True)
    return [
        (row["party_name"],
         row["party_membership_start_date"],
         row["party_membership_end_date"])
        for row in rows.iter_rows(named=True)]


# Test combine_party_memberships ----------------------------------------------


class TestCombinePartyMemberships:

    def test_combines_consecutive_memberships_of_the_same_party(self):
        pm = memberships([
            ("1", "Aa", "15", "Labour", "2001-01-01", "2005-01-01"),
            ("1", "Aa", "15", "Labour", "2005-01-01", "2010-01-01")])
        assert spells(combine_party_memberships(pm), "1") == [
            ("Labour", date("2001-01-01"), date("2010-01-01"))]

    def test_keeps_memberships_of_different_parties_separate(self):
        pm = memberships([
            ("1", "Aa", "15", "Labour", "2001-01-01", "2005-01-01"),
            ("1", "Aa", "8", "Independent", "2005-01-01", "2010-01-01")])
        assert spells(combine_party_memberships(pm), "1") == [
            ("Labour", date("2001-01-01"), date("2005-01-01")),
            ("Independent", date("2005-01-01"), date("2010-01-01"))]

    def test_keeps_a_rejoined_party_as_a_separate_membership(self):
        pm = memberships([
            ("1", "Aa", "15", "Labour", "2001-01-01", "2005-01-01"),
            ("1", "Aa", "8", "Independent", "2005-01-01", "2010-01-01"),
            ("1", "Aa", "15", "Labour", "2010-01-01", "2015-01-01")])
        assert spells(combine_party_memberships(pm), "1") == [
            ("Labour", date("2001-01-01"), date("2005-01-01")),
            ("Independent", date("2005-01-01"), date("2010-01-01")),
            ("Labour", date("2010-01-01"), date("2015-01-01"))]

    def test_keeps_the_memberships_of_each_member_separate(self):
        pm = memberships([
            ("1", "Aa", "15", "Labour", "2001-01-01", "2005-01-01"),
            ("2", "Bb", "15", "Labour", "2001-01-01", "2004-01-01")])
        result = combine_party_memberships(pm)
        assert spells(result, "1") == [
            ("Labour", date("2001-01-01"), date("2005-01-01"))]
        assert spells(result, "2") == [
            ("Labour", date("2001-01-01"), date("2004-01-01"))]

    def test_an_open_membership_stays_open_when_combined(self):
        pm = memberships([
            ("1", "Aa", "15", "Labour", "2001-01-01", "2005-01-01"),
            ("1", "Aa", "15", "Labour", "2005-01-01", None)])
        assert spells(combine_party_memberships(pm), "1") == [
            ("Labour", date("2001-01-01"), None)]

    def test_drops_the_party_membership_id_columns(self):
        pm = memberships([
            ("1", "Aa", "15", "Labour", "2001-01-01", "2005-01-01")])
        result = combine_party_memberships(pm)
        assert sorted(result.columns) == sorted(SCHEMA.keys())

    def test_is_deterministic(self):
        pm = memberships([
            ("1", "Aa", "15", "Labour", "2001-01-01", "2005-01-01"),
            ("1", "Aa", "8", "Independent", "2005-01-01", "2010-01-01"),
            ("2", "Bb", "15", "Labour", "2001-01-01", None)])
        assert combine_party_memberships(pm).equals(
            combine_party_memberships(pm))

    def test_rejects_a_dataframe_without_the_expected_columns(self):
        pm = memberships([
            ("1", "Aa", "15", "Labour", "2001-01-01", "2005-01-01")])
        with pytest.raises(ValueError):
            combine_party_memberships(pm.drop("party_name"))
