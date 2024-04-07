from collections import Counter
from dataclasses import dataclass
from enum import Enum

import pytest

from .utils import TagCounterThreadSafe, get_tags_from_item


class OperandChoices(Enum):
    OR = "OR"
    AND = "AND"


@dataclass(frozen=True, slots=True)
class TaggingOptions:
    tags: list[str] | None = None
    operand: OperandChoices = OperandChoices.OR


# Allows you to combine tags
_combined_tags = {}


def combine_tags(tag_name: str, *args):
    """Combine all tags in `args` into `new_tag`"""
    _combined_tags[tag_name] = args


def select_counter_class(config) -> type[Counter] | type[TagCounterThreadSafe]:
    must_be_threadsafe = getattr(config.option, "workers", None) or getattr(config.option, "tests_per_worker", None)
    return TagCounterThreadSafe if must_be_threadsafe else Counter


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "tags('tag1', 'tag2'): add tags to a given test")
    config_opts = TaggingOptions(
        tags=config.getoption("--tags"),
        operand=config.getoption("--tags-operand"),
    )
    counter_class = select_counter_class(config)
    config.pluginmanager.register(TaggerRunner(counter_class, config=config_opts), "taggerrunner")


def pytest_addoption(parser, pluginmanager) -> None:
    group = parser.getgroup("tagging")

    group.addoption(
        "--tags",
        default=None,  # it can be none because we have to distinguish between provided empty and not provided
        nargs="*",
        action="extend",
        help="Run the tests that contain the given tags.",
    )
    group.addoption(
        "--tags-operand",
        type=OperandChoices,
        default=OperandChoices.OR,
        choices=list(OperandChoices),
    )


class TaggerRunner:
    def __init__(
        self,
        counter_class: type[Counter] | type[TagCounterThreadSafe],
        config: TaggingOptions,
    ) -> None:
        self.counter = counter_class()
        self.config = config
        self._available_tags: list[str] = []

    def get_available_tags(self, items) -> list[str]:
        """
        Returns all available tags
        :param items: Items from pytest_collection_modifyitems
        """
        available_tags = set()
        for item in items:
            test_tags = set(get_tags_from_item(item))
            available_tags.update(test_tags)
        return list(available_tags)

    def get_tags_to_run(self, tags: list[str] | None, available_tags: list[str], operand: OperandChoices) -> set[str]:
        if tags is None:
            return set(available_tags)
        found_combined_tags = set(tags) & set(_combined_tags)
        for tag_name in found_combined_tags:
            tags += _combined_tags[tag_name]
        return set(tags) or set()

    def pytest_report_header(self, config) -> list[str]:
        """Add tagging config to pytest header."""
        return [f"tagging: tags={self.config.tags}"]

    @pytest.hookimpl(hookwrapper=True)
    def pytest_collection_modifyitems(self, session, config, items):
        selected_items = []
        deselected_items = []
        self._available_tags = self.get_available_tags(items)

        all_run_tags = self.get_tags_to_run(
            tags=self.config.tags,
            available_tags=self._available_tags,
            operand=self.config.operand,
        )
        if self.config.tags == [] or (self.config.tags is not None and not all_run_tags):
            # No tags match the conditions to run
            # or we just passed an empty `--tags` options to see them all.
            for item in items:
                deselected_items.append(item)
        else:
            # Some tags were selected
            for item in items:
                test_tags = get_tags_from_item(item)
                if (self.config.operand is OperandChoices.OR and test_tags & all_run_tags) or (
                    self.config.operand is OperandChoices.AND and all_run_tags <= test_tags
                ):
                    selected_items.append(item)
                else:
                    deselected_items.append(item)
            config.hook.pytest_deselected(items=deselected_items)
        items[:] = selected_items
        yield

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        tags = self.config.tags
        if tags is not None and len(tags) == 0:
            terminalreporter.write_line("=" * 6 + " Available tags " + "=" * 6)
            for tag in self._available_tags:
                terminalreporter.write_line(f"- '{tag}'")

        if self.counter:
            terminalreporter.write_sep("=", "failing tags", yellow=True, bold=True)
            terminalreporter.ensure_newline()

        for key, value in self.counter.items():
            terminalreporter.write_line(f"{key} - {value}")
        terminalreporter.ensure_newline()
        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        yield
        if call.when == "call" and call.excinfo:
            tags = get_tags_from_item(item)
            self.counter.update(tags)
