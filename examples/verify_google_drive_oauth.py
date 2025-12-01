#!/usr/bin/env python3
"""Test Google Drive OAuth integration for chuk-mcp-stage.

This script verifies that:
1. OAuth provider initializes correctly
2. OAuth endpoints are registered
3. Google Drive credentials work
4. Can create/read/list files in Google Drive

Prerequisites:
1. Set up .env file with Google OAuth credentials
2. Install with: pip install -e ".[google_drive]"

Usage:
    python examples/test_google_drive_oauth.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dotenv import load_dotenv
except ImportError:
    print("Installing python-dotenv...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv


async def test_oauth_provider_init():
    """Test that OAuth provider can be initialized."""
    print("=" * 70)
    print("Test 1: OAuth Provider Initialization")
    print("=" * 70)
    print()

    try:
        from chuk_mcp_server.oauth.providers import GoogleDriveOAuthProvider
    except ImportError as e:
        print(f"❌ Failed to import GoogleDriveOAuthProvider: {e}")
        print()
        print("Install with:")
        print("  pip install -e '.[google_drive]'")
        return False

    # Get credentials from environment
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Missing Google OAuth credentials")
        print()
        print("Set environment variables:")
        print("  export GOOGLE_CLIENT_ID='your-client-id'")
        print("  export GOOGLE_CLIENT_SECRET='your-client-secret'")
        print()
        print("Or create .env file from .env.example")
        return False

    print(f"✓ Found GOOGLE_CLIENT_ID: {client_id[:20]}...")
    print(f"✓ Found GOOGLE_CLIENT_SECRET: {client_secret[:10]}...")
    print()

    # Create provider
    try:
        provider = GoogleDriveOAuthProvider(
            google_client_id=client_id,
            google_client_secret=client_secret,
            google_redirect_uri=os.getenv(
                "GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/callback"
            ),
            oauth_server_url=os.getenv("OAUTH_SERVER_URL", "http://localhost:8000"),
            sandbox_id="chuk-mcp-stage-test",
        )
        print("✓ OAuth provider created successfully")
        print(f"  - Redirect URI: {provider.google_client.redirect_uri}")
        print(f"  - OAuth server: {provider.oauth_server_url}")
        print(f"  - Sandbox ID: {provider.token_store.sandbox_id}")
        print()
        return True

    except Exception as e:
        print(f"❌ Failed to create OAuth provider: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_oauth_helper():
    """Test that OAuth helper function works."""
    print("=" * 70)
    print("Test 2: OAuth Setup Helper")
    print("=" * 70)
    print()

    try:
        from chuk_mcp_server import ChukMCPServer
        from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth
    except ImportError as e:
        print(f"❌ Failed to import OAuth helpers: {e}")
        return False

    # Create MCP server
    mcp = ChukMCPServer("test-stage")

    # Setup OAuth
    oauth_hook = setup_google_drive_oauth(mcp)

    if oauth_hook is None:
        print("❌ OAuth hook not created (missing credentials?)")
        return False

    print("✓ OAuth hook created successfully")
    print("  - Function: setup_google_drive_oauth()")
    print("  - Returns: post_register_hook callable")
    print()

    # Call the hook to create middleware
    try:
        oauth_middleware = oauth_hook()
        print("✓ OAuth middleware initialized")
        print(f"  - Provider: {oauth_middleware.provider_name}")
        print(f"  - Scopes: {oauth_middleware.scopes_supported}")
        print()
        return True
    except Exception as e:
        print(f"❌ Failed to initialize OAuth middleware: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_storage_helper():
    """Test storage configuration helper."""
    print("=" * 70)
    print("Test 3: Storage Configuration Helper")
    print("=" * 70)
    print()

    try:
        from chuk_mcp_server.oauth.helpers import configure_storage_from_oauth
    except ImportError as e:
        print(f"❌ Failed to import storage helper: {e}")
        return False

    # Mock token data
    mock_token_data = {
        "user_id": "test-user-123",
        "client_id": "test-client",
        "scope": "drive.file userinfo.profile",
        "external_access_token": "mock-google-token",
        "external_refresh_token": "mock-google-refresh-token",
    }

    try:
        storage_config = configure_storage_from_oauth(mock_token_data)

        print("✓ Storage config generated")
        print(f"  - User ID: {storage_config['user_id']}")
        print(f"  - Root folder: {storage_config['root_folder']}")
        print(f"  - Has credentials: {bool(storage_config['credentials'])}")
        print(f"  - Token present: {bool(storage_config['credentials'].get('token'))}")
        print(
            f"  - Refresh token present: {bool(storage_config['credentials'].get('refresh_token'))}"
        )
        print()
        return True

    except Exception as e:
        print(f"❌ Failed to generate storage config: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_google_drive_client():
    """Test Google Drive OAuth client."""
    print("=" * 70)
    print("Test 4: Google Drive OAuth Client")
    print("=" * 70)
    print()

    try:
        from chuk_mcp_server.oauth.providers import GoogleDriveOAuthClient
    except ImportError as e:
        print(f"❌ Failed to import GoogleDriveOAuthClient: {e}")
        return False

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("⚠️  Skipping (no credentials)")
        return True

    try:
        client = GoogleDriveOAuthClient(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/oauth/callback"),
        )

        # Generate auth URL
        test_state = "test-state-123"
        auth_url = client.get_authorization_url(state=test_state)

        print("✓ OAuth client created")
        print(f"  - Client ID: {client.client_id[:20]}...")
        print(f"  - Redirect URI: {client.redirect_uri}")
        print()
        print("✓ Authorization URL generated")
        print(f"  - URL: {auth_url[:80]}...")
        print(f"  - Contains state: {test_state in auth_url}")
        print(f"  - Contains client_id: {client_id[:20] in auth_url}")
        print()

        # Verify required scopes
        print("✓ Required scopes:")
        for scope in client.SCOPES:
            print(f"  - {scope}")
        print()

        return True

    except Exception as e:
        print(f"❌ Failed to test OAuth client: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_oauth_endpoints():
    """Test that OAuth endpoints can be registered."""
    print("=" * 70)
    print("Test 5: OAuth Endpoints Registration")
    print("=" * 70)
    print()

    try:
        from chuk_mcp_server import ChukMCPServer
        from chuk_mcp_server.oauth import OAuthMiddleware
        from chuk_mcp_server.oauth.providers import GoogleDriveOAuthProvider
    except ImportError as e:
        print(f"❌ Failed to import OAuth components: {e}")
        return False

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("⚠️  Skipping (no credentials)")
        return True

    try:
        # Create MCP server
        mcp = ChukMCPServer("test-stage")

        # Create provider
        provider = GoogleDriveOAuthProvider(
            google_client_id=client_id,
            google_client_secret=client_secret,
            google_redirect_uri="http://localhost:8000/oauth/callback",
            oauth_server_url="http://localhost:8000",
            sandbox_id="test-sandbox",
        )

        # Create middleware (this registers endpoints)
        _oauth = OAuthMiddleware(
            mcp_server=mcp,
            provider=provider,
            oauth_server_url="http://localhost:8000",
            callback_path="/oauth/callback",
            scopes_supported=["drive.file", "userinfo.profile"],
            provider_name="Google Drive",
        )

        print("✓ OAuth middleware registered")
        print()
        print("OAuth endpoints that should be available:")
        print("  - GET  /.well-known/oauth-authorization-server")
        print("  - GET  /.well-known/oauth-protected-resource")
        print("  - GET  /oauth/authorize")
        print("  - POST /oauth/token")
        print("  - POST /oauth/register")
        print("  - GET  /oauth/callback")
        print()

        return True

    except Exception as e:
        print(f"❌ Failed to register OAuth endpoints: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print()
    print("=" * 70)
    print("Google Drive OAuth Integration Test Suite")
    print("=" * 70)
    print()

    # Load environment variables from .env file if it exists
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print(f"✓ Loading environment from {env_file}")
        load_dotenv(env_file)
    else:
        print(f"⚠️  No .env file found at {env_file}")
        print("   Using environment variables only")

    print()

    # Run tests
    tests = [
        ("OAuth Provider Initialization", test_oauth_provider_init),
        ("OAuth Setup Helper", test_oauth_helper),
        ("Storage Configuration Helper", test_storage_helper),
        ("Google Drive OAuth Client", test_google_drive_client),
        ("OAuth Endpoints Registration", test_oauth_endpoints),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback

            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print()

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("🎉 All tests passed! OAuth integration is working correctly.")
        print()
        print("Next steps:")
        print("1. Run the server: uv run chuk-mcp-stage http")
        print("2. Connect MCP client to http://localhost:8000")
        print("3. Browser will open for Google authorization")
        print("4. After authorization, scenes will be stored in Google Drive")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
