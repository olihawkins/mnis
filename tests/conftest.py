"""Fixtures shared across the test suite"""

# Imports ---------------------------------------------------------------------

import json
import pathlib
import pytest

from mnis import utility
from mnis.cache import clear_cache
from mnis.constants import API_TIMEOUT
from mnis.settings import set_timeout

# Constants -------------------------------------------------------------------

PAYLOADS = pathlib.Path(__file__).parent / "fixtures" / "payloads"
SCHEMAS = pathlib.Path(__file__).parent / "fixtures" / "schemas.json"


# Payload helpers -------------------------------------------------------------


def load_payload(house: str, data_output: str) -> list[dict]:
    """Load one saved API payload.

    :param house: The House the payload was fetched for.
    :param data_output: The data output the payload holds.
    """
    path = PAYLOADS / f"{house.lower()}_{data_output.lower()}.json"
    return json.loads(path.read_text())


# Isolation fixtures ----------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_state():
    """Reset the package state before and after every test.

    The cache and the settings both last for the duration of a session, so
    without this a test can be affected by whatever ran before it, and can
    affect whatever runs after it.
    """
    clear_cache()
    set_timeout(API_TIMEOUT)
    yield
    clear_cache()
    set_timeout(API_TIMEOUT)


# API fixtures ----------------------------------------------------------------


@pytest.fixture
def api(monkeypatch):
    """Serve the saved payloads in place of the live API.

    The fixture replaces fetch_query_data, which is the single point at
    which the package reads from MNIS. Tests which need the API to return
    something other than the saved payload can pass their own data to
    set_data, or a function to set_handler.
    """

    class FakeAPI:

        def __init__(self):
            self.overrides = {}
            self.handler = None
            self.calls = []

        def set_data(self, house: str, data_output: str, data: list[dict]):
            """Return the given data for one house and data output."""
            self.overrides[(house, data_output)] = data

        def set_handler(self, handler):
            """Call the given function in place of fetching the data."""
            self.handler = handler

        def fetch(self, house: str, data_output: str) -> list[dict]:
            """Return the data for one house and data output."""
            self.calls.append((house, data_output))

            if self.handler is not None:
                return self.handler(house, data_output)

            if (house, data_output) in self.overrides:
                return self.overrides[(house, data_output)]

            return load_payload(house, data_output)

    fake = FakeAPI()
    monkeypatch.setattr(utility, "fetch_query_data", fake.fetch)
    return fake
