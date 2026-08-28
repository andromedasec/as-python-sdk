"""Local pytest config for the SDK test suite.

These tests are usually collected via `make test` in services/ai-agent, whose
pytest.ini registers the shared markers. Register `live` here as well so the
suite is also clean when run directly from lib/python (where that ini is not
picked up) — otherwise `--strict-markers` turns the marker into an error.
"""


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "live: tests that require a running apiserver and tenant credentials",
    )
