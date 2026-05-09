import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires live DB, Redis, Celery, Qdrant")
