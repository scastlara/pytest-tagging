import platform
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


class TestsTagNotSelected:
    def test_collect_only_tagged(self, testdir):
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
        result = testdir.runpytest("--tags=foo")
        result.assert_outcomes(passed=1, failed=0)

    def test_none_tagged(self, testdir):
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
        result = testdir.runpytest("--tags=123")
        result.assert_outcomes(passed=0, failed=0)


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


def test_print_tags_available(pytester):
    pytester.makepyfile(
        """
    import pytest
    @pytest.mark.tags('bar')
    def test_tagged1():
        pass
    @pytest.mark.tags('bar')
    def test_tagged2():
        pass
    @pytest.mark.tags('foo')
    def test_tagged3():
        pass
    """
    )
    res = pytester.runpytest("--tags")
    res.assert_outcomes(passed=0)
    assert res.stdout.str().count("bar") == 1
    assert res.stdout.str().count("foo") == 1


def test_no_print_tags_unspecified(pytester):
    pytester.makepyfile(
        """
        import pytest
        @pytest.mark.tags('bar')
        def test_tagged1():
            pass
        """
    )
    res = pytester.runpytest("")

    assert "Available tags" not in res.stdout.str()


def test_combine_tags(pytester):
    pytester.makepyfile(
        """
        import pytest
        from pytest_tagging import combine_tags

        combine_tags("new_tag", "foo", "bar")

        @pytest.mark.tags('bar')
        def test_tagged1():
            pass
        @pytest.mark.tags('bar')
        def test_tagged2():
            pass
        @pytest.mark.tags('foo')
        def test_tagged3():
            pass
        """
    )
    res = pytester.runpytest("--tags=new_tag")
    res.assert_outcomes(passed=3)


@pytest.mark.parametrize(
    ("options", "expected_in_output"),
    [
        ("", ".+2 passed.+"),
        ("--tags", ".+Available tags.+"),
        ("--tags=foo", ".+1 passed.+"),
    ],
)
def test_all_states_of_tags_options(pytester, options, expected_in_output):
    """We have different behaviors depending on the content of --tags but also
    if the option is provided at all.

    This test ensures this behaviors are consistent."""

    pytester.makepyfile(
        """
    import pytest
    @pytest.mark.tags('bar')
    def test_tagged2():
        pass
    @pytest.mark.tags('foo')
    def test_tagged3():
        pass
    """
    )
    res = pytester.runpytest(options)
    res.stdout.re_match_lines(expected_in_output)


@pytest.mark.skipif(platform.system() == "Windows", reason="pytest-parallel not supported on Windows")
def test_taggerrunner_with_parallel_with_processes_and_threads(testdir):
    """
    This test ensures counts are collected correctly when tests run in different processes and threads.
    Cannot use `pytest.mark.parametrize` because `testdir` fixture ends up raising a weird
    AssertionError on teardown.
    Ensure this testcase is the last of the tests else it will break all tests because of a bug in pytest-parallel
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


def test_no_tags(pytester):
    """Test that with no tags specified a test is still executed"""
    pytester.makepyfile("def test_pass(): pass")
    res = pytester.runpytest()
    res.assert_outcomes(passed=1)
