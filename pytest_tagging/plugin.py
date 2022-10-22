import argparse
import threading
from collections import Counter, abc, defaultdict
from enum import Enum, auto
from typing import Iterable, Iterator, Optional

import pytest

from .utils import TagCounter, get_tags_from_item

CACHE_PREFIX = "pytest-tagging"


class OperandChoices(Enum):
    OR = "OR"
    AND = "AND"


def pytest_configure(config):
    TagCounter.from_cache(config.cache).reset()
    config.addinivalue_line("markers", "tags('tag1', 'tag2'): add tags to a given test")
    if not config.option.collectonly:
        config.pluginmanager.register(TaggerRunner(), "taggerrunner")


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
    def __init__(self):
        self.lock = threading.Lock()

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
            if not run_tags:
                selected_items.append(item)
            elif operand is OperandChoices.OR and test_tags & run_tags:
                selected_items.append(item)
            elif operand is OperandChoices.AND and run_tags <= test_tags:
                selected_items.append(item)
            else:
                deselected_items.append(item)

        config.hook.pytest_deselected(items=deselected_items)
        items[:] = selected_items
        yield

    @pytest.mark.trylast
    @pytest.hookimpl(hookwrapper=True)
    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        counter = TagCounter.from_cache(config.cache)
        if counter:
            terminalreporter.write_sep("=", "failing tags", yellow=True, bold=True)
            terminalreporter.ensure_newline()

        for key, value in counter.items():
            terminalreporter.write_line(f"{key} - {value}")
        terminalreporter.ensure_newline()
        yield

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        yield
        if call.when == "call" and call.excinfo:
            tags = get_tags_from_item(item)
            with self.lock:
                counter = TagCounter.from_cache(item.config.cache)
                counter.update(tags)
