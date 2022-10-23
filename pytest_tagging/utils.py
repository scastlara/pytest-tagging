import threading
from multiprocessing import Manager
from typing import Any, Iterable


class TagCounter:
    """Counter that uses pytest caching module to store the counts"""

    def __init__(self, lock: threading.Lock) -> None:
        self.lock = lock
        self._manager = Manager()
        self.counter = self._manager.dict()

    def update(self, tags: Iterable[str]) -> None:
        with self.lock:
            for tag in tags:
                if tag in self.counter:
                    self.counter[tag] += 1
                else:
                    self.counter[tag] = 1

    def items(self) -> list[Any]:
        return self.counter.items()

    def __bool__(self) -> bool:
        return bool(self.counter)


def get_tags_from_item(item) -> set[str]:
    return (
        set(item.get_closest_marker("tags").args)
        if item.get_closest_marker("tags")
        else set()
    )
