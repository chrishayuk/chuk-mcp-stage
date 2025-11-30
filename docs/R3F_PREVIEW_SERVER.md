# R3F Preview Server Design

## Overview

The R3F Preview Server provides real-time visual preview of 3D scenes being composed via `chuk-mcp-stage`. It enables interactive iteration on scene composition, camera paths, lighting, and physics visualization before final export.

## Architecture

```
┌─────────────────────────┐
│   chuk-mcp-stage        │
│   (Scene Composition)   │
└───────────┬─────────────┘
            │
            │ VFS Scene Data
            ▼
┌─────────────────────────┐
│  chuk-mcp-r3f-preview       │
│  (MCP Server)           │
├─────────────────────────┤
│  Tools:                 │
│  - start_preview        │
│  - stop_preview         │
│  - reload_scene         │
│  - get_preview_url      │
└───────────┬─────────────┘
            │
            │ Spawn & Manage
            ▼
┌─────────────────────────┐
│  Vite Dev Server        │
│  (React + R3F)          │
├─────────────────────────┤
│  - Hot reload           │
│  - Scene loader         │
│  - Camera controls      │
│  - Timeline scrubber    │
└─────────────────────────┘
```

## Core Features

### 1. Scene Loading & Hot Reload

**Scene Loader Component**
- Watches VFS for scene.json changes
- Dynamically constructs R3F scene graph from JSON
- Supports all ObjectTypes (box, sphere, cylinder, plane, mesh)
- Applies materials, transforms, and physics bindings

**Hot Reload**
- File watcher on VFS scene workspace
- WebSocket push notifications to browser
- Automatic scene re-render on changes

### 2. Interactive Camera Control

**Camera Modes**
- **Orbit**: Mouse drag to rotate around focus point
- **Fly**: WASD + mouse look for free navigation
- **Shot Preview**: Playback camera paths defined in scene.shots
- **Split View**: Side-by-side comparison of multiple shots

**Timeline Scrubber**
- Timeline UI showing all defined shots
- Scrub through time to preview camera animations
- Play/pause/step controls
- Current time indicator

### 3. Physics Visualization

**Trajectory Trails**
- Render baked animation paths as curves
- Color-coded by object
- Opacity fades with time
- Toggle visibility per object

**Playback Controls**
- Play physics animation from baked keyframes
- Speed control (0.1x - 2x)
- Loop mode
- Frame-by-frame stepping

### 4. Lighting & Environment Preview

**Real-time Adjustments**
- Environment HDRI rotation
- Light intensity sliders
- Ambient occlusion toggle
- Shadow quality settings

**Preset Comparison**
- Quick switch between lighting presets
- A/B comparison view

## MCP Server API

### Tools

#### `preview_start`

Start a preview server for a scene.

```python
await preview_start(
    scene_id: str,
    port: int = 3000,
    auto_reload: bool = True
) -> PreviewStartResponse
```

**Response:**
```python
{
    "preview_url": "http://localhost:3000",
    "scene_id": "scene-abc123",
    "status": "running"
}
```

#### `preview_stop`

Stop a running preview server.

```python
await preview_stop(
    scene_id: str
) -> PreviewStopResponse
```

#### `preview_reload`

Force reload of scene in preview (if auto_reload is off).

```python
await preview_reload(
    scene_id: str
) -> PreviewReloadResponse
```

#### `preview_status`

Get status of all running previews.

```python
await preview_status() -> PreviewStatusResponse
```

**Response:**
```python
{
    "previews": [
        {
            "scene_id": "scene-abc123",
            "url": "http://localhost:3000",
            "uptime_seconds": 145,
            "last_reload": "2025-11-30T12:34:56Z"
        }
    ]
}
```

## Tech Stack

### Backend (MCP Server)

- **Python 3.11+**: MCP server implementation
- **chuk-mcp-server**: Base MCP framework
- **chuk-artifacts**: VFS scene access
- **subprocess**: Vite dev server management
- **watchdog**: File system monitoring for hot reload

### Frontend (Preview App)

- **React 18**: UI framework
- **React Three Fiber**: Three.js React renderer
- **@react-three/drei**: R3F helpers (OrbitControls, etc.)
- **@react-three/rapier**: Physics visualization (optional)
- **Vite**: Dev server with HMR
- **zustand**: State management
- **socket.io-client**: Hot reload notifications

