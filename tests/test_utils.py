from pytest_tagging.utils import CACHE_PREFIX, TagCounter

from .utils import FakeCache


class TestTagCounter:
    def test_update(self):
        counter = TagCounter(FakeCache())
        assert dict(counter.items()) == {}

        counter.update({"A", "B", "C"})
        assert dict(counter.items()) == {"A": 1, "B": 1, "C": 1}

        counter.update({"A"})
        assert dict(counter.items()) == {"A": 2, "B": 1, "C": 1}

    def test_from_cache(self):
        fake_cache = FakeCache()
        fake_cache.set(CACHE_PREFIX, {"foo": 1})
        counter = TagCounter.from_cache(fake_cache)
        assert dict(counter.items()) == {"foo": 1}

    def test_reset(self):
        fake_cache = FakeCache()
        counter = TagCounter(fake_cache)
        counter.update({"A"})

        assert dict(counter.items())

        counter.reset()

        assert fake_cache.data == {CACHE_PREFIX: {}}
