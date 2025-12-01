# Google Drive OAuth Integration

Complete guide to Google Drive OAuth 2.1 integration in chuk-mcp-stage.

## Overview

chuk-mcp-stage now supports **user-owned persistent storage** via Google Drive with OAuth 2.1 authentication. Scenes are stored in the user's own Google Drive, giving them full control over their data.

## Architecture

**Two-Layer Authentication:**

```
┌──────────────┐     OAuth 2.1      ┌──────────────┐     Google OAuth    ┌──────────────┐
│              │ ◄─────────────────► │              │ ◄─────────────────► │              │
│   Claude     │   MCP Access Token  │ chuk-mcp-    │  Google Tokens     │   Google     │
│   Desktop    │                     │   stage      │                     │   Drive      │
│              │                     │              │                     │              │
└──────────────┘                     └──────────────┘                     └──────────────┘
```

**Token Flow:**

1. **MCP Layer**: Claude Desktop ↔ chuk-mcp-stage
   - Short-lived access tokens (15 min)
   - Refresh tokens (1 day)
   - Managed by chuk-sessions (memory or Redis)

2. **Google Layer**: chuk-mcp-stage ↔ Google Drive
   - Google access tokens (stored server-side)
   - Auto-refreshed when expired
   - User authorizes once via browser

## Quick Start

### 1. Setup Google Cloud Project

```bash
# Go to https://console.cloud.google.com/
# 1. Create project (or select existing)
# 2. Enable Google Drive API
# 3. Create OAuth 2.0 Client ID (Web application)
# 4. Add redirect URI: http://localhost:8000/oauth/callback
# 5. Copy Client ID and Secret
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add credentials:
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 3. Install Dependencies

```bash
pip install -e ".[google_drive]"
```

### 4. Verify OAuth Setup

```bash
# Verify OAuth integration works
python examples/verify_google_drive_oauth.py
```

Expected output:
```
======================================================================
Google Drive OAuth Integration Test Suite
======================================================================

Test 1: OAuth Provider Initialization
======================================================================
✓ Found GOOGLE_CLIENT_ID: ...
✓ Found GOOGLE_CLIENT_SECRET: ...
✓ OAuth provider created successfully

Test 2: OAuth Setup Helper
======================================================================
✓ OAuth hook created successfully
✓ OAuth middleware initialized

...

🎉 All tests passed! OAuth integration is working correctly.
```

### 5. Run Server

```bash
# HTTP mode (required for OAuth)
uv run chuk-mcp-stage http
```

### 6. Authorize

When MCP client connects:
1. Browser opens for Google authorization
2. User grants access to Google Drive
3. Tokens stored securely
4. Scenes stored in `/CHUK/stage/` in user's Drive

## OAuth Endpoints

Automatically registered when server runs in HTTP mode with Google credentials:

- **Discovery**: `http://localhost:8000/.well-known/oauth-authorization-server`
- **Authorization**: `http://localhost:8000/oauth/authorize`
- **Token**: `http://localhost:8000/oauth/token`
- **Register**: `http://localhost:8000/oauth/register`
- **Callback**: `http://localhost:8000/oauth/callback`

## Reusable Provider

The Google Drive OAuth provider is implemented as a **reusable component** in `chuk-mcp-server`:

```python
from chuk_mcp_server import ChukMCPServer, run
from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth

mcp = ChukMCPServer("my-server")

# ... register tools ...

# ONE LINE: Add Google Drive OAuth!
oauth_hook = setup_google_drive_oauth(mcp)

run(transport="http", port=8000, post_register_hook=oauth_hook)
```

Any MCP server can use this provider by:
1. Installing: `pip install chuk-mcp-server[google_drive]`
2. Setting environment variables
3. Calling `setup_google_drive_oauth(mcp)`

See: `/mcp-servers/chuk-mcp-server/docs/OAUTH_PROVIDERS.md`

## Environment Variables

**Required:**
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret

**Optional (with defaults):**
- `GOOGLE_REDIRECT_URI` - OAuth callback (default: `http://localhost:8000/oauth/callback`)
- `OAUTH_SERVER_URL` - Server base URL (default: `http://localhost:8000`)
- `GOOGLE_DRIVE_ROOT_FOLDER` - Root folder in Drive (default: `CHUK`)
- `GOOGLE_DRIVE_CACHE_TTL` - Cache TTL in seconds (default: `60`)

**Session Backend (Production):**
- `SESSION_PROVIDER` - `memory` (default) or `redis` (production)
- `SESSION_REDIS_URL` - Redis URL (if using Redis)

**Token TTLs (Advanced):**
- `OAUTH_AUTH_CODE_TTL` - Authorization code lifetime (default: 300s / 5 min)
- `OAUTH_ACCESS_TOKEN_TTL` - Access token lifetime (default: 900s / 15 min)
- `OAUTH_REFRESH_TOKEN_TTL` - Refresh token lifetime (default: 86400s / 1 day)
- `OAUTH_EXTERNAL_TOKEN_TTL` - Google token TTL (default: 86400s / 1 day)

## Deployment

### Local Development

```bash
# Use .env file
cp .env.example .env
# Edit .env with credentials
uv run chuk-mcp-stage http
```

### Fly.io Production

```bash
# Set secrets
fly secrets set GOOGLE_CLIENT_ID="..."
fly secrets set GOOGLE_CLIENT_SECRET="..."
fly secrets set OAUTH_SERVER_URL="https://your-app.fly.dev"
fly secrets set GOOGLE_REDIRECT_URI="https://your-app.fly.dev/oauth/callback"

# Optional: Redis for production token storage
fly secrets set SESSION_PROVIDER="redis"
fly secrets set SESSION_REDIS_URL="redis://..."

# Deploy
fly deploy
```

