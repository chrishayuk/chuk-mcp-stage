# Transport Modes Guide

chuk-mcp-stage supports three transport modes for different use cases:

## 1. STDIO Mode (Default)

**Use case**: Claude Desktop, MCP CLI tools, and other MCP-compatible clients

**How to run**:
```bash
uv run chuk-mcp-stage
# or
python -m chuk_mcp_stage.server
```

**Characteristics**:
- Uses stdin/stdout for JSON-RPC communication
- Default mode when no arguments provided
- Compatible with MCP specification
- Logging suppressed to avoid polluting the JSON-RPC stream
- All logs go to stderr only

**Claude Desktop configuration**:
```json
{
  "mcpServers": {
    "stage": {
      "command": "uv",
      "args": ["run", "chuk-mcp-stage"]
    }
  }
}
```

**Example client usage**:
```bash
# Using mcp-cli
mcp-cli connect "uv run chuk-mcp-stage"
```

---

## 2. HTTP Mode

**Use case**: REST API access, integration with web services, chuk-mcp-r3f-preview

**How to run**:
```bash
uv run chuk-mcp-stage http
# or
python -m chuk_mcp_stage.server http
```

**Characteristics**:
- HTTP REST API server
- Runs on `http://0.0.0.0:8000`
- Accepts POST requests to `/tools/{tool_name}`
- Returns JSON responses
- Logging enabled (warnings and errors)

**HTTP API endpoints**:
```
POST http://localhost:8000/tools/stage_create_scene
POST http://localhost:8000/tools/stage_add_object
POST http://localhost:8000/tools/stage_add_shot
POST http://localhost:8000/tools/stage_bind_physics
POST http://localhost:8000/tools/stage_bake_simulation
POST http://localhost:8000/tools/stage_export_scene
POST http://localhost:8000/tools/stage_get_scene
POST http://localhost:8000/tools/stage_get_shot
POST http://localhost:8000/tools/stage_set_environment
```

**Example HTTP request**:
```bash
curl -X POST http://localhost:8000/tools/stage_create_scene \
  -H "Content-Type: application/json" \
  -d '{
    "name": "demo-scene",
    "author": "Claude",
    "description": "Example scene"
  }'
```

**Response**:
```json
{
  "scene_id": "scene-abc12345",
  "message": "Scene 'demo-scene' created"
}
```

**Used by**:
- chuk-mcp-r3f-preview (Vite MCP proxy plugin)
- Custom integrations
- Testing and debugging

---

## 3. Streamable Mode (SSE)

**Use case**: Server-Sent Events for streaming responses, real-time updates

**How to run**:
```bash
uv run chuk-mcp-stage streamable
# or
python -m chuk_mcp_stage.server streamable
```

**Characteristics**:
- Server-Sent Events (SSE) transport
- Streaming responses for long-running operations
- Real-time progress updates
- Compatible with EventSource API in browsers

**When to use**:
- Long-running operations (physics baking, exports)
- Real-time progress tracking
- Web-based clients that need streaming
- Applications requiring incremental results

**Example client** (JavaScript):
```javascript
const eventSource = new EventSource('http://localhost:8000/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data);
};
```

---

## Transport Mode Comparison

| Feature | STDIO | HTTP | Streamable |
|---------|-------|------|------------|
| **Protocol** | JSON-RPC | REST | SSE |
| **Use case** | MCP clients | Web services | Streaming |
| **Port** | N/A | 8000 | 8000 |
| **Logging** | Suppressed | Enabled | Enabled |
| **Streaming** | No | No | Yes |
| **Claude Desktop** | ✅ Yes | ❌ No | ❌ No |
| **Web browser** | ❌ No | ✅ Yes | ✅ Yes |
| **Progress updates** | Limited | Polling | Real-time |

---

## Choosing the Right Transport

### Use **STDIO** when:
- Integrating with Claude Desktop
- Using MCP CLI tools
- Running as a standard MCP server
- Don't need HTTP access

### Use **HTTP** when:
- Building web applications
- Need REST API access
- Integrating with non-MCP clients
- Testing with curl/Postman
- Running chuk-mcp-r3f-preview

### Use **Streamable** when:
- Need real-time progress updates
- Long-running operations (physics baking)
- Web-based clients with EventSource
- Streaming responses required

