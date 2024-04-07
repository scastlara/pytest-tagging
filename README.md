![Build Status](https://github.com/scastlara/pytest-tagging/actions/workflows/tests.yml/badge.svg)
[![PyPI version](https://img.shields.io/pypi/v/pytest-tagging)](https://pypi.org/project/pytest-tagging/)
[![Python Version](https://img.shields.io/pypi/pyversions/pytest-tagging?logo=python&logoColor=yellow)](https://pypi.org/project/pytest-tagging/)
![Code style](https://img.shields.io/badge/code%20style-black-000000.svg)
[![License](https://img.shields.io/github/license/scastlara/pytest-tagging)](LICENSE)

# pytest-tagging
[pytest](https://docs.pytest.org/en/7.1.x/) plugin that allows tagging tests using arbitrary strings.

It supports selecting only tests with a specific tag, and displays a counter of how many tests failed
for each specific tag.

This package exists because doing all of this with `pytest.mark` is painful, since it requires registering marks, 
and you cannot use variables defined elsewhere easily.

## Usage

```python
@pytest.mark.tags("JIRA-XX", "integration", constants.COMPONENT_X)
def test_foo():
    assert False
```

Invocation:

```sh
pytest --tags integration --tags MY_COMPONENT_NAME
```

![pytest-tagging-screenshot](/media/screenshot-1.png)

By default, all tests that match at least one tag will be collected. To only select
tests that have all the provided tags, use the option --tags-operand=AND, like so:

```sh
pytest --tags integration --tags MY_COMPONENT_NAME --tags-operand AND
```

You can also display all available tags by specifying `--tags` empty:

```sh
pytest --tags
>>Available tags:
>>foo
>>bar
```

### Combining tags

Tags can be combined using `pytest_tagging.combine_tags`:

```python
from pytest_tagging import combine_tags
combine_tags("all", "foo", "bar")
```

Then you can execute `pytest --tags all` and it will run all tests with `foo` and `bar` tags

### Excluding tags

You can exclude tags for a particular test run by using the option `--exclude-tags` in a similar
way to the `--tags` option. Notice tests with tags that are excluded will not be executed, even if
they contain a tag that was selected with `--tags`.

```sh
pytest --tags mobile --tags web --exclude-tags flaky
```

## Extra

- It is thread-safe, so it can be used with [pytest-parallel](https://github.com/browsertron/pytest-parallel).
