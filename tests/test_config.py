"""Tests for configuration module."""

import os

from chuk_mcp_stage.config import Config


def test_get_rapier_url_default():
    """Test default Rapier URL."""
    # Clear environment variables
    for key in ["RAPIER_SERVICE_URL", "RAPIER_URL"]:
        if key in os.environ:
            del os.environ[key]

    url = Config.get_rapier_url()
    assert url == "https://rapier.chukai.io"


def test_get_rapier_url_from_service_url_env():
    """Test Rapier URL from RAPIER_SERVICE_URL environment variable."""
    os.environ["RAPIER_SERVICE_URL"] = "http://localhost:9000"

    try:
        url = Config.get_rapier_url()
        assert url == "http://localhost:9000"
    finally:
        del os.environ["RAPIER_SERVICE_URL"]


def test_get_rapier_url_from_alias_env():
    """Test Rapier URL from RAPIER_URL alias."""
    # Ensure RAPIER_SERVICE_URL is not set
    if "RAPIER_SERVICE_URL" in os.environ:
        del os.environ["RAPIER_SERVICE_URL"]

    os.environ["RAPIER_URL"] = "http://custom:8080"

    try:
        url = Config.get_rapier_url()
        assert url == "http://custom:8080"
    finally:
        del os.environ["RAPIER_URL"]


def test_get_rapier_url_service_url_takes_precedence():
    """Test that RAPIER_SERVICE_URL takes precedence over RAPIER_URL."""
    os.environ["RAPIER_SERVICE_URL"] = "http://service:9000"
    os.environ["RAPIER_URL"] = "http://alias:8080"

    try:
        url = Config.get_rapier_url()
        assert url == "http://service:9000"
    finally:
        del os.environ["RAPIER_SERVICE_URL"]
        del os.environ["RAPIER_URL"]


def test_get_rapier_timeout_default():
    """Test default Rapier timeout."""
    if "RAPIER_TIMEOUT" in os.environ:
        del os.environ["RAPIER_TIMEOUT"]

    timeout = Config.get_rapier_timeout()
    assert timeout == 30.0


def test_get_rapier_timeout_from_env():
    """Test Rapier timeout from environment variable."""
    os.environ["RAPIER_TIMEOUT"] = "60.5"

    try:
        timeout = Config.get_rapier_timeout()
        assert timeout == 60.5
    finally:
        del os.environ["RAPIER_TIMEOUT"]


def test_get_rapier_timeout_invalid_falls_back_to_default():
    """Test that invalid timeout value falls back to default."""
    os.environ["RAPIER_TIMEOUT"] = "not-a-number"

    try:
        timeout = Config.get_rapier_timeout()
        assert timeout == 30.0
    finally:
        del os.environ["RAPIER_TIMEOUT"]


def test_get_physics_provider_default():
    """Test default physics provider."""
    if "PHYSICS_PROVIDER" in os.environ:
        del os.environ["PHYSICS_PROVIDER"]

    provider = Config.get_physics_provider()
    assert provider == "auto"


def test_get_physics_provider_from_env():
    """Test physics provider from environment variable."""
    os.environ["PHYSICS_PROVIDER"] = "rapier"

    try:
        provider = Config.get_physics_provider()
        assert provider == "rapier"
    finally:
        del os.environ["PHYSICS_PROVIDER"]


def test_get_physics_provider_lowercase():
    """Test that physics provider is normalized to lowercase."""
    os.environ["PHYSICS_PROVIDER"] = "RAPIER"

    try:
        provider = Config.get_physics_provider()
        assert provider == "rapier"
    finally:
        del os.environ["PHYSICS_PROVIDER"]
