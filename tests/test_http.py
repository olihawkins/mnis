"""Tests for fetching data over HTTP"""

# Imports ---------------------------------------------------------------------

import json
import pytest
import requests

from mnis import utility
from mnis.constants import API_RETRIES
from mnis.constants import API_RETRY_BACKOFF
from mnis.settings import set_timeout
from mnis.utility import fetch_query_data
from mnis.utility import fetch_query_response

# Constants -------------------------------------------------------------------

TIMEOUT = requests.exceptions.Timeout("timed out")
CONNECTION = requests.exceptions.ConnectionError("connection refused")


# Helpers ---------------------------------------------------------------------


class Response:
    """A stand in for a response from the API."""

    def __init__(self, status_code: int = 200, content: bytes = b""):
        self.status_code = status_code
        self.content = content


@pytest.fixture
def http(monkeypatch):
    """Answer requests with given responses and record what happens.

    The fixture replaces requests.get with a function which returns each
    of the given responses in turn, raising any which are exceptions, and
    repeating the last one once they are used up. It also replaces the
    wait between retries so that the tests do not have to wait for it.
    """

    class FakeHTTP:

        def __init__(self):
            self.responses = [Response()]
            self.requests = []
            self.waits = []

        def set_responses(self, responses: list):
            """Set the responses to return in turn."""
            self.responses = responses

        def get(self, url, **kwargs):
            """Return the next response."""
            self.requests.append({"url": url, **kwargs})
            index = min(len(self.requests) - 1, len(self.responses) - 1)
            response = self.responses[index]
            if isinstance(response, Exception):
                raise response
            return response

        @property
        def attempts(self) -> int:
            """The number of requests which were sent."""
            return len(self.requests)

    fake = FakeHTTP()
    monkeypatch.setattr(utility.requests, "get", fake.get)
    monkeypatch.setattr(utility.time, "sleep", fake.waits.append)
    return fake


# Test fetch_query_response ---------------------------------------------------


class TestFetchQueryResponse:

    def test_sends_one_request_when_it_succeeds(self, http):
        http.set_responses([Response(200)])
        assert fetch_query_response("query").status_code == 200
        assert http.attempts == 1
        assert http.waits == []

    def test_sends_the_query_as_the_url(self, http):
        fetch_query_response("query")
        assert http.requests[0]["url"] == "query"

    def test_asks_for_json(self, http):
        fetch_query_response("query")
        assert http.requests[0]["headers"] == {"Accept": "application/json"}

    def test_uses_the_timeout_setting(self, http):
        set_timeout(7)
        fetch_query_response("query")
        assert http.requests[0]["timeout"] == 7

    def test_reads_the_timeout_setting_on_each_request(self, http):
        set_timeout(7)
        fetch_query_response("query")
        set_timeout(9)
        fetch_query_response("query")
        assert [r["timeout"] for r in http.requests] == [7, 9]

    # A request which fails for a reason which may not recur is retried,
    # waiting for longer before each attempt in turn

    @pytest.mark.parametrize("failure", [TIMEOUT, CONNECTION])
    def test_retries_a_request_which_fails_to_get_a_response(
            self, http, failure):
        http.set_responses([failure, Response(200)])
        assert fetch_query_response("query").status_code == 200
        assert http.attempts == 2
        assert http.waits == [API_RETRY_BACKOFF[0]]

    @pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
    def test_retries_a_status_which_means_try_again(self, http, status):
        http.set_responses([Response(status), Response(200)])
        assert fetch_query_response("query").status_code == 200
        assert http.attempts == 2

    def test_waits_for_longer_before_each_retry(self, http):
        http.set_responses([TIMEOUT])
        with pytest.raises(RuntimeError):
            fetch_query_response("query")
        assert http.waits == API_RETRY_BACKOFF

    def test_gives_up_after_the_given_number_of_retries(self, http):
        http.set_responses([TIMEOUT])
        with pytest.raises(RuntimeError):
            fetch_query_response("query")
        assert http.attempts == API_RETRIES + 1

    def test_reports_why_the_last_attempt_failed(self, http):
        http.set_responses([Response(503)])
        with pytest.raises(RuntimeError, match="503"):
            fetch_query_response("query")

    def test_succeeds_on_the_last_attempt(self, http):
        failures = [TIMEOUT] * API_RETRIES
        http.set_responses(failures + [Response(200)])
        assert fetch_query_response("query").status_code == 200
        assert http.attempts == API_RETRIES + 1

    # A request which fails for a reason which will recur is not retried,
    # as repeating it cannot change the outcome

    @pytest.mark.parametrize("status", [400, 401, 403, 404, 410])
    def test_does_not_retry_a_status_which_will_not_change(self, http, status):
        http.set_responses([Response(status)])
        assert fetch_query_response("query").status_code == status
        assert http.attempts == 1
        assert http.waits == []


# Test fetch_query_data -------------------------------------------------------


class TestFetchQueryData:

    def response(self, members: list[dict]) -> Response:
        """Return a response holding the given members."""
        body = json.dumps({"Members": {"Member": members}})
        return Response(200, body.encode("utf-8-sig"))

    def test_returns_the_members_from_the_response(self, http):
        http.set_responses([self.response([{"@Member_Id": "1"}])])
        data = fetch_query_data(house="Commons", data_output="BasicDetails")
        assert data == [{"@Member_Id": "1"}]

    def test_reads_a_response_with_a_byte_order_mark(self, http):
        body = json.dumps({"Members": {"Member": []}})
        http.set_responses([Response(200, b"\xef\xbb\xbf" + body.encode())])
        assert fetch_query_data(house="Commons", data_output="X") == []

    def test_builds_the_query_from_the_house_and_data_output(self, http):
        http.set_responses([self.response([])])
        fetch_query_data(house="Lords", data_output="Parties")
        assert http.requests[0]["url"].endswith(
            "House=Lords|Membership=all/Parties")

    @pytest.mark.parametrize("status", [400, 403, 404])
    def test_raises_for_a_status_which_is_not_success(self, http, status):
        http.set_responses([Response(status)])
        with pytest.raises(RuntimeError, match=str(status)):
            fetch_query_data(house="Commons", data_output="BasicDetails")
