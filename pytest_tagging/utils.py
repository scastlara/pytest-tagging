from collections import Counter, abc
from typing import Any, Iterable, Iterator, Optional

CACHE_PREFIX = "pytest-tagging"


class TagCounter:
    """Counter that uses pytest caching module to store the counts"""

    @classmethod
    def from_cache(cls, cache):
        return cls(cache, cache.get(CACHE_PREFIX, {}))

    def __init__(self, cache, counter_data: Optional[dict[str, int]] = None) -> None:
        self.cache = cache
        self.data: Counter = Counter()
        if counter_data:
            self.data.update(counter_data)

    def update(self, tags: Iterable[str]) -> None:
        self.data.update(tags)
        self.save()

    def items(self) -> Iterator[tuple[Any, int]]:
        for item in sorted(self.data.items(), key=lambda x: (x[1], x[0]), reverse=True):
            yield item

    def reset(self) -> None:
        self.cache.set(CACHE_PREFIX, {})

    def save(self) -> None:
        self.cache.set(CACHE_PREFIX, self.data)

    def __bool__(self) -> bool:
        return bool(self.data)


def get_tags_from_item(item) -> set[str]:
    return (
        set(item.get_closest_marker("tags").args)
        if item.get_closest_marker("tags")
        else set()
    )
