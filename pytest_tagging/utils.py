from dataclasses import dataclass
from multiprocessing import Manager
from typing import Any, Iterable

from pytest_tagging.choices import OperandChoices


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


@dataclass(frozen=True, slots=True)
class TaggingOptions:
    tags: list[str] | None = None
    exclude_tags: list[str] | None = None
    operand: OperandChoices = OperandChoices.OR
