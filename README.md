# chuk-mcp-stage

> **3D Scene & Camera MCP Server** - The director layer between physics simulation and motion rendering

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-compatible-green.svg)](https://modelcontextprotocol.io)
[![Async](https://img.shields.io/badge/async-native-green.svg)](https://docs.python.org/3/library/asyncio.html)

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
