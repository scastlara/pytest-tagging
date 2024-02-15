from collections import Counter
from enum import Enum

import pytest

from .utils import TagCounterThreadSafe, get_run_tags, get_tags_from_item


class OperandChoices(Enum):
    OR = "OR"
    AND = "AND"


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
    counter_class = select_counter_class(config)
    config.pluginmanager.register(TaggerRunner(counter_class), "taggerrunner")


def pytest_addoption(parser, pluginmanager) -> None:
    group = parser.getgroup("tagging")

    # --tags can be in 3 states
    # []] if not specified
    # [[]] if specified but empty
    # [["my_tag"]] if specified with an tag
    # That means with multiple --tags it becomes [["my_tag1"], ["my_tag2"]]
    # With action="extend" it cannot become [[]]
    group.addoption(
        "--tags",
        default=[],
        nargs="*",
        action="append",
        help="Run the tests that contain the given tags, separated by commas",
    )
    group.addoption(
        "--tags-operand",
        type=OperandChoices,
        default=OperandChoices.OR,
        choices=list(OperandChoices),
    )
    parser.addini(
        "tags",
        help="Run the tests that contain the given tags, separated by commas",
    )


class TaggerRunner:
    def __init__(self, counter_class: type[Counter] | type[TagCounterThreadSafe]) -> None:
        self.counter = counter_class()
        self._available_tags: list[str] = []

    def get_available_tags(self, items) -> list:
        """
        Returns all available tags
        :param items: Items from pytest_collection_modifyitems
        """
        available_tags = []
        for item in items:
            test_tags = set(get_tags_from_item(item))
            for tag in test_tags:
                if tag not in available_tags:
                    available_tags.append(tag)

        return available_tags

    def pytest_report_header(self, config) -> list[str]:
        """Add tagging config to pytest header."""
        tags = config.getoption("--tags")
        return [f"tagging: tags={tags}"]

    @pytest.hookimpl(hookwrapper=True)
    def pytest_collection_modifyitems(self, session, config, items):
        selected_items = []
        deselected_items = []

        all_run_tags = get_run_tags(config.getoption("--tags"))
        if all_run_tags is not None:
            # --tags was provided
            if len(all_run_tags) == 0:
                # If no items in --tags
                self._available_tags = self.get_available_tags(items)
                for item in items:
                    deselected_items.append(item)
            else:
                # If items in --tags
                operand = config.getoption("--tags-operand")

                # Allows you to combine tags
                found_combined_tags = set(all_run_tags) & set(_combined_tags)
                for tag_name in found_combined_tags:
                    all_run_tags += _combined_tags[tag_name]

                for item in items:
                    run_tags = set(all_run_tags)
                    test_tags = get_tags_from_item(item)
                    if (
                        not run_tags
                        or (operand is OperandChoices.OR and test_tags & run_tags)
                        or (operand is OperandChoices.AND and run_tags <= test_tags)
                    ):
                        selected_items.append(item)
                    else:
                        deselected_items.append(item)
            config.hook.pytest_deselected(items=deselected_items)
        else:
            # --tags was not provided. Run all tests as normal
            selected_items = items
        items[:] = selected_items
        yield

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        tags = get_run_tags(config.getoption("--tags"))
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
