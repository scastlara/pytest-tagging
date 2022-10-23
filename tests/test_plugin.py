import pytest


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
    result.assert_outcomes(passed=1)


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
    result.assert_outcomes(passed=1)


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


def test_taggerrunner_with_parallel_with_threads(testdir):
    """This fails if the taggerrunner is not threadsafe"""
    testdir.makepyfile(
        """
        import pytest

        @pytest.mark.tags('foo')
        def test_tagged_1():
            assert False

        @pytest.mark.tags('foo', 'bar')
        def test_tagged_2():
            assert False
        
        @pytest.mark.tags('bar')
        def test_tagged_3():
            assert False
        
        @pytest.mark.tags('bar')
        def test_tagged_4():
            assert False
    """
    )
    result = testdir.runpytest("--tests-per-worker=2")
    result.stdout.re_match_lines("foo - 2")
    result.stdout.re_match_lines("bar - 3")
