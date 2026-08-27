"""Tests for the fetch functions against the saved API payloads

These tests run the whole package against payloads which do not change, so
they can assert exact values. The members in the payloads are listed in
tests/fixtures/build_payloads.py.
"""

# Imports ---------------------------------------------------------------------

import datetime
import polars as pl
import pytest

import mnis

# Constants -------------------------------------------------------------------

ABBOTT = "172"
ADAM = "5120"
ADONIS = "3743"

MPS = ["172", "5131", "4212", "662", "5120", "4057", "4639"]


# Helpers ---------------------------------------------------------------------


def date(iso: str) -> datetime.date:
    """Return a date from an ISO 8601 string."""
    return datetime.date.fromisoformat(iso)


def rows(df: pl.DataFrame, mnis_id: str, *columns) -> list[tuple]:
    """Return the given columns for one member, in order."""
    return list(
        df.filter(pl.col("mnis_id") == mnis_id).select(*columns)
        .iter_rows())


# Test fetching members -------------------------------------------------------


class TestFetchMembers:

    def test_fetch_mps_returns_a_row_for_each_mp(self, api):
        assert sorted(mnis.fetch_mps()["mnis_id"].to_list()) == sorted(MPS)

    def test_fetch_mps_sorts_by_family_name(self, api):
        names = mnis.fetch_mps()["family_name"].to_list()
        assert names == sorted(names)

    def test_fetch_mps_reads_a_date_of_death(self, api):
        mps = mnis.fetch_mps()
        assert rows(mps, "662", "date_of_death") == [(date("2008-08-19"),)]

    def test_fetch_mps_leaves_a_living_member_without_a_date_of_death(
            self, api):
        mps = mnis.fetch_mps()
        assert rows(mps, ABBOTT, "date_of_death") == [(None,)]

    def test_fetch_lords_returns_a_row_for_each_lord(self, api):
        lords = mnis.fetch_lords()
        assert lords.height == 5
        assert "lord_type" in lords.columns

    def test_fetch_mps_strips_whitespace_from_strings(self, api):
        mps = mnis.fetch_mps()
        for name in mps["display_name"].to_list():
            assert name == name.strip()


# Test Commons memberships ----------------------------------------------------


class TestCommonsMemberships:

    def test_returns_a_row_for_each_membership(self, api):
        memberships = mnis.fetch_commons_memberships()
        assert rows(memberships, "5131", "constituency_name") == [("Ipswich",)]

    def test_an_open_membership_has_no_end_date(self, api):
        memberships = mnis.fetch_commons_memberships()
        current = memberships.filter(
            pl.col("seat_incumbency_end_date").is_null())
        assert ABBOTT in current["mnis_id"].to_list()

    # A membership is taken to end at the dissolution of Parliament rather
    # than on the date of the general election which followed it

    def test_a_membership_ends_at_the_dissolution_of_parliament(self, api):
        memberships = mnis.fetch_commons_memberships()
        ends = [
            row[0] for row in rows(
                memberships, ABBOTT, "seat_incumbency_end_date")
            if row[0] is not None]
        assert date("2024-05-30") in ends
        assert date("2024-07-04") not in ends

    def test_filters_memberships_on_a_date(self, api):
        memberships = mnis.fetch_commons_memberships(on_date="2012-01-01")
        assert sorted(memberships["mnis_id"].unique().to_list()) == \
            sorted([ABBOTT, "4212", "4057"])

    def test_filters_memberships_between_dates(self, api):
        memberships = mnis.fetch_commons_memberships(
            from_date="1990-01-01", to_date="1991-01-01")
        assert memberships["mnis_id"].unique().to_list() == [ABBOTT]


# Test party memberships ------------------------------------------------------


