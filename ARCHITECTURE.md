# chuk-mcp-stage Architecture

## Overview

**chuk-mcp-stage** is the orchestration layer that bridges physics simulation and motion rendering. It's the "director + set designer" that:

1. Defines **what's in the 3D world** (scene graph, objects, materials)
2. Decides **where the camera goes** (shots, paths, cinematography)
3. Bridges **physics → visuals** (body bindings, animation baking)
4. Exports **to rendering targets** (R3F, Remotion, glTF)

---

## Core Components

### 1. Scene Manager (`scene_manager.py`)

**Purpose:** Manages 3D scenes with chuk-artifacts storage backend.

**Key responsibilities:**
- Create/retrieve scenes
- Add/modify objects
- Manage shots and camera paths
- Bind physics bodies to visual objects
- Store baked animations
- Provide VFS access to scene workspaces

**Storage model:**
- Each scene = 1 workspace namespace in chuk-artifacts
- Scene definition → `/scene.json`
- Baked animations → `/animations/*.json`
- Exports → `/export/r3f/`, `/export/remotion/`

**API:**
```python
manager = SceneManager()

# Create scene
scene = await manager.create_scene(scene_id, name, metadata)

# Add content
await manager.add_object(scene_id, scene_object)
await manager.add_shot(scene_id, shot)

# Physics
await manager.bind_physics(scene_id, object_id, physics_body_id)
await manager.add_baked_animation(scene_id, object_id, animation)

# Access
vfs = await manager.get_scene_vfs(scene_id)
```

---

### 2. Models (`models.py`)

**Purpose:** Strongly-typed Pydantic models for all scene data.

**No dictionary goop. No magic strings. Everything is enums and typed.**

**Key models:**

```python
Scene              # Complete scene definition
  ├─ objects: dict[str, SceneObject]
  ├─ shots: dict[str, Shot]
  ├─ environment: Environment
  ├─ lighting: Lighting
  └─ baked_animations: dict[str, BakedAnimation]

SceneObject        # 3D visual object
  ├─ type: ObjectType (enum)
  ├─ transform: Transform
  ├─ material: Material
  ├─ physics_binding: Optional[str]
  └─ trail/label: Optional

Shot               # Camera shot definition
  ├─ camera_path: CameraPath
  ├─ start_time / end_time
  └─ easing: EasingFunction (enum)

CameraPath         # Camera movement
  ├─ mode: CameraPathMode (enum)
  └─ mode-specific parameters
```

**Enums:**
- `ObjectType`: BOX, SPHERE, CYLINDER, PLANE, MESH
- `MaterialPreset`: METAL_DARK, GLASS_BLUE, PLASTIC_WHITE, etc.
- `CameraPathMode`: ORBIT, STATIC, CHASE, DOLLY, FLYTHROUGH
- `LightingPreset`: THREE_POINT, STUDIO, NOON, SUNSET
- `EasingFunction`: LINEAR, EASE_IN_OUT_CUBIC, SPRING
- `ExportFormat`: R3F_COMPONENT, REMOTION_PROJECT, GLTF, JSON

---

### 3. Physics Bridge (`physics_bridge.py`)

**Purpose:** Integrate physics simulations with scene animations.

**Workflow:**

```
1. Physics sim runs (chuk-mcp-physics)
   └─ Produces per-frame body states

2. PhysicsBridge.bake_simulation()
   └─ Samples physics at specified FPS
   └─ Converts to keyframes (time, position, rotation, velocity)

3. Keyframes stored in scene VFS
   └─ /animations/{object_id}.json

4. Scene exports with animation data
   └─ R3F/Remotion can use keyframes for rendering
```

**API:**
```python
async with PhysicsBridge(physics_server_url) as bridge:
    keyframes = await bridge.bake_simulation(
        simulation_id,
        body_ids=["ball", "car"],
        fps=60,
        duration=10.0
    )
    # Returns: dict[body_id, list[keyframe]]
```

**Keyframe format:**
```json
{
  "time": 0.016,
  "position": [0.0, 5.0, 0.0],
  "rotation": [0.0, 0.0, 0.0, 1.0],
  "velocity": [0.0, -9.81, 0.0]
}
```

---

### 4. Exporters (`exporters.py`)

**Purpose:** Convert scenes to rendering-ready formats.

**Export targets:**

#### JSON
Raw scene data as JSON.

#### R3F Component
React Three Fiber `.tsx` files:
- `Scene.tsx` - Main scene component
- `Camera.tsx` - Camera controller (if shots exist)
- `animations.json` - Baked animation data

#### Remotion Project
Full Remotion project structure:
- `Composition.tsx` - Main composition
- `Root.tsx` - Remotion config
- `package.json` - Dependencies

#### glTF
Static 3D scene file (standard format).

**API:**
```python
artifacts = await SceneExporter.export_scene(
    scene,
    format=ExportFormat.R3F_COMPONENT,
    vfs=vfs,
    output_path="/export/r3f"
)
# Returns: {"component": "/export/r3f/Scene.tsx", ...}
```

