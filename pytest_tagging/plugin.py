from collections import Counter
from enum import Enum

import pytest

from .utils import TagCounterThreadSafe, get_tags_from_item


class OperandChoices(Enum):
    OR = "OR"
    AND = "AND"


def select_counter_class(config) -> type[Counter] | type[TagCounterThreadSafe]:
    must_be_threadsafe = getattr(config.option, "workers", None) or getattr(config.option, "tests_per_worker", None)
    return TagCounterThreadSafe if must_be_threadsafe else Counter


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "tags('tag1', 'tag2'): add tags to a given test")
    if not config.option.collectonly:
        counter_class = select_counter_class(config)
        config.pluginmanager.register(TaggerRunner(counter_class), "taggerrunner")


def pytest_addoption(parser, pluginmanager) -> None:
    group = parser.getgroup("tagging")
    group.addoption(
        "--tags",
        type=str,
        default=[],
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

    def pytest_report_header(self, config) -> list[str]:
        """Add tagging config to pytest header."""
        tags = config.getoption("--tags")
        return [f"tagging: tags={tags}"]

    @pytest.hookimpl(hookwrapper=True)
    def pytest_collection_modifyitems(self, session, config, items):
        selected_items = []
        deselected_items = []

        all_run_tags = config.getoption("--tags")
        operand = config.getoption("--tags-operand")
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
        items[:] = selected_items
        yield

    @pytest.mark.trylast
    @pytest.hookimpl(hookwrapper=True)
    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
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