**Important**: Update Google Cloud Console redirect URIs:
- Development: `http://localhost:8000/oauth/callback`
- Production: `https://your-app.fly.dev/oauth/callback`

## Data Storage

Scenes are stored in user's Google Drive:

```
Google Drive
└── CHUK/
    └── stage/
        ├── scene-abc123/
        │   ├── scene.json
        │   ├── baked_animations.json
        │   └── exports/
        │       ├── r3f_component.tsx
        │       └── scene.gltf
        └── scene-def456/
            └── scene.json
```

Users can:
- ✅ View/edit files in Google Drive UI
- ✅ Share scenes with collaborators
- ✅ Access from any device
- ✅ Download/backup locally
- ✅ Own their data completely

## Security

### OAuth 2.1 Compliance

✅ **PKCE** (Proof Key for Code Exchange) - All flows use S256 challenge
✅ **Short-Lived Tokens** - Access tokens expire in 15 minutes
✅ **Refresh Tokens** - Automatic token refresh (1 day TTL)
✅ **Secure Storage** - Tokens stored server-side, never sent to client
✅ **State Parameter** - CSRF protection on all flows

### MCP Specification Compliance

✅ **RFC 8414** - OAuth Authorization Server Metadata
✅ **RFC 9728** - OAuth Protected Resource Metadata
✅ **SEP-835** - Incremental scope consent
✅ **SEP-991** - Dynamic Client Registration (DCR)
✅ **November 2025 MCP Spec** - Latest authorization enhancements

### Best Practices

1. **Environment Variables** - Never hardcode credentials
2. **HTTPS in Production** - Use TLS for all OAuth endpoints
3. **Minimal Scopes** - Only request `drive.file` (own files only)
4. **Token Rotation** - Tokens auto-refresh before expiry
5. **Sandbox Isolation** - Multi-tenant token separation
6. **Audit Logging** - OAuth events logged for security monitoring

## Troubleshooting

### Browser doesn't open

**Problem**: OAuth flow doesn't redirect to Google

**Solutions**:
- OAuth only works in **HTTP mode**, not STDIO
- Run: `uv run chuk-mcp-stage http`
- Check port 8000 is not blocked by firewall

### Invalid redirect URI

**Problem**: Google shows "redirect_uri_mismatch" error

**Solutions**:
- Ensure exact match in Google Cloud Console
- Protocol must match (http vs https)
- Port must match (include :8000 for local)
- Check: `http://localhost:8000/oauth/callback`

### Missing credentials

**Problem**: Server starts but OAuth not configured

**Solutions**:
- Check `.env` file exists and has credentials
- Verify environment variables: `echo $GOOGLE_CLIENT_ID`
- Run verification script: `python examples/verify_google_drive_oauth.py`

### Access blocked error

**Problem**: Google shows "This app isn't verified"

**Solutions**:
- Add your email as test user in OAuth consent screen
- Or complete Google's verification process
- Development apps limited to 100 test users

### Token expired

**Problem**: Requests fail with invalid_token error

**Solutions**:
- Tokens auto-refresh, but may need re-authorization
- Check server logs for refresh errors
- User may need to re-authorize via browser
- Verify `OAUTH_EXTERNAL_TOKEN_TTL` is set correctly

## Files Created

### chuk-mcp-server (Reusable Provider)
- `src/chuk_mcp_server/oauth/providers/google_drive.py` - Provider implementation
- `src/chuk_mcp_server/oauth/providers/__init__.py` - Provider registry
- `src/chuk_mcp_server/oauth/helpers.py` - Setup helpers
- `docs/OAUTH_PROVIDERS.md` - Provider documentation
- `pyproject.toml` - Added `google_drive` optional dependency

### chuk-mcp-stage (Integration)
- `.env.example` - Environment template with all variables
- `examples/verify_google_drive_oauth.py` - OAuth integration verification script
- `GOOGLE_DRIVE_OAUTH.md` - This guide
- `README.md` - Updated with OAuth setup instructions
- `pyproject.toml` - Google Drive dependency
- `src/chuk_mcp_stage/server.py` - OAuth integration (3 lines!)
- `src/chuk_mcp_stage/config.py` - Config helpers

## Next Steps

1. **Verify Locally**: Run verification script and check OAuth flow
2. **Create First Scene**: Use chuk-mcp-stage tools to create a scene
3. **Verify Storage**: Check Google Drive for `/CHUK/stage/` folder
4. **Deploy to Fly.io**: Set secrets and deploy to production
5. **Share Scenes**: Use Google Drive sharing to collaborate

## Resources

- **MCP OAuth Spec**: https://modelcontextprotocol.io/specification/2025-11-25/authorization
- **Google OAuth Guide**: https://developers.google.com/identity/protocols/oauth2
- **chuk-mcp-server Docs**: `/mcp-servers/chuk-mcp-server/docs/OAUTH.md`
- **OAuth Providers**: `/mcp-servers/chuk-mcp-server/docs/OAUTH_PROVIDERS.md`
- **chuk-virtual-fs**: Google Drive provider documentation

## Support

For issues or questions:
- Check troubleshooting section above
- Review verification script output
- Check server logs for OAuth errors
- See chuk-mcp-server OAuth documentation

## License

MIT