---

### 5. MCP Server (`server.py`)

**Purpose:** Expose all functionality as MCP tools.

**Tools provided:**

#### Scene Management
- `stage_create_scene` - Create new scene
- `stage_add_object` - Add 3D object
- `stage_set_environment` - Set lighting/background
- `stage_get_scene` - Get complete scene data

#### Camera & Shots
- `stage_add_shot` - Add camera shot
- `stage_get_shot` - Get shot details

#### Physics Integration
- `stage_bind_physics` - Bind object to physics body
- `stage_bake_simulation` - Bake sim to keyframes

#### Export
- `stage_export_scene` - Export to R3F/Remotion/glTF

**All tools are:**
- Async-native
- Pydantic-validated
- Enum-driven (no magic strings)
- Documented with examples

---

## Data Flow

### Two-Phase Model

chuk-mcp-stage operates in **two distinct phases**:

#### Phase 1: Authoring (Declarative)

"What should exist and where should it be?"

- Define scene graph structure
- Place objects with transforms
- Set materials and lighting
- Define camera shots
- Bind object IDs to physics body IDs (metadata only)

**No computation happens yet** - this is pure scene composition.

#### Phase 2: Baking (Computational)

"What motion actually happened?"

- Connect to physics simulation (Rapier/chuk-mcp-physics)
- Sample physics state at target FPS
- Convert physics data → animation keyframes
- Store keyframes in VFS
- Export scene + animations to rendering formats

**Computation happens here** - physics oracle generates the motion data.

---

### Typical Workflow

```
┌──────────────────────────────────────────────────────────────┐
│ AUTHORING PHASE (Declarative)                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 1. Create Scene                                              │
│    stage_create_scene(name="ball-throw")                     │
│    → VFS: Creates /scene.json                                │
│    → Returns: artifact://stage/ball-throw-xyz                │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 2. Define Visual World                                       │
│    stage_add_object(id="ground", type="plane", ...)          │
│    stage_add_object(id="ball", type="sphere", y=2, ...)      │
│    stage_set_environment(lighting="three-point")             │
│    → Scene graph: {objects: {ground, ball}, env: {...}}      │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 3. Add Cinematography                                        │
│    stage_add_shot(mode="chase", target="ball", ...)          │
│    stage_add_shot(mode="static", position=[10,5,10])         │
│    → Scene graph: {shots: {chase-1, static-1}}               │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 4. Create Physics Simulation (chuk-mcp-physics)              │
│    create_simulation(gravity_y=-9.81)                        │
│    add_rigid_body(sim_id, body_id="ball", shape="sphere")    │
│    → Simulation ready, no motion yet                         │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 5. Bind Physics → Visuals (Metadata Only)                    │
│    stage_bind_physics(                                       │
│        object_id="ball",                                     │
│        physics_body_id="rapier://sim-abc/body-ball"          │
│    )                                                         │
│    → Scene graph: ball.physics_binding = "rapier://..."      │
│    → NO MOTION DATA YET - just a pointer                     │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│ BAKING PHASE (Computational)                                 │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 6. Run Physics Simulation (chuk-mcp-physics)                 │
│    step_simulation(sim_id, steps=300)  # 5s @ 60 FPS         │
│    → Physics oracle computes all trajectories                │
│    → Stored in Rapier service memory/state                   │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 7. Bake Animation (PhysicsBridge)                            │
│    stage_bake_simulation(                                    │
│        scene_id="ball-throw-xyz",                            │
│        simulation_id="sim-abc",                              │
│        fps=60,                                               │
│        duration=5.0                                          │
│    )                                                         │
│    → PhysicsBridge connects to Rapier service                │
│    → Samples physics state every 1/60s                       │
│    → Converts to keyframes:                                  │
│        {time: 0.016, pos: [x,y,z], rot: [x,y,z,w], vel: ...} │
│    → VFS: Writes /animations/ball.json                       │
│    → Scene graph: baked_animations["ball"] = metadata        │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 8. Export (SceneExporter)                                    │
│    stage_export_scene(                                       │
│        scene_id="ball-throw-xyz",                            │
│        format="remotion-project",                            │
│        output_path="/export/remotion"                        │
│    )                                                         │
│    → Reads scene.json from VFS                               │
│    → Reads /animations/*.json from VFS                       │
│    → Generates:                                              │
│        /export/remotion/Composition.tsx                      │
│        /export/remotion/Root.tsx                             │
│        /export/remotion/package.json                         │
│    → Returns artifact URIs (NOT file contents!)              │
│        {                                                     │
│          composition: "artifact://.../Composition.tsx",      │
│          root: "artifact://.../Root.tsx",                    │
│          package: "artifact://.../package.json"              │
│        }                                                     │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│ RENDERING PHASE (External - Remotion)                        │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ 9. Render Video (Outside chuk-mcp-stage)                     │
│    # User or automation:                                     │
│    cd artifact://stage/ball-throw-xyz/export/remotion        │
│    npm install                                               │
│    npm run build                                             │
│    → Remotion renders → output.mp4                           │
│                                                               │
└──────────────────────────────────────────────────────────────┘

Key Observations:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Authoring creates STRUCTURE (scene graph, bindings)
2. Physics oracle creates MOTION (trajectories, state)
3. Baking creates KEYFRAMES (sampled, renderable data)
4. Export creates CODE (R3F/Remotion components)
5. Rendering creates MEDIA (MP4, images)

Authoring is declarative. Baking is computational.
```

