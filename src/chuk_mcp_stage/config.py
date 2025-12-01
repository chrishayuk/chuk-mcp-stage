"""Configuration for chuk-mcp-stage.

Handles environment variables and default settings.
"""

import os


class Config:
    """Configuration for Stage MCP Server."""

    # Default Rapier physics service (public)
    DEFAULT_RAPIER_URL = "https://rapier.chukai.io"

    @staticmethod
    def get_rapier_url() -> str:
        """Get Rapier service URL from environment or use default.

        Environment variables checked (in order):
        1. RAPIER_SERVICE_URL - Full service URL
        2. RAPIER_URL - Alias for service URL

        Returns:
            Rapier service URL (defaults to public service)

        Examples:
            # Use public service (default)
            url = Config.get_rapier_url()  # https://rapier.chukai.io

            # Use custom service via environment
            export RAPIER_SERVICE_URL=http://localhost:9000
            url = Config.get_rapier_url()  # http://localhost:9000
        """
        return (
            os.getenv("RAPIER_SERVICE_URL") or os.getenv("RAPIER_URL") or Config.DEFAULT_RAPIER_URL
        )

    @staticmethod
    def get_rapier_timeout() -> float:
        """Get Rapier service timeout in seconds.

        Returns:
            Timeout in seconds (default 30.0)
        """
        try:
            return float(os.getenv("RAPIER_TIMEOUT", "30.0"))
        except ValueError:
            return 30.0

    @staticmethod
    def get_physics_provider() -> str:
        """Get physics provider type.

        Returns:
            Provider type: 'rapier', 'mcp', or 'auto' (default)

        Provider types:
        - 'rapier': Use Rapier HTTP service directly (fastest for simulations)
        - 'mcp': Use chuk-mcp-physics tools (flexible, supports analytic too)
        - 'auto': Auto-detect based on available services (default)
        """
        return os.getenv("PHYSICS_PROVIDER", "auto").lower()

    @staticmethod
    def get_google_drive_config() -> dict[str, str] | None:
        """Get Google Drive OAuth configuration.

        Returns:
            Dict with client_id, client_secret, redirect_uri or None if not configured

        Environment variables:
        - GOOGLE_CLIENT_ID: Google OAuth client ID
        - GOOGLE_CLIENT_SECRET: Google OAuth client secret
        - GOOGLE_REDIRECT_URI: OAuth callback URL (default: http://localhost:8000/oauth/callback)
        - OAUTH_SERVER_URL: OAuth server base URL (default: http://localhost:8000)
        """
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        if not client_id or not client_secret:
            return None

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": os.getenv(
                "GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/callback"
            ),
            "oauth_server_url": os.getenv("OAUTH_SERVER_URL", "http://localhost:8000"),
        }
