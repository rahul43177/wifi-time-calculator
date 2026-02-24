"""Pytest configuration and shared markers."""


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "mongodb: Tests using MongoDB backend (integration tests)"
    )