---

## Storage Architecture

**Backend:** chuk-artifacts (VFS-backed workspaces)

**Scope:** SESSION (default, ephemeral)

**Structure:**
```
grid/
└── default/
    └── sess-{session_id}/
        └── {scene_namespace_id}/
            ├── scene.json          # Scene definition
            ├── animations/         # Baked keyframes
            │   ├── ball.json
            │   └── car.json
            └── export/             # Generated exports
                ├── r3f/
                │   ├── Scene.tsx
                │   └── Camera.tsx
                └── remotion/
                    ├── Composition.tsx
                    ├── Root.tsx
                    └── package.json
```

**Benefits:**
- Automatic isolation (session-scoped)
- VFS operations (ls, cp, find, etc.)
- Checkpoint support
- Provider-agnostic (memory, filesystem, S3)

---

## Camera Path Modes

### ORBIT
Circular orbit around a focus object.

**Parameters:**
- `focus`: Object ID to orbit
- `radius`: Distance from focus
- `elevation`: Angle above horizon (degrees)
- `speed`: Revolutions per second

**Use cases:** Product shots, object inspection

### STATIC
Fixed camera position.

**Parameters:**
- `position`: Camera XYZ
- `look_at`: Point to face

**Use cases:** Observing motion, fixed angles

### CHASE
Follow a moving object.

**Parameters:**
- `focus`: Object to follow
- `offset`: XYZ offset from object
- `damping`: Smoothing factor

**Use cases:** Following cars, balls, characters

### DOLLY
Linear movement from A to B.

**Parameters:**
- `from_position`: Start XYZ
- `to_position`: End XYZ
- `look_at`: Point to face

**Use cases:** Dramatic reveals, pull-backs

### FLYTHROUGH
Follow a spline path through waypoints.

**Parameters:**
- `waypoints`: List of Vector3 positions

**Use cases:** Scene tours, complex moves

---

## Integration Points

### With chuk-mcp-physics

**Physics produces:**
- Simulation state (positions, rotations, velocities)
- Per-timestep body data

**Stage consumes:**
- Body IDs → Object IDs (via bindings)
- Trajectory data → Animation keyframes
- Simulation timing → Shot timing

**Bridge:** `PhysicsBridge.bake_simulation()`

### With chuk-motion / Remotion

**Stage produces:**
- R3F components (JSX/TSX)
- Camera definitions
- Animation keyframes
- Remotion compositions

**Motion/Remotion consumes:**
- TSX files → React components
- Keyframes → `useSpring` / `interpolate`
- Shot timing → Composition duration

**Bridge:** `SceneExporter.export_scene()`

---

## Design Principles

1. **Async-native** - All operations are `async/await`
2. **Pydantic-native** - No dictionaries, all typed models
3. **Enum-driven** - No magic strings, all constants
4. **VFS-backed** - All storage via chuk-artifacts
5. **Provider-agnostic** - Works with any VFS provider
6. **Export-first** - Designed for R3F/Remotion output
7. **Physics-aware** - First-class integration with simulations

---

## Extension Points

### Custom Object Types
Add new primitives in `ObjectType` enum and exporter logic.

### Custom Camera Modes
Add new modes in `CameraPathMode` and camera generation.

### Custom Materials
Add presets in `MaterialPreset` and material definitions.

### Custom Export Formats
Implement new exporters in `SceneExporter`.

### Custom Storage Providers
Use any chuk-artifacts VFS provider (S3, filesystem, etc.).

---

## Performance Considerations

- **In-memory cache** - Scenes cached in SceneManager
- **Lazy loading** - Scenes loaded on-demand from VFS
- **Batch operations** - VFS supports batch read/write
- **Streaming exports** - Large exports streamed to VFS
- **Async I/O** - All storage operations are async

---

## Security

- **Session isolation** - Scenes scoped to session by default
- **VFS sandboxing** - All file access via VFS layer
- **Input validation** - All inputs Pydantic-validated
- **No code execution** - Exports are data, not code

---

## Future Enhancements

- **Real-time preview** - WebSocket updates for live editing
- **Animation interpolation** - Bezier curves, custom easing
- **Particle systems** - Trails, effects, explosions
- **Post-processing** - Bloom, DOF, motion blur settings
- **Audio sync** - Timeline with audio tracks
- **Collaborative editing** - Multi-user scene editing
- **Template library** - Pre-built scene templates
- **Asset management** - Import/manage 3D models, textures

---

This architecture enables the core value prop:

> **Physics → Stage → Motion → Video**
>
> From simulation to rendered media, all programmatically.
