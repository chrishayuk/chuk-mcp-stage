# chuk-mcp-stage

> **3D Scene & Camera MCP Server** - The director layer between physics simulation and motion rendering

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![Async](https://img.shields.io/badge/async-native-green.svg)](https://docs.python.org/3/library/asyncio.html)

**🌐 Quick Install:** `uvx stage.chukai.io/mcp`

**chuk-mcp-stage** is the orchestration layer that bridges:
- **chuk-mcp-physics** (Rapier simulations) → Scene animations
- **chuk-motion / Remotion** (video rendering) → Export targets

It's the **"director + set designer"** that defines what's in the 3D world, where the camera goes, and how physics drives motion.

---

## 🎯 What This Does

**Core capabilities:**

1. **Scene Graph** - Define 3D worlds (objects, materials, lighting)
2. **Camera Paths** - Cinematography (orbit, chase, dolly, static shots)
3. **Physics Bridge** - Bind scene objects to physics bodies (uses public Rapier service by default)
4. **Animation Baking** - Convert physics simulations → keyframes
5. **Export** - Generate R3F components, Remotion projects, glTF

**The full pipeline:**

```
Physics Simulation → Stage → Motion/Video
(chuk-mcp-physics) → (chuk-mcp-stage) → (chuk-motion/Remotion)
```

---

## 🚀 Quick Start

### Installation

**Option 1: Install from public URL (Recommended)**

```bash
# Install directly from public URL with uvx
uvx stage.chukai.io/mcp
```

**Option 2: Install from PyPI**

```bash
pip install chuk-mcp-stage
```

**Option 3: Install from source**

```bash
cd chuk-mcp-stage
pip install -e .
```

**Physics ready out-of-the-box!** Uses the public Rapier service at `https://rapier.chukai.io` by default. No additional setup required for physics simulations.

### Run the Server

```bash
# STDIO mode (default - for MCP clients like Claude Desktop)
uv run chuk-mcp-stage

# HTTP mode (REST API on port 8000)
uv run chuk-mcp-stage http

# Streamable mode (Server-Sent Events for streaming responses)
uv run chuk-mcp-stage streamable
```

**Transport modes:**
- **stdio**: Standard MCP protocol via stdin/stdout (default for Claude Desktop)
- **http**: HTTP REST API server on port 8000 (used by chuk-mcp-r3f-preview)
- **streamable**: SSE (Server-Sent Events) transport for streaming responses

📖 **[Complete Transport Modes Guide](docs/TRANSPORT_MODES.md)** - Detailed documentation, examples, and troubleshooting

### Configure in Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

**Option 1: Using public URL (Recommended)**

```json
{
  "mcpServers": {
    "stage": {
      "command": "uvx",
      "args": ["stage.chukai.io/mcp"],
      "env": {
        "RAPIER_SERVICE_URL": "https://rapier.chukai.io"
      }
    }
  }
}
```

**Option 2: Using local installation**

```json
{
  "mcpServers": {
    "stage": {
      "command": "chuk-mcp-stage",
      "env": {
        "RAPIER_SERVICE_URL": "https://rapier.chukai.io"
      }
    }
  }
}
```

### Physics Integration Configuration

chuk-mcp-stage integrates with physics simulations via **[chuk-mcp-physics](https://github.com/chrishayuk/chuk-mcp-physics)** and the Rapier physics engine.

**Three Integration Methods:**

1. **Direct Rapier HTTP** (Default) - Fastest for simulations
   - Directly calls Rapier service HTTP API
   - Used by `stage_bake_simulation` tool
   - Defaults to public service: `https://rapier.chukai.io`

2. **Via MCP Tools** - Most flexible
   - Use chuk-mcp-physics MCP server tools
   - Supports both analytic calculations and Rapier simulations
   - Requires chuk-mcp-physics server running

3. **Hybrid** - Best of both worlds
   - Use MCP tools for simulation creation/setup
   - Use direct HTTP for baking trajectories

**Environment Variables:**

```bash
# Rapier service URL (default: https://rapier.chukai.io)
RAPIER_SERVICE_URL=https://rapier.chukai.io  # Public service
# RAPIER_SERVICE_URL=http://localhost:9000   # Local development

# Rapier timeout in seconds (default: 30.0)
RAPIER_TIMEOUT=30.0

# Physics provider type (default: auto)
PHYSICS_PROVIDER=auto  # or 'rapier', 'mcp'
```

**Claude Desktop with Custom Rapier Service:**

```json
{
  "mcpServers": {
    "stage": {
      "command": "chuk-mcp-stage",
      "env": {
        "RAPIER_SERVICE_URL": "http://localhost:9000",
        "RAPIER_TIMEOUT": "60.0"
      }
    },
    "physics": {
      "command": "uvx",
      "args": ["chuk-mcp-physics"],
      "env": {
        "RAPIER_SERVICE_URL": "http://localhost:9000"
      }
    }
  }
}
```

**Public Rapier Service:**
- URL: `https://rapier.chukai.io`
- No authentication required
- Rate limits may apply
- Perfect for prototyping and demos

**Local Rapier Service:**
```bash
# Run locally with Docker
docker run -p 9000:9000 chuk-rapier-service

# Or from source
cd rapier-service && cargo run --release
```

See **[chuk-mcp-physics README](https://github.com/chrishayuk/chuk-mcp-physics)** for complete physics integration guide.

---

### Google Drive OAuth Storage (HTTP Mode)

**Store your scenes in Google Drive** with OAuth 2.1 authentication for secure, persistent, user-owned storage!

When running in **HTTP mode**, chuk-mcp-stage supports Google Drive OAuth integration. Users authenticate via their browser, and scenes are stored in their own Google Drive under `/CHUK/stage/`.

**Benefits:**
- ✅ **Secure OAuth 2.1** - Industry-standard authentication with PKCE
- ✅ **User Owns Data** - Scenes stored in user's Google Drive, not your infrastructure
- ✅ **Auto Token Refresh** - Seamless authentication with automatic refresh
- ✅ **Cross-Device Access** - Access scenes from any device with Drive
- ✅ **Built-in Sharing** - Share scenes using Google Drive's native sharing
- ✅ **Natural Discoverability** - View/edit scene files directly in Drive UI
- ✅ **No Infrastructure Cost** - Zero storage costs for the provider

#### Setup Steps

**1. Create Google Cloud Project:**

- Go to https://console.cloud.google.com/
- Create new project (or select existing)
- Enable **Google Drive API**
- Go to **OAuth consent screen**:
  - User Type: External
  - Add your email as test user
- Go to **Credentials** → Create **OAuth 2.0 Client ID**:
  - Application type: Web application
  - Authorized redirect URIs: `http://localhost:8000/oauth/callback`
- Copy Client ID and Client Secret

**2. Install with Google Drive Support:**

```bash
pip install "chuk-mcp-stage[google_drive]"
```

**3. Configure Environment:**

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Google credentials:
# GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
# GOOGLE_CLIENT_SECRET=your-client-secret
```

**4. Verify OAuth Integration (Optional but Recommended):**

```bash
# Verify that OAuth setup works
python examples/verify_google_drive_oauth.py
```

This will verify:
- OAuth provider initializes correctly
- Credentials are valid
- OAuth endpoints can be registered
- Ready for Google Drive integration

**5. Run Server in HTTP Mode:**

```bash
# Load from .env file
uv run chuk-mcp-stage http

# Or set environment variables directly
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
uv run chuk-mcp-stage http
```

**6. Authorize Access:**

When Claude Desktop (or any MCP client) connects:
1. OAuth flow automatically initiates
2. Browser opens for Google authorization
3. User grants access to Google Drive
4. Tokens securely stored and auto-refreshed

**OAuth Endpoints** (automatically registered):
- Authorization: `http://localhost:8000/oauth/authorize`
- Token: `http://localhost:8000/oauth/token`
- Discovery: `http://localhost:8000/.well-known/oauth-authorization-server`
- Callback: `http://localhost:8000/oauth/callback`

#### Deployment to Fly.io

For production deployments, set secrets instead of using `.env`:

```bash
# Set Google OAuth credentials as Fly secrets
fly secrets set GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
fly secrets set GOOGLE_CLIENT_SECRET="your-client-secret"

# Set OAuth server URL (use your Fly.io app URL)
fly secrets set OAUTH_SERVER_URL="https://your-app.fly.dev"
fly secrets set GOOGLE_REDIRECT_URI="https://your-app.fly.dev/oauth/callback"

# Optional: Configure session backend for production
fly secrets set SESSION_PROVIDER="redis"
fly secrets set SESSION_REDIS_URL="redis://your-redis-url:6379/0"

# Deploy
fly deploy
```

**Important**: Update Google Cloud Console with production redirect URI:
- Add `https://your-app.fly.dev/oauth/callback` to authorized redirect URIs

#### Storage Providers Comparison

| Provider | Persistence | User Owns Data | Setup Complexity | Cost |
|----------|-------------|----------------|------------------|------|
| **Memory** (default) | ❌ Session only | N/A | ✅ Zero | Free |
| **Google Drive** | ✅ Permanent | ✅ Yes | ⚠️ OAuth setup | Free (user's Drive) |
| **S3** | ✅ Permanent | ❌ Provider-owned | ⚠️ AWS credentials | $$ (your infrastructure) |

#### Where Your Scenes Live

**With Memory (default)**:
- Scenes exist only during the session
- Lost when server restarts

**With Google Drive**:
```
Google Drive
└── CHUK/
    └── stage/
        ├── scene-abc123/
        │   ├── scene.json
        │   ├── baked_animations.json
        │   └── exports/
        └── scene-def456/
            └── scene.json
```

Users can:
- View scenes in Google Drive web UI
- Share scene folders with collaborators
- Download/backup scenes locally
- Access from any device

**Environment Variables**:

```bash
# Use Google Drive provider
VFS_PROVIDER=google_drive

# Path to credentials JSON (defaults to ~/.chuk/google_drive_credentials.json)
GOOGLE_DRIVE_CREDENTIALS_FILE=~/.chuk/google_drive_credentials.json

# Or provide credentials directly as JSON string
GOOGLE_DRIVE_CREDENTIALS='{"token": "...", "refresh_token": "...", ...}'

# Root folder in Drive (default: CHUK)
GOOGLE_DRIVE_ROOT_FOLDER=CHUK

# Cache TTL in seconds (default: 60)
GOOGLE_DRIVE_CACHE_TTL=60
```

---

## 📦 Tool Surface

### Scene Management

```python
# Create a new scene
stage_create_scene(name, author, description)

# Add 3D objects
stage_add_object(
    scene_id,
    object_id,
    object_type,  # "box", "sphere", "cylinder", "plane"
    position_x, position_y, position_z,
    radius, size_x, size_y, size_z,
    material_preset,  # "metal-dark", "glass-blue", "plastic-white"
    color_r, color_g, color_b
)

# Set environment & lighting
stage_set_environment(
    scene_id,
    environment_type,  # "gradient", "solid", "hdri"
    lighting_preset    # "three-point", "studio", "noon"
)
```

### Camera & Shots

```python
# Add camera shot
stage_add_shot(
    scene_id,
    shot_id,
    camera_mode,  # "orbit", "static", "chase", "dolly"
    start_time,
    end_time,
    focus_object,      # Object to orbit/chase
    orbit_radius,
    orbit_elevation,
    orbit_speed,
    easing  # "ease-in-out-cubic", "spring", "linear"
)

# Get shot details
stage_get_shot(scene_id, shot_id)
```

### Physics Integration

```python
# Bind object to physics body
stage_bind_physics(
    scene_id,
    object_id,
    physics_body_id  # "rapier://sim-abc/body-ball"
)

# Bake simulation to keyframes
stage_bake_simulation(
    scene_id,
    simulation_id,
    fps=60,
    duration=10.0,
    physics_server_url=None  # Optional: defaults to https://rapier.chukai.io
)
```

### Export

```python
# Export to R3F/Remotion/glTF
stage_export_scene(
    scene_id,
    format,  # "r3f-component", "remotion-project", "gltf", "json"
    output_path
)

# Get complete scene data
stage_get_scene(scene_id)
```

---

## 🧩 Core Concepts

### Stage Objects

A **Stage Object** is an entry in the scene graph that represents a 3D visual element. Every object has:

| Property | Description | Example |
|----------|-------------|---------|
| **id** | Unique identifier | `"ball"`, `"ground"`, `"car-chassis"` |
| **type** | Primitive shape | `"sphere"`, `"box"`, `"cylinder"`, `"plane"` |
| **transform** | Position, rotation, scale | `{position: [0, 5, 0], rotation: [0, 0, 0], scale: [1, 1, 1]}` |
| **material** | Visual appearance | `"glass-blue"`, `"metal-dark"`, custom PBR |
| **physics_binding** | Optional physics link | `"rapier://sim-abc/body-ball"` |

**Example scene JSON:**

```json
{
  "id": "demo-scene",
  "name": "Falling Ball Demo",
  "objects": {
    "ground": {
      "id": "ground",
      "type": "plane",
      "transform": {
        "position": {"x": 0, "y": 0, "z": 0},
        "rotation": {"x": 0, "y": 0, "z": 0},
        "scale": {"x": 1, "y": 1, "z": 1}
      },
      "size": {"x": 20, "y": 20, "z": 1},
      "material": {
        "preset": "metal-dark"
      },
      "physics_binding": null
    },
    "ball": {
      "id": "ball",
      "type": "sphere",
      "transform": {
        "position": {"x": 0, "y": 5, "z": 0},
        "rotation": {"x": 0, "y": 0, "z": 0},
        "scale": {"x": 1, "y": 1, "z": 1}
      },
      "radius": 1.0,
      "material": {
        "preset": "glass-blue",
        "color": {"r": 0.3, "g": 0.6, "b": 1.0}
      },
      "physics_binding": "rapier://sim-falling/body-ball"
    }
  },
  "shots": {
    "main": {
      "id": "main",
      "camera_path": {
        "mode": "orbit",
        "focus": "ball",
        "radius": 8.0,
        "elevation": 30.0
      },
      "start_time": 0.0,
      "end_time": 10.0
    }
  }
}
```

**Why this matters for LLMs:**

When you create an object with `stage_add_object`, you're modifying this scene graph. Later operations like `stage_bind_physics` or `stage_add_shot` reference the **same object ID** you created. This makes it easy to reason about: "I want to modify the ball I just created" → just use `object_id="ball"`.

### Authoring vs Baking

chuk-mcp-stage has **two distinct phases**:

#### 1️⃣ Authoring Phase (Define the World)

**What you're doing:** Planning and composing the scene

**Operations:**
- Create scene structure
- Place objects (primitives, positions, materials)
- Define camera shots and movements
- Bind object IDs to physics body IDs
- Set environment and lighting

**Output:** Scene definition (metadata only, no animation yet)

**Tools used:**
- `stage_create_scene`
- `stage_add_object`
- `stage_add_shot`
- `stage_bind_physics`
- `stage_set_environment`

#### 2️⃣ Baking Phase (Generate Animation Data)

**What you're doing:** Converting physics simulation to renderable keyframes

**Operations:**
- Connect to physics simulation (Rapier)
- Sample physics state at desired FPS
- Convert body positions/rotations → keyframes
- Store animation data in scene VFS

**Output:** Timestamped keyframe arrays (position, rotation, velocity per frame)

**Tools used:**
- `stage_bake_simulation` (connects to physics, generates keyframes)
- `stage_export_scene` (exports scene + baked animations)

#### Typical Flow

```
┌──────────────────────────────────────────────────────────────┐
│ AUTHORING PHASE                                              │
├──────────────────────────────────────────────────────────────┤
│ 1. stage_create_scene(name="demo")                           │
│    → Creates empty scene graph                               │
│                                                               │
│ 2. stage_add_object(id="ground", type="plane", ...)          │
│    stage_add_object(id="ball", type="sphere", y=10, ...)     │
│    → Defines visual objects (no motion yet)                  │
│                                                               │
│ 3. stage_set_environment(lighting="three-point")             │
│    → Sets lights, background                                 │
│                                                               │
│ 4. Use physics MCP to create simulation                      │
│    create_simulation(gravity_y=-9.81)                        │
│    add_rigid_body(sim_id, body_id="ball", ...)               │
│    → Physics oracle creates simulation                       │
│                                                               │
│ 5. stage_bind_physics(object_id="ball",                      │
│                       body_id="rapier://sim-id/body-ball")   │
│    → Links visual object to physics body                     │
│                                                               │
│ 6. step_simulation(sim_id, steps=600)  # 10s @ 60 FPS        │
│    → Physics oracle runs simulation                          │
│                                                               │
│ 7. stage_add_shot(mode="orbit", focus="ball", ...)           │
│    → Defines camera cinematography                           │
├──────────────────────────────────────────────────────────────┤
│ BAKING PHASE                                                 │
├──────────────────────────────────────────────────────────────┤
│ 8. stage_bake_simulation(scene_id, sim_id, fps=60, dur=10)  │
│    → Fetches physics data from Rapier                        │
│    → Converts to keyframes                                   │
│    → Stores in /animations/ball.json                         │
│                                                               │
│ 9. stage_export_scene(format="remotion-project")            │
│    → Generates R3F/Remotion code                             │
│    → Includes baked animation data                           │
│    → Returns artifact URIs                                   │
└──────────────────────────────────────────────────────────────┘

   Authoring = "What should exist and where?"
   Baking    = "What motion actually happened?"
```

**Key Insight:** Authoring is **declarative** (you define intent), baking is **computational** (physics oracle generates the motion).

---

## 🎬 Example Workflow

### 1. Simple Falling Ball Demo

```python
# 1. Create scene
scene = await stage_create_scene(
    name="falling-ball-demo",
    description="Ball falling under gravity"
)

# 2. Add ground plane
await stage_add_object(
    scene_id=scene.scene_id,
    object_id="ground",
    object_type="plane",
    size_x=20.0,
    size_y=20.0,
    material_preset="metal-dark"
)

# 3. Add falling ball
await stage_add_object(
    scene_id=scene.scene_id,
    object_id="ball",
    object_type="sphere",
    radius=1.0,
    position_y=5.0,
    material_preset="glass-blue",
    color_r=0.3,
    color_g=0.5,
    color_b=1.0
)

# 4. Add orbiting camera shot
await stage_add_shot(
    scene_id=scene.scene_id,
    shot_id="orbit-shot",
    camera_mode="orbit",
    focus_object="ball",
    orbit_radius=8.0,
    orbit_elevation=30.0,
    orbit_speed=0.1,
    start_time=0.0,
    end_time=10.0
)

# 5. Export to Remotion
result = await stage_export_scene(
    scene_id=scene.scene_id,
    format="remotion-project"
)
```

### 2. Physics-Driven Animation

**Note:** This example uses the **public Rapier service** (`https://rapier.chukai.io`) by default. No configuration needed!

```python
# 1. Create physics simulation (chuk-mcp-physics)
sim = await create_simulation(gravity_y=-9.81)

await add_rigid_body(
    sim_id=sim.sim_id,
    body_id="ball",
    body_type="dynamic",
    shape="sphere",
    radius=1.0,
    position=[0, 5, 0]
)

# 2. Create scene
scene = await stage_create_scene(name="physics-demo")

await stage_add_object(
    scene_id=scene.scene_id,
    object_id="ball",
    object_type="sphere",
    radius=1.0,
    position_y=5.0
)

# 3. Bind physics to visual
await stage_bind_physics(
    scene_id=scene.scene_id,
    object_id="ball",
    physics_body_id=f"rapier://{sim.sim_id}/body-ball"
)

# 4. Run simulation (chuk-mcp-physics)
await step_simulation(sim_id=sim.sim_id, steps=600)

# 5. Bake physics → keyframes
await stage_bake_simulation(
    scene_id=scene.scene_id,
    simulation_id=sim.sim_id,
    fps=60,
    duration=10.0
)

# 6. Export with animation data
await stage_export_scene(
    scene_id=scene.scene_id,
    format="r3f-component"
)
```

---

## 📚 Examples

The `examples/` directory contains ready-to-run demonstrations of all features.

### 🌟 Start Here: Golden Path

**The canonical example showing the complete pipeline:**

```bash
uv run examples/00_golden_path_ball_throw.py
```

This example demonstrates:
- ✅ **Authoring phase** - Scene creation, object placement, camera shots
- ✅ **Baking phase** - Physics simulation → keyframes (conceptual)
- ✅ **Export phase** - Generate R3F/Remotion code
- ✅ **Artifact URIs** - How chuk-mcp-stage integrates with chuk-artifacts
- ✅ **Two-phase model** - Declarative → Computational
- ✅ **Complete pipeline** - Physics → Stage → Motion → Video

**This is the best example to understand the CHUK stack cohesion.**

### Getting Started

```bash
# Run any example
uv run examples/00_golden_path_ball_throw.py  # ⭐ Start here!
uv run examples/01_simple_scene.py
uv run examples/02_physics_integration_demo.py
uv run examples/03_camera_shots_demo.py
uv run examples/04_export_formats.py
uv run examples/05_full_physics_workflow.py
```

### Example Guide

| Example | Purpose | What You'll Learn |
|---------|---------|-------------------|
| **00_golden_path_ball_throw.py** ⭐ | **Complete pipeline** | **Full workflow, artifact URIs, two-phase model** |
| **01_simple_scene.py** | Basic scene creation | Objects, transforms, materials, simple camera |
| **02_physics_integration_demo.py** | Physics binding concepts | Binding objects to physics bodies, metadata |
| **03_camera_shots_demo.py** | Camera cinematography | ORBIT, STATIC, DOLLY, CHASE modes, easing functions |
| **04_export_formats.py** | Export capabilities | JSON, R3F, Remotion, glTF formats and use cases |
| **05_full_physics_workflow.py** | Complete pipeline | Full physics-to-video workflow with public Rapier |

### Example Outputs

**00_golden_path_ball_throw.py** ⭐ - Complete pipeline demonstration
```
📂 Artifact URIs (Not file contents!):
   Scene data:  artifact://stage/golden-path-ball-throw/exports/scene.json
   R3F:         artifact://stage/golden-path-ball-throw/exports/r3f/Scene.tsx
   Remotion:    artifact://stage/golden-path-ball-throw/exports/remotion/

🎬 Complete Pipeline:
   1. Authoring   - Define scene structure   ✓
   2. Physics     - Create simulation         (conceptual)
   3. Binding     - Link objects → bodies     ✓
   4. Baking      - Physics → keyframes       (conceptual)
   5. Export      - Scene → R3F/Remotion      ✓
   6. Render      - Remotion → MP4            (external)
```

**01_simple_scene.py** - Creates falling ball scene
```
✓ Created scene: falling-ball
✓ Added ground plane
✓ Added ball at (0, 5, 0)
✓ Added orbit camera shot (10s)
```

**03_camera_shots_demo.py** - 38-second multi-shot sequence
```
📹 Shot Sequence:
   •   0.0s -  10.0s  ORBIT   - Smooth orbit around center
   •  10.0s -  15.0s  STATIC  - Static wide angle
   •  15.0s -  22.0s  DOLLY   - Dolly tracking shot
   •  22.0s -  28.0s  CHASE   - Chase with spring easing
   •  28.0s -  33.0s  ORBIT   - Fast linear orbit
   •  33.0s -  38.0s  STATIC  - Low angle hero shot
```

**04_export_formats.py** - Exports to all formats
```
✓ JSON:     /exports/scene.json
✓ R3F:      /exports/r3f/Scene.tsx
✓ Remotion: /exports/remotion/Root.tsx
✓ glTF:     /exports/scene.gltf

Note: In production, these would be artifact URIs like:
  artifact://stage/{scene_id}/exports/scene.json
```

**05_full_physics_workflow.py** - Shows complete pipeline
```
🎬 Complete Pipeline:
   1. Physics Simulation (chuk-mcp-physics)
   2. Scene Composition (chuk-mcp-stage) ✓
   3. Bind Physics ✓
   4. Bake Simulation (Rapier service)
   5. Export (R3F/Remotion) ✓
   6. Render Video (Remotion)
```

### Learning Path

**Recommended order:**
1. **Start with `00_golden_path_ball_throw.py`** ⭐ - See the complete pipeline first
2. Understand basics with `01_simple_scene.py`
3. Explore camera control with `03_camera_shots_demo.py`
4. Learn export options with `04_export_formats.py`
5. See physics concepts with `02_physics_integration_demo.py`
6. Complete workflow with `05_full_physics_workflow.py`

**Why start with golden path?** It shows you the **destination** (full pipeline) before diving into individual pieces. You'll understand how all the tools work together in the CHUK stack.

---

## 🏗️ Architecture

### Scene Storage

- **Backend**: chuk-artifacts (VFS-backed workspaces)
- **Format**: JSON scene definitions with nested objects
- **Scope**: SESSION (ephemeral), USER (persistent), SANDBOX (shared)

Each scene is a workspace containing:
```
/scene.json          # Scene definition
/animations/         # Baked keyframe data
  ball.json
  car.json
/export/             # Generated R3F/Remotion code
  r3f/
  remotion/
```

### Camera Path Modes

| Mode | Use Case | Parameters |
|------|----------|------------|
| `orbit` | Product shots, inspection | radius, elevation, speed, focus |
| `static` | Fixed observation | position, look_at |
| `chase` | Follow moving objects | target, offset, damping |
| `dolly` | Linear reveals | from_position, to_position, look_at |
| `flythrough` | Scene tours | waypoints[] |
| `crane` | Cinematic sweeps | pivot, arc, height_range |

### Material Presets

- `metal-dark`, `metal-light`
- `glass-clear`, `glass-blue`, `glass-green`
- `plastic-red`, `plastic-blue`, `plastic-white`
- `rubber-black`
- `wood-oak`

### Export Formats

- **R3F Component** - React Three Fiber `.tsx` files
- **Remotion Project** - Full project with `package.json`
- **glTF** - Static 3D scene file
- **JSON** - Raw scene data

### VFS & Artifacts Integration

**chuk-mcp-stage** is tightly integrated with **[chuk-artifacts](https://github.com/chrishayuk/chuk-artifacts)** and **[chuk-virtual-fs](https://github.com/chrishayuk/chuk-virtual-fs)** for storage and asset management.

#### Why This Matters

Unlike typical MCP servers that return large JSON blobs inline, chuk-mcp-stage returns **artifact URIs**:

```python
# ❌ Traditional approach (bloated)
{
  "scene_data": "...<10MB of JSON>...",
  "r3f_component": "...<5000 lines of TSX>...",
  "animations": "...<50MB of keyframes>..."
}

# ✅ CHUK approach (cohesive)
{
  "scene": "artifact://stage/demo-scene/scene.json",
  "component": "artifact://stage/demo-scene/export/r3f/Scene.tsx",
  "animations": "artifact://stage/demo-scene/animations/ball.json"
}
```

**Benefits:**

1. **No inline bloat** - Tools return URIs, not massive data
2. **Persistent storage** - Scenes survive across sessions (if using USER scope)
3. **VFS operations** - Use `vfs_ls`, `vfs_find`, `vfs_cp` to manage scene files
4. **Cross-tool sharing** - Other MCP servers can access same artifacts
5. **Checkpoint support** - Version control for scene iterations

#### Storage Model

Each scene = **one workspace** in chuk-artifacts:

```
artifact://stage/{scene_id}/
├── scene.json              # Scene definition
├── animations/             # Baked physics keyframes
│   ├── ball.json          # Per-object animation data
│   ├── car.json
│   └── character.json
└── export/                 # Generated code
    ├── r3f/               # React Three Fiber
    │   ├── Scene.tsx
    │   ├── Camera.tsx
    │   └── animations.json
    ├── remotion/          # Remotion project
    │   ├── Composition.tsx
    │   ├── Root.tsx
    │   └── package.json
    └── gltf/              # 3D model exports
        └── scene.gltf
```

#### Example: Working with Artifacts

```python
# 1. Create scene (returns artifact URI)
result = await stage_create_scene(name="demo")
# → {"scene_id": "demo-xyz", "workspace": "artifact://stage/demo-xyz"}

# 2. Add objects and bake simulation
# ... (authoring phase)

# 3. Export to Remotion (returns artifact URIs)
export_result = await stage_export_scene(
    scene_id="demo-xyz",
    format="remotion-project",
    output_path="/export/remotion"
)
# → {
#     "composition": "artifact://stage/demo-xyz/export/remotion/Composition.tsx",
#     "root": "artifact://stage/demo-xyz/export/remotion/Root.tsx",
#     "package": "artifact://stage/demo-xyz/export/remotion/package.json"
# }

# 4. Use VFS tools to explore (via chuk-virtual-fs MCP)
await vfs_ls("artifact://stage/demo-xyz/export/remotion")
# → ["Composition.tsx", "Root.tsx", "package.json"]

await vfs_read("artifact://stage/demo-xyz/export/remotion/package.json")
# → Returns package.json contents

# 5. Copy to another location
await vfs_cp(
    "artifact://stage/demo-xyz/export/remotion",
    "artifact://projects/my-video"
)
```

#### Integration with Other CHUK Tools

**chuk-mcp-r3f-preview** can directly preview scenes:

```python
# Stage creates scene
scene_uri = "artifact://stage/demo-xyz/export/r3f/Scene.tsx"

# R3F preview server loads it
await r3f_preview_scene(scene_uri)
# → Opens interactive 3D preview in browser
```

**chuk-motion** can render baked animations:

```python
# Stage bakes physics
animation_uri = "artifact://stage/demo-xyz/animations/ball.json"

# Motion applies spring physics to keyframes
await motion_apply_spring(animation_uri, stiffness=100)
```

This is where the **CHUK stack cohesion** shines: Every tool speaks the same artifact URI language.

---

## 🔗 Integration with CHUK Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     chuk-mcp-stage                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Scene Graph  │  │   Camera     │  │  Physics Bridge  │  │
│  │              │  │   Paths      │  │                  │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼─────────────────┼───────────────────┼────────────┘
          │                 │                   │
          ▼                 ▼                   ▼
┌─────────────────┐  ┌─────────────┐  ┌─────────────────────┐
│ chuk-artifacts  │  │ chuk-motion │  │  chuk-mcp-physics   │
│                 │  │             │  │      (Rapier)       │
│ • scene.json    │  │ • easing    │  │                     │
│ • assets/       │  │ • springs   │  │ • rigid bodies      │
│ • animations/   │  │ • keyframes │  │ • constraints       │
└─────────────────┘  └──────┬──────┘  │ • sim state         │
                            │         └─────────────────────┘
                            ▼
                   ┌─────────────────┐
                   │ Remotion        │
                   │                 │
                   │ • R3F render    │
                   │ • video export  │
                   │ • MP4 output    │
                   └─────────────────┘
```

---

## 🎯 Use Cases

### Immediate Wins

1. **Physics Explainer Videos** - Auto-generate educational content
2. **Simulation-as-a-Service** - LLMs can request visualizations
3. **Procedural B-Roll** - Synthetic motion graphics

### Vertical Plays

4. **Motorsport Visualization** - Racing lines, braking zones, overtakes
5. **3D Data Storytelling** - Animated datasets with cinematography
6. **Science Journalism** - Render model predictions visually

### Weird & Powerful

7. **Explainable AI Animations** - Show what models are thinking
8. **Virtual Physics Lab** - Programmable experiments
9. **Agent Cinematography** - AI chooses camera paths

---

## 📐 Data Models

All models are **Pydantic-native** with **no dictionary goop**:

```python
from chuk_mcp_stage.models import (
    Scene,              # Complete scene definition
    SceneObject,        # 3D object (mesh, material, transform)
    Shot,               # Camera path + time range
    CameraPath,         # Camera movement definition
    Material,           # PBR material properties
    Environment,        # Lighting & background
    BakedAnimation,     # Physics → keyframes
)
```

**Enums everywhere:**
```python
ObjectType.SPHERE
MaterialPreset.GLASS_BLUE
CameraPathMode.ORBIT
LightingPreset.THREE_POINT
ExportFormat.R3F_COMPONENT
```

---

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=chuk_mcp_stage
```

---

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format
black src/ tests/

# Lint
ruff check src/

# Type check
mypy src/
```

---

## 📄 License

MIT License - see LICENSE for details

---

## 🌟 Why This Matters

Most people can:
✅ Run simulations
✅ Generate charts
✅ Animate text

Almost nobody can:
> **Simulate → Direct → Render → Explain → Export**

**chuk-mcp-stage gives you that pipeline.**

You're not rendering things anymore.
You're **producing explainable simulations as media**.

---

**Built with ❤️ for the CHUK AI stack**
