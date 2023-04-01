from collections import Counter
from unittest.mock import Mock

import pytest

from pytest_tagging.plugin import select_counter_class
from pytest_tagging.utils import TagCounterThreadSafe


@pytest.mark.parametrize(
    "option, expected_counter",
    (
        ("foo", Counter),
        ("workers", TagCounterThreadSafe),
        ("tests_per_worker", TagCounterThreadSafe),
    ),
)
def test_select_counter_class(option, expected_counter):
    m_option = Mock(spec=[option])
    setattr(m_option, option, 1)
    m_config = Mock(option=m_option)

    assert select_counter_class(m_config) is expected_counter


def test_collect_tag(testdir):
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.tags('foo')
        def test_tagged():
            assert True
    """
    )
    result = testdir.runpytest("--tags=foo")
    result.assert_outcomes(passed=1)


def test_collect_only_tag(testdir):
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.tags('foo')
        def test_tagged():
            assert True

        def test_untagged():
            assert False
    """
    )
    result = testdir.runpytest("--tags=foo")
    result.assert_outcomes(passed=1, failed=0)


def test_collect_tags_or(testdir):
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.tags('foo')
        def test_tagged_1():
            assert True

        @pytest.mark.tags('bar')
        def test_tagged_2():
            assert True
    """
    )
    result = testdir.runpytest("--tags=foo", "--tags=bar")
    result.assert_outcomes(passed=2)


def test_collect_tags_and(testdir):
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.tags('foo')
        def test_tagged_1():
            assert True

        @pytest.mark.tags('bar')
        def test_tagged_2():
            assert True

        @pytest.mark.tags('foo', 'bar')
        def test_tagged_3():
            assert True
    """
    )
    result = testdir.runpytest("--tags=foo", "--tags=bar", "--tags-operand=AND")
    result.assert_outcomes(passed=1, failed=0)


def test_summary_contains_counts(testdir):
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.tags('foo')
        def test_tagged_1():
            assert False
    """
    )
    result = testdir.runpytest()
    result.stdout.re_match_lines(".+failing tags.+")
    result.stdout.re_match_lines("foo - 1")


def test_taggerrunner_with_parallel_with_processes_and_threads(testdir):
    """
    This test ensures counts are collected correctly when tests run in different processes and threads.
    Cannot use `pytest.mark.parametrize` because `testdir` fixture ends up raising a weird
    AssertionError on teardown.
    """
    testdir.makepyfile(
        """
        import pytest
        from time import sleep

        @pytest.mark.tags('foo')
        def test_tagged_1():
            sleep(0.01)
            assert False

        @pytest.mark.tags('foo', 'bar')
        def test_tagged_2():
            sleep(0.01)
            assert False

        @pytest.mark.tags('bar')
        def test_tagged_3():
            sleep(0.01)
            assert False

        @pytest.mark.tags('bar')
        def test_tagged_4():
            sleep(0.01)
            assert False
    """
    )
    for _ in range(10):  # to ensure the passing test is not just (very bad) luck
        result = testdir.runpytest("--workers=2", "--tests-per-worker=2")
        result.stdout.re_match_lines("foo - 2")
        result.stdout.re_match_lines("bar - 3")
