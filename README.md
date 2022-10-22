![tests](https://github.com/scastlara/pytest-tagging/actions/workflows/tests.yml/badge.svg?branch=main)
[![PyPI version](https://badge.fury.io/py/pytest-tagging.svg)](https://badge.fury.io/py/pytest-tagging)

# pytest-tagging
[pytest](https://docs.pytest.org/en/7.1.x/) plugin that allows tagging tests using arbitrary strings.

It supports selecting only tests with a specific tag, and display a counter of how many tests failed
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


## Extra
- It is thread-safe, so it can be used with [pytest-parallel](https://github.com/browsertron/pytest-parallel).
