"""Build the frozen API payloads used by the tests.

The tests run against saved payloads rather than the live API so that they
assert exact values. The data behind MNIS changes continually, so counts
taken from a live response are not stable enough to assert against.

The payloads saved here are trimmed to a small number of members chosen to
cover the cases the package has to handle. A trimmed payload can be read
and reviewed; a full response cannot, and a change within one would go
unnoticed.

Run this module to rebuild the payloads from the live API:

    python tests/fixtures/build_payloads.py

The members are chosen to cover, between them:

    - members with several memberships, returned by the API as a list, and
      members with one membership, returned as a bare object
    - a member who left a party and later rejoined it, whose party
      memberships therefore repeat a party id
    - members who have died, whose date of death is present, and members
      who have not, whose date of death is a nil object
    - open memberships, whose end date is a nil object, and closed ones
    - government, opposition and parliamentary roles
    - maiden speeches, contested elections and other parliaments
    - addresses of several types, including physical offices and the
      social media types the contact functions read
"""

# Imports ---------------------------------------------------------------------

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "src"))

from mnis import utility
from mnis.constants import HOUSE_COMMONS
from mnis.constants import HOUSE_LORDS

# Constants -------------------------------------------------------------------

PAYLOADS = pathlib.Path(__file__).parent / "payloads"

DATA_OUTPUTS = [
    "BasicDetails",
    "Parties",
    "GovernmentPosts",
    "OppositionPosts",
    "ParliamentaryPosts",
    "MaidenSpeeches",
    "OtherParliaments",
    "ElectionsContested",
    "Addresses"]

HOUSE_DATA_OUTPUTS = {
    HOUSE_COMMONS: "Constituencies",
    HOUSE_LORDS: "HouseMemberships"}

MEMBERS = {
    HOUSE_COMMONS: [
        "172",      # Diane Abbott: long service, twice left and rejoined
                    # Labour, many constituencies, maiden speech
        "5131",     # Jack Abbott: 2024 intake, one constituency and one
                    # party membership, both returned as bare objects
        "4639",     # Bim Afolami: government posts, rejoined a party
        "4057",     # Nigel Adams: government and opposition posts
        "662",      # Leo Abse: died, so has a date of death
        "4212",     # Debbie Abrahams: contested elections
        "5120"],    # Shockat Adam: addresses of every social type the
                    # contact functions read, including Facebook and
                    # Instagram
    HOUSE_LORDS: [
        "4508",     # Baroness Anderson of Stoke-on-Trent: government posts,
                    # contested elections, addresses
        "56",       # Lord Arbuthnot of Edrom: served in both Houses
        "3305",     # Lord Aberconway: died, one house membership and one
                    # party membership, both returned as bare objects
        "4149",     # Lord Bannside: sat in another parliament
        "3743"]}    # Lord Adonis: website and social media addresses


# Build payloads --------------------------------------------------------------


def build_payload(house: str, data_output: str, members: list[str]) -> int:
    """Fetch one data output and save it trimmed to the given members.

    :param house: The House to fetch the data output for.
    :param data_output: The data output to fetch.
    :param members: The ids of the members to keep.
    :return: The number of members kept.
    """
    data = utility.fetch_query_data(house=house, data_output=data_output)
    kept = [member for member in data if member["@Member_Id"] in members]

    path = PAYLOADS / f"{house.lower()}_{data_output.lower()}.json"
    path.write_text(json.dumps(kept, indent=1) + "\n")
    return len(kept)


def build_payloads() -> None:
    """Fetch and save every payload used by the tests."""
    PAYLOADS.mkdir(parents=True, exist_ok=True)

    for house, members in MEMBERS.items():
        outputs = DATA_OUTPUTS + [HOUSE_DATA_OUTPUTS[house]]
        for data_output in outputs:
            kept = build_payload(house, data_output, members)
            print(f"{house:8s} {data_output:19s} members: {kept}")


if __name__ == "__main__":
    build_payloads()
