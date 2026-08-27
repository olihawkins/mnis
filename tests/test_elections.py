"""Tests for the general election data"""

# Imports ---------------------------------------------------------------------

import datetime
import polars as pl

from mnis.elections import get_general_elections
from mnis.elections import get_general_elections_list


# Test get_general_elections --------------------------------------------------


class TestGetGeneralElections:

    def test_returns_the_expected_columns(self):
        elections = get_general_elections()
        assert elections.columns == ["name", "dissolution", "election"]

    def test_returns_the_expected_types(self):
        elections = get_general_elections()
        assert elections.schema["name"] == pl.String
        assert elections.schema["dissolution"] == pl.Date
        assert elections.schema["election"] == pl.Date

    def test_begins_with_the_1929_general_election(self):
        first = get_general_elections().row(0, named=True)
        assert first["name"] == "1929"
        assert first["election"] == datetime.date(1929, 5, 30)

    def test_includes_the_2024_general_election(self):
        elections = get_general_elections()
        row = elections.filter(pl.col("name") == "2024").row(0, named=True)
        assert row["dissolution"] == datetime.date(2024, 5, 30)
        assert row["election"] == datetime.date(2024, 7, 4)

    def test_names_the_two_general_elections_of_1974(self):
        names = get_general_elections()["name"].to_list()
        assert "1974 (Feb)" in names
        assert "1974 (Oct)" in names

    def test_every_election_has_a_unique_name(self):
        elections = get_general_elections()
        assert elections["name"].n_unique() == elections.height

    def test_every_dissolution_precedes_its_election(self):
        elections = get_general_elections()
        assert elections.filter(
            pl.col("dissolution") >= pl.col("election")).height == 0

    def test_the_elections_are_in_chronological_order(self):
        elections = get_general_elections()
        assert elections["election"].to_list() == sorted(
            elections["election"].to_list())


# Test get_general_elections_list ---------------------------------------------


class TestGetGeneralElectionsList:

    def test_returns_an_item_for_every_election(self):
        assert len(get_general_elections_list()) == \
            get_general_elections().height

    def test_keys_each_item_with_the_election_name(self):
        elections = get_general_elections_list()
        assert "2024" in elections
        assert "1974 (Feb)" in elections

    def test_returns_the_dissolution_and_election_dates(self):
        election = get_general_elections_list()["2024"]
        assert election["dissolution"] == datetime.date(2024, 5, 30)
        assert election["election"] == datetime.date(2024, 7, 4)

    def test_agrees_with_the_dataframe(self):
        frame = get_general_elections()
        elections = get_general_elections_list()
        for row in frame.iter_rows(named=True):
            assert elections[row["name"]]["dissolution"] == row["dissolution"]
            assert elections[row["name"]]["election"] == row["election"]
