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
    def get_storage_provider() -> str:
        """Get storage provider for chuk-artifacts.

        Returns:
            Storage provider type (default: 'vfs-filesystem')

        Provider types:
        - 'vfs-filesystem': VFS-based local filesystem storage (default, works everywhere)
        - 'vfs-memory': VFS-based in-memory storage (testing only)
        - 'vfs-s3': VFS-based S3 storage (production, requires AWS credentials)
        - 'vfs-sqlite': VFS-based SQLite storage
        - 'memory': Legacy in-memory storage
        - 'filesystem': Legacy local filesystem storage

        For Google Drive integration:
        - Use 'vfs-filesystem' (default)
        - Google Drive is enabled via OAuth when GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set
        - chuk-virtual-fs[google_drive] dependency provides the Google Drive VFS provider

        Environment variable:
        - STORAGE_PROVIDER: Storage provider type
        """
        return os.getenv("STORAGE_PROVIDER", "vfs-filesystem")

    @staticmethod
    def get_session_provider() -> str:
        """Get session provider for chuk-sessions.

        Returns:
            Session provider type (default: 'memory')

        Provider types:
        - 'memory': In-memory session storage (default, good for development)
        - 'redis': Redis-based session storage (production, requires REDIS_URL)

        Environment variables:
        - SESSION_PROVIDER: Session provider type
        - REDIS_URL: Redis connection URL (for redis provider)
        """
        return os.getenv("SESSION_PROVIDER", "memory")

    @staticmethod
    def is_google_drive_enabled() -> bool:
        """Check if Google Drive integration should be enabled.

        Returns:
            True if storage provider is vfs-filesystem AND OAuth credentials are configured

        Google Drive is only enabled when:
        1. Storage provider is 'vfs-filesystem' (default)
        2. GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set
        3. chuk-virtual-fs[google_drive] is installed (checked at runtime)
        """
        storage_provider = Config.get_storage_provider()

        # Google Drive only works with vfs-filesystem provider
        if storage_provider != "vfs-filesystem":
            return False

        # Check if OAuth credentials are configured
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        return bool(client_id and client_secret)

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

        Note: Google Drive storage is enabled when:
        1. Storage provider is 'vfs-filesystem' (default)
        2. OAuth is configured (these env vars are set)
        3. User authenticates via OAuth
        4. chuk-virtual-fs[google_drive] is installed
        5. StorageScope.USER is used (automatic when authenticated)
        """
        if not Config.is_google_drive_enabled():
            return None

        # These are guaranteed to be set by is_google_drive_enabled()
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        # Type checker needs explicit check even though is_google_drive_enabled() validates
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
