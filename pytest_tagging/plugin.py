from collections import Counter

import pytest

from pytest_tagging.choices import OperandChoices
from pytest_tagging.selector import TestSelector, get_tags_from_item
from pytest_tagging.utils import TagCounterThreadSafe, TaggingOptions


def select_counter_class(config) -> type[Counter] | type[TagCounterThreadSafe]:
    must_be_threadsafe = getattr(config.option, "workers", None) or getattr(config.option, "tests_per_worker", None)
    return TagCounterThreadSafe if must_be_threadsafe else Counter


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "tags('tag1', 'tag2'): add tags to a given test")
    config_opts = TaggingOptions(
        tags=config.getoption("--tags"),
        exclude_tags=config.getoption("--exclude-tags"),
        operand=config.getoption("--tags-operand"),
    )
    counter_class = select_counter_class(config)
    selector = TestSelector(config=config_opts)
    config.pluginmanager.register(TaggerRunnerPlugin(counter_class, selector=selector), "taggerrunner")


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
    group.addoption(
        "--exclude-tags",
        default=None,
        nargs="*",
        action="extend",
        help="Exclude the tests that contain the given tags.",
    )


class TaggerRunnerPlugin:
    def __init__(self, counter_class: type[Counter] | type[TagCounterThreadSafe], selector: TestSelector) -> None:
        self.counter = counter_class()
        self.selector = selector
        self._available_tags: list[str] = []

    def pytest_report_header(self, config) -> list[str]:
        """Add tagging config to pytest header."""
        tags_to_display = self.selector.config.tags or []
        exclude_tags_to_display = self.selector.config.exclude_tags or []
        return [f"tagging: tags={tags_to_display} , exclude-tags={exclude_tags_to_display}"]

    @pytest.hookimpl(hookwrapper=True)
    def pytest_collection_modifyitems(self, session, config, items):
        self._available_tags = self.selector.get_available_tags(items)
        tags_to_run = (
            self.selector.resolve_combined_tags(tags=self.selector.config.tags)
            if self.selector.config.tags is not None
            else set(self._available_tags)
        )
        tags_to_exclude = (
            self.selector.resolve_combined_tags(tags=self.selector.config.exclude_tags)
            if self.selector.config.exclude_tags is not None
            else set()
        )
        selected_items, deselected_items = self.selector.get_items_to_run(
            tags_to_run=tags_to_run, tags_to_exclude=tags_to_exclude, items=items
        )

        # Deselect those tags that should be excluded
        config.hook.pytest_deselected(items=deselected_items)
        # Select those tags that match our tag selection
        items[:] = selected_items
        yield

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        tags = self.selector.config.tags
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