## Project Structure

```
chuk-mcp-r3f-preview/
├── src/
│   ├── chuk_mcp_r3f_preview/
│   │   ├── __init__.py
│   │   ├── server.py           # MCP server tools
│   │   ├── preview_manager.py  # Vite server lifecycle
│   │   ├── scene_watcher.py    # VFS file watching
│   │   └── models.py           # Pydantic models
│   └── preview-app/            # React + R3F app
│       ├── src/
│       │   ├── components/
│       │   │   ├── SceneRenderer.tsx
│       │   │   ├── CameraControls.tsx
│       │   │   ├── Timeline.tsx
│       │   │   ├── PhysicsPlayback.tsx
│       │   │   └── LightingPanel.tsx
│       │   ├── hooks/
│       │   │   ├── useSceneLoader.ts
│       │   │   ├── useHotReload.ts
│       │   │   └── usePhysicsPlayback.ts
│       │   ├── store/
│       │   │   └── previewStore.ts
│       │   ├── App.tsx
│       │   └── main.tsx
│       ├── package.json
│       └── vite.config.ts
├── tests/
├── pyproject.toml
└── README.md
```

## Implementation Plan

### Phase 1: MCP Server Core
1. ✅ Project scaffolding
2. ✅ PreviewManager class (Vite lifecycle)
3. ✅ MCP tools (start, stop, reload, status)
4. ✅ Basic tests

### Phase 2: React App Foundation
1. ✅ Vite + React + R3F setup
2. ✅ Scene loader from JSON
3. ✅ Basic orbit controls
4. ✅ Object rendering (all types)

### Phase 3: Hot Reload
1. ✅ File watcher in Python
2. ✅ WebSocket server
3. ✅ Client WebSocket connection
4. ✅ Auto scene refresh

### Phase 4: Camera & Timeline
1. ⏳ Shot timeline UI
2. ⏳ Camera path playback
3. ⏳ Scrubber controls
4. ⏳ Split view comparison

### Phase 5: Physics & Polish
1. ⏳ Baked animation playback
2. ⏳ Trajectory trail rendering
3. ⏳ Lighting panel
4. ⏳ Performance optimization

## Usage Example

```python
from chuk_mcp_stage.server import stage_create_scene, stage_add_object, stage_add_shot
from chuk_mcp_r3f_preview.server import preview_start

# Create scene
scene = await stage_create_scene(name="Preview Demo")
scene_id = scene.scene_id

# Add objects
await stage_add_object(
    scene_id=scene_id,
    object_id="ground",
    object_type="plane",
    size_x=20.0,
    size_y=20.0,
    material_preset="plastic-white"
)

await stage_add_object(
    scene_id=scene_id,
    object_id="ball",
    object_type="sphere",
    position_y=5.0,
    radius=1.0,
    material_preset="glass-blue"
)

# Add camera shot
await stage_add_shot(
    scene_id=scene_id,
    shot_id="orbit",
    camera_mode="orbit",
    start_time=0.0,
    end_time=10.0,
    focus_object="ball",
    orbit_radius=8.0,
    orbit_elevation=30.0,
    orbit_speed=0.1
)

# Start preview
preview = await preview_start(scene_id=scene_id, auto_reload=True)
print(f"Preview running at: {preview.preview_url}")

# Browser automatically opens to http://localhost:3000
# Make changes to scene...
await stage_add_object(scene_id=scene_id, object_id="box", object_type="box")
# Preview auto-reloads with new box!
```

## Benefits

1. **Faster Iteration**: See changes immediately without manual export
2. **Visual Debugging**: Identify transform/material issues quickly
3. **Camera Tuning**: Fine-tune camera paths interactively
4. **Physics Validation**: Verify baked animations match expectations
5. **Lighting Exploration**: Try different lighting setups in real-time
6. **Client Presentation**: Share live preview URL for feedback

## Future Enhancements

- **Screenshot/Recording**: Capture stills or videos from preview
- **VR Preview**: WebXR support for immersive preview
- **Collaborative Mode**: Multi-user preview with shared cursor
- **Performance Profiling**: FPS counter, draw call stats
- **Asset Browser**: Drag-drop mesh imports
- **Material Editor**: Real-time PBR parameter tweaking