class TestPartyMemberships:

    def test_returns_each_party_membership_in_turn(self, api):
        pm = mnis.fetch_mps_party_memberships(while_mp=False)
        assert rows(pm, ABBOTT, "party_name") == [
            ("Labour",), ("Labour",), ("Labour",), ("Labour",),
            ("Independent",), ("Labour",), ("Labour",), ("Independent",),
            ("Labour",)]

    # Consecutive memberships of the same party are combined, but a party
    # which was left and later rejoined stays a separate membership

    def test_collapse_combines_consecutive_memberships(self, api):
        pm = mnis.fetch_mps_party_memberships(collapse=True)
        assert rows(
            pm, ABBOTT, "party_name",
            "party_membership_start_date",
            "party_membership_end_date") == [
                ("Labour", date("1987-06-11"), date("2023-04-23")),
                ("Independent", date("2023-04-23"), date("2024-05-28")),
                ("Labour", date("2024-05-28"), date("2025-07-17")),
                ("Independent", date("2025-07-17"), date("2026-07-30")),
                ("Labour", date("2026-07-30"), None)]

    def test_collapse_drops_the_party_membership_id(self, api):
        pm = mnis.fetch_mps_party_memberships(collapse=True)
        assert "party_mnis_id" in mnis.fetch_mps_party_memberships().columns
        assert "party_mnis_id" in pm.columns

    def test_while_mp_excludes_memberships_held_outside_the_commons(
            self, api):
        held = mnis.fetch_mps_party_memberships(while_mp=False).height
        while_mp = mnis.fetch_mps_party_memberships(while_mp=True).height
        assert while_mp <= held

    def test_lords_party_memberships_are_returned(self, api):
        pm = mnis.fetch_lords_party_memberships(while_lord=False)
        assert pm.height > 0
        assert "party_name" in pm.columns


# Test roles ------------------------------------------------------------------


class TestRoles:

    @pytest.mark.parametrize("fetch, column", [
        (mnis.fetch_mps_government_roles, "government_role_name"),
        (mnis.fetch_mps_opposition_roles, "opposition_role_name"),
        (mnis.fetch_mps_parliamentary_roles, "parliamentary_role_name")])
    def test_returns_roles_with_a_name(self, api, fetch, column):
        assert column in fetch().columns

    def test_a_role_held_before_entering_the_commons_is_excluded(self, api):
        held = mnis.fetch_mps_government_roles(while_mp=False)
        while_mp = mnis.fetch_mps_government_roles(while_mp=True)
        assert while_mp.height <= held.height

    def test_roles_are_filtered_on_a_date(self, api):
        roles = mnis.fetch_mps_government_roles(
            while_mp=False, on_date="1900-01-01")
        assert roles.height == 0


# Test contact details --------------------------------------------------------


class TestContacts:

    def test_returns_a_website_for_a_member_who_has_one(self, api):
        websites = mnis.fetch_mps_websites()
        assert "url" in websites.columns

    def test_returns_a_twitter_account_with_a_username(self, api):
        accounts = mnis.fetch_mps_twitter()
        assert ADAM in accounts["mnis_id"].to_list()
        username = rows(accounts, ADAM, "username")[0][0]
        assert username and "/" not in username

    def test_returns_a_facebook_account(self, api):
        assert ADAM in mnis.fetch_mps_facebook()["mnis_id"].to_list()

    def test_returns_an_instagram_account(self, api):
        assert ADAM in mnis.fetch_mps_instagram()["mnis_id"].to_list()

    def test_returns_office_addresses_which_are_physical(self, api):
        offices = mnis.fetch_mps_office_addresses()
        assert offices.height > 0
        assert "postcode" in offices.columns

    def test_returns_email_addresses(self, api):
        emails = mnis.fetch_mps_email_addresses()
        assert emails["email"].null_count() == 0

    def test_returns_lords_contact_details(self, api):
        assert ADONIS in mnis.fetch_lords_websites()["mnis_id"].to_list()

    def test_contact_details_are_filtered_by_member(self, api):
        accounts = mnis.fetch_mps_twitter(on_date="1990-01-01")
        assert ADAM not in accounts["mnis_id"].to_list()


# Test caching ----------------------------------------------------------------


class TestCaching:

    def test_fetches_each_data_output_once(self, api):
        mnis.fetch_mps_party_memberships()
        first = len(api.calls)
        mnis.fetch_mps_party_memberships()
        assert len(api.calls) == first

    def test_fetches_basic_details_once(self, api):
        mnis.fetch_mps()
        mnis.fetch_commons_memberships()
        mnis.fetch_mps_government_roles()
        assert api.calls.count(("Commons", "BasicDetails")) == 1

    def test_clear_cache_makes_the_data_be_fetched_again(self, api):
        mnis.fetch_mps()
        mnis.clear_cache()
        mnis.fetch_mps()
        assert api.calls.count(("Commons", "BasicDetails")) == 2

    def test_the_cache_does_not_change_the_data(self, api):
        first = mnis.fetch_mps_party_memberships()
        mnis.clear_cache()
        second = mnis.fetch_mps_party_memberships()
        assert first.equals(second)
