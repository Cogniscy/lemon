"""Historical materialized artifacts are optional; unit fixtures are self-contained."""
from pathlib import Path
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "artifacts(*paths): checks optional historical files listed as arguments")


def pytest_runtest_setup(item):
    marker = item.get_closest_marker("artifacts")
    if marker:
        missing = [path for path in marker.args if not Path(path).is_file()]
        if missing:
            pytest.skip("Historical artifacts unavailable: " + ", ".join(missing))