---

## Running Multiple Instances

You can run different transport modes simultaneously on different machines/containers:

**Terminal 1** (STDIO for Claude Desktop):
```bash
# In Claude Desktop config
uv run chuk-mcp-stage
```

**Terminal 2** (HTTP for web services):
```bash
uv run chuk-mcp-stage http
```

**Terminal 3** (Streamable for streaming clients):
```bash
uv run chuk-mcp-stage streamable
```

**Note**: HTTP and Streamable modes both use port 8000 by default, so they cannot run simultaneously on the same machine without port configuration.

---

## Environment Variables

All transport modes support these environment variables:

```bash
# Logging level (DEBUG, INFO, WARNING, ERROR)
export LOG_LEVEL=WARNING

# Custom port for HTTP/Streamable modes (future enhancement)
# export MCP_STAGE_PORT=8080
```

---

## Troubleshooting

### STDIO mode issues

**Problem**: Server doesn't respond in Claude Desktop

**Solutions**:
1. Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log`
2. Test server manually: `echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | uv run chuk-mcp-stage`
3. Verify Python/uv version: `uv --version` and `python --version`

### HTTP mode issues

**Problem**: Port 8000 already in use

**Solutions**:
1. Check what's using port 8000: `lsof -i :8000`
2. Kill the process: `kill -9 <PID>`
3. Use a different port (future: environment variable support)

**Problem**: Connection refused

**Solutions**:
1. Verify server is running: `curl http://localhost:8000/health`
2. Check firewall settings
3. Verify no errors in server logs

### Streamable mode issues

**Problem**: No events received

**Solutions**:
1. Verify EventSource connection: Check browser console
2. Test with curl: `curl -N http://localhost:8000/stream`
3. Check CORS settings if calling from browser

---

## API Compatibility

All transport modes expose the same 9 MCP tools:

1. `stage_create_scene` - Create a new 3D scene
2. `stage_add_object` - Add object to scene
3. `stage_add_shot` - Add camera shot
4. `stage_set_environment` - Configure environment/lighting
5. `stage_bind_physics` - Bind object to physics body
6. `stage_bake_simulation` - Bake physics to keyframes
7. `stage_export_scene` - Export to R3F/Remotion/glTF
8. `stage_get_scene` - Get complete scene data
9. `stage_get_shot` - Get shot details

The same function signatures and response formats are used across all transports.

---

## Security Considerations

### STDIO mode
- ✅ No network exposure
- ✅ Only accessible via process stdin/stdout
- ✅ Secure by default

### HTTP mode
- ⚠️ Binds to 0.0.0.0 (all interfaces)
- ⚠️ No authentication by default
- ⚠️ Use firewall rules for production
- 💡 Recommended: Run behind reverse proxy with auth

### Streamable mode
- ⚠️ Same security considerations as HTTP
- ⚠️ CORS configuration needed for browsers
- 💡 Recommended: Use HTTPS in production

---

## Examples

See the `examples/` directory for complete usage examples:

- `examples/01_basic_scene.py` - Works with all transports
- `examples/02_physics_workflow.py` - HTTP mode for preview integration
- `examples/03_camera_shots.py` - STDIO mode for Claude Desktop
- `examples/04_http_api.py` - Direct HTTP API usage

---

## Future Enhancements

Planned improvements for transport modes:

1. **Configurable ports** via environment variables
2. **WebSocket transport** for bidirectional streaming
3. **Authentication** for HTTP/Streamable modes
4. **Rate limiting** for HTTP endpoints
5. **CORS configuration** for web clients
6. **TLS/SSL support** for secure connections
7. **Health check endpoints** for monitoring
8. **Metrics and observability** (Prometheus, etc.)

---

## Summary

chuk-mcp-stage now supports the same transport flexibility as chuk-mcp-open-meteo and chuk-mcp-celestial:

```bash
# Standard MCP (Claude Desktop, CLI)
uv run chuk-mcp-stage

# HTTP API (Web services, preview server)
uv run chuk-mcp-stage http

# Streaming (Real-time updates)
uv run chuk-mcp-stage streamable
```

This makes chuk-mcp-stage compatible with a wide range of deployment scenarios and client types.
