from multiprocessing import Manager
from typing import Any, Iterable


class TagCounterThreadSafe:
    def __init__(self) -> None:
        self._manager = Manager()
        self.counter = self._manager.dict()
        self.lock = self._manager.Lock()

    def update(self, tags: Iterable[str]) -> None:
        with self.lock:
            for tag in tags:
                if tag in self.counter:
                    self.counter[tag] += 1
                else:
                    self.counter[tag] = 1

    def items(self) -> list[Any]:
        return sorted(self.counter.items(), key=lambda x: (x[1], x[0]), reverse=True)

    def __bool__(self) -> bool:
        return bool(self.counter)


def get_tags_from_item(item) -> set[str]:
    return set(item.get_closest_marker("tags").args) if item.get_closest_marker("tags") else set()


def flatten_list(matrix: list[list]) -> list:
    return [item for row in matrix for item in row]


def get_run_tags(all_run_tags: list[list]) -> None | list:
    """
    Get
    """
    if len(all_run_tags) == 0:
        return None
    else:
        return flatten_list(all_run_tags) if all_run_tags[0] is not None else []
