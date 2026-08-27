"""Tests for extracting contact details"""

# Imports ---------------------------------------------------------------------

import pytest

from mnis.contacts import extract_username


# Test extract_username -------------------------------------------------------


class TestExtractUsername:

    @pytest.mark.parametrize("url, username", [
        ("https://twitter.com/someone", "someone"),
        ("https://x.com/someone", "someone"),
        ("http://www.facebook.com/someone", "someone"),
        ("https://www.instagram.com/someone", "someone")])
    def test_takes_the_username_from_a_url(self, url, username):
        assert extract_username(url) == username

    def test_ignores_a_trailing_slash(self):
        assert extract_username("https://twitter.com/someone/") == "someone"

    def test_ignores_several_trailing_slashes(self):
        assert extract_username("https://twitter.com/someone//") == "someone"

    @pytest.mark.parametrize("url", [
        "https://twitter.com/someone?lang=en",
        "https://twitter.com/someone/?lang=en",
        "https://twitter.com/someone?lang=en&x=1"])
    def test_ignores_a_query_string(self, url):
        assert extract_username(url) == "someone"

    def test_takes_a_bare_username_unchanged(self):
        assert extract_username("@someone") == "@someone"

    # A url with no username returns None rather than raising, which the
    # contact functions record as a null username

    @pytest.mark.parametrize("url", ["", "/", "//", "?", "/?"])
    def test_returns_none_when_there_is_no_username(self, url):
        assert extract_username(url) is None
