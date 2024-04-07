# Allows you to combine tags
from pytest_tagging.choices import OperandChoices
from pytest_tagging.utils import TaggingOptions

_combined_tags = {}


def combine_tags(tag_name: str, *args):
    """Combine all tags in `args` into `new_tag`"""
    _combined_tags[tag_name] = args


class TestSelector:
    def __init__(self, config: TaggingOptions) -> None:
        self.config = config

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

    def resolve_combined_tags(self, tags: list[str]) -> set[str]:
        """Resolve all combined tags to return the tags that we want to select."""
        found_combined_tags = set(tags) & set(_combined_tags)
        for tag_name in found_combined_tags:
            tags += _combined_tags[tag_name]
        return set(tags) or set()

    def get_items_to_run(self, tags_to_run, tags_to_exclude, items):
        """Given tags and the pytest items collected, return two sets of items:
        - Those that should be selected.
        - Those that should be deselected.
        """
        selected_items = set()
        deselected_items = set()
        if self.config.tags == [] or (self.config.tags is not None and not tags_to_run):
            # No tags match the conditions to run
            # or we just passed an empty `--tags` options to see them all.
            deselected_items.update(items)
        else:
            # Some tags were selected
            for item in items:
                test_tags = get_tags_from_item(item)
                # Excluding tags takes precendence ove any selection.
                if test_tags & tags_to_exclude:
                    deselected_items.add(item)
                elif (self.config.operand is OperandChoices.OR and test_tags & tags_to_run) or (
                    self.config.operand is OperandChoices.AND and tags_to_run <= test_tags
                ):
                    selected_items.add(item)
                else:
                    deselected_items.add(item)
        return list(selected_items), list(deselected_items)


def get_tags_from_item(item) -> set[str]:
    return set(item.get_closest_marker("tags").args) if item.get_closest_marker("tags") else set()
