"""Guard: skip build tests if plugin/dist/ appears stale."""

from tests.dist_guard import skip_if_dist_stale


def pytest_collection_modifyitems(config, items):
    build_items = [i for i in items if "tests/build" in str(i.fspath)]
    skip_if_dist_stale(build_items)
