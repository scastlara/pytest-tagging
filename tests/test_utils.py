import threading

import pytest

from pytest_tagging.utils import TagCounterThreadSafe, flatten_list, get_run_tags


class TestTagCounterThreadSafe:
    def test_update(self):
        counter = TagCounterThreadSafe()
        assert dict(counter.items()) == {}

        counter.update({"A", "B", "C"})
        assert dict(counter.items()) == {"A": 1, "B": 1, "C": 1}

        counter.update({"A"})
        assert dict(counter.items()) == {"A": 2, "B": 1, "C": 1}

    def test_empty_is_false(self):
        assert bool(TagCounterThreadSafe()) is False

    def test_sorted_items(self):
        counter = TagCounterThreadSafe()
        counter.update({"A", "B", "C"})
        counter.update({"A"})
        counter.update({"A"})
        counter.update({"B"})

        assert list(counter.items()) == [("A", 3), ("B", 2), ("C", 1)]

    def test_threadsafe_update(self):
        counter = TagCounterThreadSafe()

        def update(counter):
            counter.update({"A", "B"})

        threads = [threading.Thread(target=update, args=(counter,)) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert dict(counter.items()) == {"A": 5, "B": 5}


def test_flatten_list():
    my_list = [["foo"], ["bar"]]
    assert flatten_list(my_list) == ["foo", "bar"]


# First index is test data, seconds is expected result
@pytest.mark.parametrize(
    "tags",
    [
        [[], None],
        [[[]], []],
        [[["tag1"], ["tag2"]], ["tag1", "tag2"]],
    ],
)
def test_get_run_tags(tags: list[list]):
    assert get_run_tags(tags[0]) == tags[1]
