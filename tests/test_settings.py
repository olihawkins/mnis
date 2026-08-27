"""Tests for the package settings and the cache"""

# Imports ---------------------------------------------------------------------

import pytest

from mnis.cache import cache
from mnis.cache import clear_cache
from mnis.constants import API_TIMEOUT
from mnis.settings import get_timeout
from mnis.settings import set_timeout


# Test the timeout setting ----------------------------------------------------


class TestTimeout:

    def test_the_timeout_starts_at_the_default(self):
        assert get_timeout() == API_TIMEOUT

    @pytest.mark.parametrize("given", [0.5, 1, 20, 60, 120.0])
    def test_sets_a_positive_number(self, given):
        set_timeout(given)
        assert get_timeout() == given

    @pytest.mark.parametrize("given", [0, -1, -0.5])
    def test_rejects_a_number_which_is_not_positive(self, given):
        with pytest.raises(ValueError):
            set_timeout(given)

    @pytest.mark.parametrize("given", ["20", None, [20], {}, object()])
    def test_rejects_a_value_which_is_not_a_number(self, given):
        with pytest.raises(ValueError):
            set_timeout(given)

    # A bool is an int in Python, so it has to be rejected explicitly

    @pytest.mark.parametrize("given", [True, False])
    def test_rejects_a_boolean(self, given):
        with pytest.raises(ValueError):
            set_timeout(given)

    def test_leaves_the_timeout_unchanged_when_a_value_is_rejected(self):
        set_timeout(30)
        with pytest.raises(ValueError):
            set_timeout(-1)
        assert get_timeout() == 30


# Test the cache --------------------------------------------------------------


class TestCache:

    def test_clear_cache_empties_the_cache(self):
        cache["test"] = "value"
        clear_cache()
        assert len(cache) == 0

    def test_clear_cache_empties_a_cache_which_is_already_empty(self):
        clear_cache()
        clear_cache()
        assert len(cache) == 0

    # The cache is cleared in place so that every module which holds a
    # reference to it sees the change

    def test_clear_cache_keeps_the_same_cache_object(self):
        original = cache
        cache["test"] = "value"
        clear_cache()
        assert original is cache
