"""Guard: skip plugin integration tests if plugin/dist/ appears stale."""

from tests.dist_guard import skip_if_dist_stale


def pytest_collection_modifyitems(config, items):
    plugin_items = [i for i in items if "tests/integration/plugin" in str(i.fspath)]
    skip_if_dist_stale(plugin_items)
