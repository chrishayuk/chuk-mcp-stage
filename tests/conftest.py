"""Pytest configuration."""


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "vfs_integration: mark test as requiring VFS integration (deselect if flaky)"
    )
