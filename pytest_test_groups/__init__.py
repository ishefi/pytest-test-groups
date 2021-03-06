# -*- coding: utf-8 -*-

# Import python libs
from random import Random
from collections import defaultdict, OrderedDict

# Import 3rd-party libs
from _pytest.config import create_terminal_writer


def get_group(items, group_count, group_id):
    """Get the items from the passed in group based on group count."""
    start = _get_start(group_id, group_count)
    return items[start:len(items):group_count]


def get_file_group(items, group_count, group_id):
    """Get the items from the passed in group, split by files, based on group count."""
    start = _get_start(group_id, group_count)
    modules_to_items = defaultdict(list)

    for item in items:
        modules_to_items[item.module.__file__].append(item)

    sorted_modules_items = sorted(
        modules_to_items.items(),
        key=lambda mod_items: len(mod_items[1]),
        reverse=True
    )

    group_to_items = OrderedDict((i, []) for i in range(group_count))
    for module, items in sorted_modules_items:
        # add largest module to minimal group, based on greedy algorithm from:
        # https://www.ijcai.org/Proceedings/09/Papers/096.pdf
        minimal_group = min(group_to_items.values(), key=lambda items: len(items))
        minimal_group.extend(items)

    return group_to_items[start]


def _get_start(group_id, group_count):
    if not (1 <= group_id <= group_count):
        raise ValueError("Invalid test-group argument")
    return group_id - 1


def pytest_addoption(parser):
    group = parser.getgroup('split your tests into evenly sized groups and run them')
    group.addoption('--test-group-count', dest='test-group-count', type=int,
                    help='The number of groups to split the tests into')
    group.addoption('--test-group', dest='test-group', type=int,
                    help='The group of tests that should be executed')
    group.addoption('--test-group-by-files', dest='group-by-files', action='store_true',
                    help='Group by files instead of collected items')
    group.addoption('--test-group-random-seed', dest='random-seed', type=int,
                    help='Integer to seed pseudo-random test ordering')


def pytest_collection_modifyitems(session, config, items):
    group_count = config.getoption('test-group-count')
    group_id = config.getoption('test-group')
    group_by_files = config.getoption("group-by-files", False)
    seed = config.getoption('random-seed', False)

    if not group_count or not group_id:
        return

    if seed:
        seeded = Random(seed)
        seeded.shuffle(items)

    if group_by_files:
        items[:] = get_file_group(items, group_count, group_id)
    else:
        items[:] = get_group(items, group_count, group_id)

    terminal_reporter = config.pluginmanager.get_plugin('terminalreporter')
    terminal_writer = create_terminal_writer(config)
    message = terminal_writer.markup(
        'Running test group #{0} ({1} tests)\n'.format(
            group_id,
            len(items)
        ),
        yellow=True
    )
    terminal_reporter.write(message)
