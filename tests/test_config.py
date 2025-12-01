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


def test_get_google_drive_config_not_configured():
    """Test Google Drive config when credentials not set."""
    # Clear all Google Drive environment variables
    for key in [
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "GOOGLE_REDIRECT_URI",
        "OAUTH_SERVER_URL",
    ]:
        if key in os.environ:
            del os.environ[key]

    config = Config.get_google_drive_config()
    assert config is None


def test_get_google_drive_config_missing_client_id():
    """Test Google Drive config returns None when client_id is missing."""
    # Clear client_id but set client_secret
    if "GOOGLE_CLIENT_ID" in os.environ:
        del os.environ["GOOGLE_CLIENT_ID"]
    os.environ["GOOGLE_CLIENT_SECRET"] = "test-secret"

    try:
        config = Config.get_google_drive_config()
        assert config is None
    finally:
        del os.environ["GOOGLE_CLIENT_SECRET"]


def test_get_google_drive_config_missing_client_secret():
    """Test Google Drive config returns None when client_secret is missing."""
    # Set client_id but clear client_secret
    os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
    if "GOOGLE_CLIENT_SECRET" in os.environ:
        del os.environ["GOOGLE_CLIENT_SECRET"]

    try:
        config = Config.get_google_drive_config()
        assert config is None
    finally:
        del os.environ["GOOGLE_CLIENT_ID"]


def test_get_google_drive_config_with_defaults():
    """Test Google Drive config with minimal configuration (uses defaults)."""
    os.environ["GOOGLE_CLIENT_ID"] = "test-client-id.apps.googleusercontent.com"
    os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"

    # Clear optional variables to test defaults
    for key in ["GOOGLE_REDIRECT_URI", "OAUTH_SERVER_URL"]:
        if key in os.environ:
            del os.environ[key]

    try:
        config = Config.get_google_drive_config()
        assert config is not None
        assert config["client_id"] == "test-client-id.apps.googleusercontent.com"
        assert config["client_secret"] == "test-client-secret"
        assert config["redirect_uri"] == "http://localhost:8000/oauth/callback"
        assert config["oauth_server_url"] == "http://localhost:8000"
    finally:
        del os.environ["GOOGLE_CLIENT_ID"]
        del os.environ["GOOGLE_CLIENT_SECRET"]


def test_get_google_drive_config_with_custom_values():
    """Test Google Drive config with all custom values."""
    os.environ["GOOGLE_CLIENT_ID"] = "custom-client-id"
    os.environ["GOOGLE_CLIENT_SECRET"] = "custom-secret"
    os.environ["GOOGLE_REDIRECT_URI"] = "https://example.com/callback"
    os.environ["OAUTH_SERVER_URL"] = "https://oauth.example.com"

    try:
        config = Config.get_google_drive_config()
        assert config is not None
        assert config["client_id"] == "custom-client-id"
        assert config["client_secret"] == "custom-secret"
        assert config["redirect_uri"] == "https://example.com/callback"
        assert config["oauth_server_url"] == "https://oauth.example.com"
    finally:
        for key in [
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI",
            "OAUTH_SERVER_URL",
        ]:
            if key in os.environ:
                del os.environ[key]


def test_get_google_drive_config_partial_custom():
    """Test Google Drive config with partial custom values."""
    os.environ["GOOGLE_CLIENT_ID"] = "partial-client-id"
    os.environ["GOOGLE_CLIENT_SECRET"] = "partial-secret"
    os.environ["GOOGLE_REDIRECT_URI"] = "https://custom.redirect.com/auth"
    # Don't set OAUTH_SERVER_URL - should use default

    if "OAUTH_SERVER_URL" in os.environ:
        del os.environ["OAUTH_SERVER_URL"]

    try:
        config = Config.get_google_drive_config()
        assert config is not None
        assert config["client_id"] == "partial-client-id"
        assert config["client_secret"] == "partial-secret"
        assert config["redirect_uri"] == "https://custom.redirect.com/auth"
        assert config["oauth_server_url"] == "http://localhost:8000"  # Default
    finally:
        for key in ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"]:
            if key in os.environ:
                del os.environ[key]
