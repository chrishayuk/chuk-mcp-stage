"""Stage MCP Server.

3D scene composition, camera control, and physics-to-motion orchestration.

Features:
- Scene graph management (objects, transforms, materials)
- Camera paths and cinematography (shots, movements)
- Physics integration (bind objects to Rapier bodies)
- Animation baking (physics → keyframes)
- Export to R3F, Remotion, glTF

This is the "director" layer that sits between:
- chuk-mcp-physics (simulation engine)
- chuk-motion / Remotion (video rendering)

All data stored via chuk-artifacts for persistence and sharing.
"""

import logging
import sys
from typing import Optional

from chuk_mcp_server import get_mcp_server, run, tool  # type: ignore[attr-defined]

try:
    from chuk_mcp_server.oauth.helpers import setup_google_drive_oauth
except ImportError:
    setup_google_drive_oauth = None  # type: ignore[assignment]

from .exporters import SceneExporter
from .models import (
    AddObjectResponse,
    AddShotResponse,
    BakeSimulationResponse,
    BakedAnimation,
    BindPhysicsResponse,
    CameraPath,
    CreateSceneResponse,
    ExportFormat,
    ExportSceneResponse,
    GetSceneResponse,
    GetShotResponse,
    Material,
    SceneObject,
    SetEnvironmentResponse,
    Shot,
    Transform,
)
from .physics_bridge import PhysicsBridge
from .scene_manager import SceneManager

# Configure logging
logging.basicConfig(
    level=logging.WARNING, format="%(levelname)s:%(name)s:%(message)s", stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Global scene manager instance
_scene_manager: Optional[SceneManager] = None


def get_scene_manager() -> SceneManager:
    """Get or create the global scene manager."""
    global _scene_manager
    if _scene_manager is None:
        _scene_manager = SceneManager()
    return _scene_manager


# ============================================================================
# Scene Management Tools
# ============================================================================


@tool  # type: ignore[arg-type]
async def stage_create_scene(
    name: Optional[str] = None,
    author: Optional[str] = None,
    description: Optional[str] = None,
) -> CreateSceneResponse:
    """Create a new 3D scene for composition.

    Initializes a new scene workspace backed by chuk-artifacts.
    The scene can contain 3D objects, lighting, camera shots, and physics bindings.

    Args:
        name: Optional scene name (e.g., "pendulum-demo", "f1-silverstone-t1")
        author: Optional author name for metadata
        description: Optional scene description

    Returns:
        CreateSceneResponse with scene_id and success message

    Tips for LLMs:
        - Scene ID is auto-generated (UUID)
        - Scenes are stored in chuk-artifacts SESSION scope (ephemeral by default)
        - Use the scene_id for all subsequent operations
        - Typical workflow: create_scene → add_objects → add_shots → export

    Example:
        scene = await stage_create_scene(
            name="falling-ball-demo",
            author="Claude",
            description="Simple gravity demonstration"
        )
        # Use scene.scene_id for next steps
    """
    from .models import SceneMetadata

    manager = get_scene_manager()

    # Generate scene ID
    import uuid

    scene_id = f"scene-{uuid.uuid4().hex[:8]}"

    # Create metadata
    metadata = SceneMetadata(author=author, description=description)

    # Create scene
    scene = await manager.create_scene(scene_id=scene_id, name=name, metadata=metadata)

    return CreateSceneResponse(scene_id=scene.id, message=f"Scene '{name or scene_id}' created")


@tool  # type: ignore[arg-type]
async def stage_add_object(
    scene_id: str,
    object_id: str,
    object_type: str,
    position_x: float = 0.0,
    position_y: float = 0.0,
    position_z: float = 0.0,
    rotation_x: float = 0.0,
    rotation_y: float = 0.0,
    rotation_z: float = 0.0,
    rotation_w: float = 1.0,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    scale_z: float = 1.0,
    size_x: Optional[float] = None,
    size_y: Optional[float] = None,
    size_z: Optional[float] = None,
    radius: Optional[float] = None,
    height: Optional[float] = None,
    material_preset: str = "plastic-white",
    color_r: float = 1.0,
    color_g: float = 1.0,
    color_b: float = 1.0,
) -> AddObjectResponse:
    """Add a 3D object to the scene.

    Adds primitives (box, sphere, cylinder, etc.) or placeholders for meshes.
    Objects can be bound to physics bodies later for animation.

    Args:
        scene_id: Scene identifier
        object_id: Unique object name (e.g., "ground", "ball", "car")
        object_type: Object type - "box", "sphere", "cylinder", "capsule", "plane", "mesh"
        position_x, position_y, position_z: Position in 3D space
        rotation_x, rotation_y, rotation_z, rotation_w: Rotation quaternion
        scale_x, scale_y, scale_z: Scale factors
        size_x, size_y, size_z: Size for box (width, height, depth)
        radius: Radius for sphere/cylinder/capsule
        height: Height for cylinder/capsule
        material_preset: Material preset - "metal-dark", "glass-blue", "plastic-white", etc.
        color_r, color_g, color_b: RGB color (0.0-1.0)

    Returns:
        AddObjectResponse with object_id confirmation

    Tips for LLMs:
        - For ground: object_type="plane", large size, static
        - For dynamic objects: smaller primitives that match physics bodies
        - Quaternion: [0,0,0,1] is identity (no rotation)
        - Common materials: "metal-dark", "glass-blue", "plastic-white", "rubber-black"

    Example:
        # Add ground plane
        await stage_add_object(
            scene_id=scene_id,
            object_id="ground",
            object_type="plane",
            size_x=20.0,
            size_y=20.0,
            material_preset="metal-dark"
        )

        # Add falling sphere
        await stage_add_object(
            scene_id=scene_id,
            object_id="ball",
            object_type="sphere",
            radius=1.0,
            position_y=5.0,
            material_preset="glass-blue",
            color_r=0.3,
            color_g=0.5,
            color_b=1.0
        )
    """
    from .models import Color, MaterialPreset, ObjectType, Vector3

    manager = get_scene_manager()

    # Build transform
    transform = Transform(
        position=Vector3(x=position_x, y=position_y, z=position_z),
        rotation={"x": rotation_x, "y": rotation_y, "z": rotation_z, "w": rotation_w},
        scale=Vector3(x=scale_x, y=scale_y, z=scale_z),
    )

    # Build material
    material = Material(
        preset=MaterialPreset(material_preset), color=Color(r=color_r, g=color_g, b=color_b)
    )

    # Build size vector if provided
    size = Vector3(x=size_x, y=size_y, z=size_z or 0.0) if size_x is not None else None

    # Create object
    obj = SceneObject(
        id=object_id,
        type=ObjectType(object_type),
        transform=transform,
        material=material,
        size=size,
        radius=radius,
        height=height,
    )

    # Add to scene
    await manager.add_object(scene_id, obj)

    return AddObjectResponse(object_id=object_id, scene_id=scene_id)


@tool  # type: ignore[arg-type]
async def stage_set_environment(
    scene_id: str,
    environment_type: str = "gradient",
    lighting_preset: str = "three-point",
    intensity: float = 0.8,
) -> SetEnvironmentResponse:
    """Set scene environment and lighting.

    Configures the background, ambient lighting, and light sources.

    Args:
        scene_id: Scene identifier
        environment_type: "gradient", "solid", "hdri", or "none"
        lighting_preset: "studio", "three-point", "noon", "sunset", "warehouse"
        intensity: Overall light intensity (0.0-2.0)

    Returns:
        SetEnvironmentResponse confirmation

    Example:
        await stage_set_environment(
            scene_id=scene_id,
            environment_type="gradient",
            lighting_preset="three-point"
        )
    """
    from .models import Environment, EnvironmentType, Lighting, LightingPreset

    manager = get_scene_manager()

    environment = Environment(type=EnvironmentType(environment_type), intensity=intensity)
    lighting = Lighting(preset=LightingPreset(lighting_preset))

    await manager.set_environment(scene_id, environment, lighting)

    return SetEnvironmentResponse(scene_id=scene_id)


# ============================================================================
# Camera and Shot Tools
# ============================================================================


@tool  # type: ignore[arg-type]
async def stage_add_shot(
    scene_id: str,
    shot_id: str,
    camera_mode: str,
    start_time: float,
    end_time: float,
    focus_object: Optional[str] = None,
    orbit_radius: Optional[float] = None,
    orbit_elevation: Optional[float] = None,
    orbit_speed: Optional[float] = None,
    static_position_x: Optional[float] = None,
    static_position_y: Optional[float] = None,
    static_position_z: Optional[float] = None,
    look_at_x: Optional[float] = None,
    look_at_y: Optional[float] = None,
    look_at_z: Optional[float] = None,
    easing: str = "ease-in-out-cubic",
) -> AddShotResponse:
    """Add a camera shot to the scene.

    Defines a camera movement path and time range for cinematography.

    Args:
        scene_id: Scene identifier
        shot_id: Unique shot name (e.g., "intro-orbit", "close-up")
        camera_mode: "orbit", "static", "chase", "dolly", "flythrough", "crane", "track"
        start_time: Shot start time in seconds
        end_time: Shot end time in seconds
        focus_object: Object ID to focus on (for orbit/chase modes)
        orbit_radius: Distance from focus object (orbit mode)
        orbit_elevation: Camera elevation angle in degrees (orbit mode)
        orbit_speed: Rotation speed in revolutions per second (orbit mode)
        static_position_x, static_position_y, static_position_z: Camera position (static mode)
        look_at_x, look_at_y, look_at_z: Point to look at
        easing: Easing function - "linear", "ease-in-out", "spring", etc.

    Returns:
        AddShotResponse with shot details

    Tips for LLMs:
        - Orbit mode: Great for product shots, object inspection
        - Static mode: Fixed camera, good for observing motion
        - Chase mode: Follow moving objects
        - Multiple shots can be sequenced for different camera angles

    Example:
        # Orbiting shot around falling ball
        await stage_add_shot(
            scene_id=scene_id,
            shot_id="orbit-shot",
            camera_mode="orbit",
            focus_object="ball",
            orbit_radius=8.0,
            orbit_elevation=30.0,
            orbit_speed=0.1,
            start_time=0.0,
            end_time=10.0
        )
    """
    from .models import CameraPathMode, EasingFunction, Vector3

    manager = get_scene_manager()

    # Build camera path
    camera_path = CameraPath(
        mode=CameraPathMode(camera_mode),
        focus=focus_object,
        radius=orbit_radius,
        elevation=orbit_elevation,
        speed=orbit_speed,
        position=Vector3(
            x=static_position_x or 0, y=static_position_y or 0, z=static_position_z or 0
        )
        if static_position_x is not None
        else None,
        look_at=Vector3(x=look_at_x or 0, y=look_at_y or 0, z=look_at_z or 0)
        if look_at_x is not None
        else None,
    )

    # Create shot
    shot = Shot(
        id=shot_id,
        camera_path=camera_path,
        start_time=start_time,
        end_time=end_time,
        easing=EasingFunction(easing),
    )

    # Add to scene
    await manager.add_shot(scene_id, shot)

    duration = end_time - start_time
    return AddShotResponse(shot_id=shot_id, scene_id=scene_id, duration=duration)


@tool  # type: ignore[arg-type]
async def stage_get_shot(scene_id: str, shot_id: str) -> GetShotResponse:
    """Get shot details from a scene.

    Args:
        scene_id: Scene identifier
        shot_id: Shot identifier

    Returns:
        GetShotResponse with shot data
    """
    manager = get_scene_manager()
    shot = await manager.get_shot(scene_id, shot_id)
    return GetShotResponse(shot=shot, scene_id=scene_id)


# ============================================================================
# Physics Integration Tools
# ============================================================================


@tool  # type: ignore[arg-type]
async def stage_bind_physics(
    scene_id: str, object_id: str, physics_body_id: str
) -> BindPhysicsResponse:
    """Bind a scene object to a physics body.

    Links a visual object to a physics simulation body so that
    the physics simulation drives the object's animation.

    Args:
        scene_id: Scene identifier
        object_id: Scene object ID
        physics_body_id: Physics body ID from chuk-mcp-physics
            Format: "rapier://sim-{sim_id}/body-{body_id}"
            Example: "rapier://sim-abc123/body-ball"

    Returns:
        BindPhysicsResponse confirmation

    Tips for LLMs:
        - Create physics body first using chuk-mcp-physics
        - Then create matching scene object with same shape/size
        - Bind them together so physics drives visuals
        - Use stage_bake_simulation to convert physics → keyframes

    Example:
        # 1. Create physics simulation (chuk-mcp-physics)
        sim = await create_simulation(gravity_y=-9.81)

        # 2. Add physics body
        await add_rigid_body(
            sim_id=sim.sim_id,
            body_id="ball",
            body_type="dynamic",
            shape="sphere",
            radius=1.0,
            position=[0, 5, 0]
        )

        # 3. Create scene object
        await stage_add_object(
            scene_id=scene_id,
            object_id="ball",
            object_type="sphere",
            radius=1.0,
            position_y=5.0
        )

        # 4. Bind them
        await stage_bind_physics(
            scene_id=scene_id,
            object_id="ball",
            physics_body_id=f"rapier://{sim.sim_id}/body-ball"
        )
    """
    manager = get_scene_manager()
    await manager.bind_physics(scene_id, object_id, physics_body_id)

    return BindPhysicsResponse(
        object_id=object_id, physics_body_id=physics_body_id, message="Physics binding created"
    )


@tool  # type: ignore[arg-type]
async def stage_bake_simulation(
    scene_id: str,
    simulation_id: str,
    fps: int = 60,
    duration: Optional[float] = None,
    physics_server_url: Optional[str] = None,
) -> BakeSimulationResponse:
    """Bake physics simulation to keyframe animations.

    Converts physics simulation data into keyframes that can be
    exported to R3F/Remotion for video rendering.

    Args:
        scene_id: Scene identifier
        simulation_id: Physics simulation ID from chuk-mcp-physics
        fps: Frames per second for sampling (default 60)
        duration: Duration in seconds to bake (if None, bakes entire simulation)
        physics_server_url: Optional Rapier HTTP server URL
            If None, defaults to public Rapier service (https://rapier.chukai.io)
            Can be overridden with RAPIER_SERVICE_URL environment variable

    Returns:
        BakeSimulationResponse with frame count and baked object list

    Tips for LLMs:
        - Run physics simulation first (chuk-mcp-physics step_simulation or record_trajectory)
        - Bind objects to physics bodies (stage_bind_physics)
        - Bake simulation to convert physics → animation keyframes
        - Then export scene to R3F/Remotion with animation data

    Example:
        # After running simulation and binding objects
        result = await stage_bake_simulation(
            scene_id=scene_id,
            simulation_id=sim.sim_id,
            fps=60,
            duration=10.0
        )
        print(f"Baked {result.total_frames} frames for {len(result.baked_objects)} objects")
    """
    manager = get_scene_manager()
    scene = await manager.get_scene(scene_id)

    # Find all objects with physics bindings
    bound_objects = [
        (obj_id, obj)
        for obj_id, obj in scene.objects.items()
        if obj.physics_binding and simulation_id in obj.physics_binding
    ]

    if not bound_objects:
        raise ValueError(f"No objects bound to simulation {simulation_id}")

    # Extract body IDs from bindings
    body_ids = []
    for obj_id, obj in bound_objects:
        # Parse "rapier://sim-{sim_id}/body-{body_id}"
        parts = obj.physics_binding.split("/")  # type: ignore
        if len(parts) >= 2:
            body_id = parts[-1].replace("body-", "")
            body_ids.append(body_id)

    logger.info(f"Baking simulation {simulation_id} for {len(body_ids)} bodies")

    # Use physics bridge to bake
    async with PhysicsBridge(physics_server_url) as bridge:
        baked_data = await bridge.bake_simulation(simulation_id, body_ids, fps, duration)

    # Store baked animations in scene workspace
    vfs = await manager.get_scene_vfs(scene_id)
    await vfs.mkdir("/animations")

    total_frames = 0
    baked_object_ids = []

    for obj_id, obj in bound_objects:
        # Get body ID
        body_id = obj.physics_binding.split("/")[-1].replace("body-", "")  # type: ignore

        if body_id in baked_data:
            keyframes = baked_data[body_id]
            total_frames = max(total_frames, len(keyframes))

            # Save keyframes to VFS
            keyframes_json = PhysicsBridge.keyframes_to_json(keyframes)
            animation_path = f"/animations/{obj_id}.json"
            await vfs.write_text(animation_path, keyframes_json)

            # Add baked animation to scene
            baked_anim = BakedAnimation(
                object_id=obj_id,
                source=simulation_id,
                fps=fps,
                frames=len(keyframes),
                data_path=animation_path,
            )
            await manager.add_baked_animation(scene_id, obj_id, baked_anim)

            baked_object_ids.append(obj_id)

    return BakeSimulationResponse(
        scene_id=scene_id,
        baked_objects=baked_object_ids,
        total_frames=total_frames,
        fps=fps,
        message=f"Baked {total_frames} frames for {len(baked_object_ids)} objects",
    )


# ============================================================================
# Export Tools
# ============================================================================


@tool  # type: ignore[arg-type]
async def stage_export_scene(
    scene_id: str, format: str = "r3f-component", output_path: Optional[str] = None
) -> ExportSceneResponse:
    """Export scene to R3F, Remotion, or glTF format.

    Converts the scene definition into code/files that can be used
    with React Three Fiber or Remotion for rendering.

    Args:
        scene_id: Scene identifier
        format: Export format - "r3f-component", "remotion-project", "gltf", "json"
        output_path: Optional VFS path for output (auto-generated if None)

    Returns:
        ExportSceneResponse with output paths

    Tips for LLMs:
        - "r3f-component": Generate React Three Fiber .tsx files
        - "remotion-project": Full Remotion project with package.json
        - "gltf": Static 3D scene file
        - "json": Raw scene JSON data
        - Exported files are in the scene's VFS workspace
        - Use chuk-artifacts to retrieve exported files

    Example:
        result = await stage_export_scene(
            scene_id=scene_id,
            format="remotion-project"
        )
        print(f"Exported to {result.output_path}")
        # Files available at result.artifacts paths
    """
    manager = get_scene_manager()
    scene = await manager.get_scene(scene_id)
    vfs = await manager.get_scene_vfs(scene_id)

    export_format = ExportFormat(format)

    # Use exporter
    artifacts = await SceneExporter.export_scene(scene, export_format, vfs, output_path)

    # Determine main output path
    main_path = artifacts.get("scene") or artifacts.get("component") or artifacts.get("gltf") or "/"

    return ExportSceneResponse(
        scene_id=scene_id, format=export_format, output_path=main_path, artifacts=artifacts
    )


@tool  # type: ignore[arg-type]
async def stage_get_scene(scene_id: str) -> GetSceneResponse:
    """Get complete scene data.

    Returns the full scene definition including all objects, shots,
    animations, and configuration.

    Args:
        scene_id: Scene identifier

    Returns:
        GetSceneResponse with complete Scene object
    """
    manager = get_scene_manager()
    scene = await manager.get_scene(scene_id)
    return GetSceneResponse(scene=scene)


# ============================================================================
# Main Entry Point
# ============================================================================


def main() -> None:
    """Run the Stage MCP server.

    Supports three transport modes:
    - stdio: Standard MCP protocol via stdin/stdout (default for Claude Desktop)
    - http: HTTP REST API server on port 8000
    - streamable: SSE (Server-Sent Events) transport for streaming responses

    Usage:
        uv run chuk-mcp-stage           # stdio mode (default)
        uv run chuk-mcp-stage http      # HTTP mode
        uv run chuk-mcp-stage streamable # SSE mode
    """
    # Default to stdio for MCP compatibility (Claude Desktop, mcp-cli)
    transport = "stdio"

    # Check command line args for transport mode
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["http", "--http"]:
            transport = "http"
            logger.warning("Starting Stage MCP Server in HTTP mode on port 8000")
        elif arg in ["streamable", "--streamable", "sse", "--sse"]:
            transport = "streamable"
            logger.warning("Starting Stage MCP Server in Streamable (SSE) mode")

    # Suppress logging in STDIO mode to avoid polluting JSON-RPC stream
    if transport == "stdio":
        logging.getLogger("chuk_mcp_server").setLevel(logging.ERROR)
        logging.getLogger("chuk_mcp_server.core").setLevel(logging.ERROR)
        logging.getLogger("chuk_mcp_server.stdio_transport").setLevel(logging.ERROR)
        logging.getLogger("httpx").setLevel(logging.ERROR)

    # Set up Google Drive OAuth if configured (HTTP mode only)
    oauth_hook = None
    if transport == "http" and setup_google_drive_oauth is not None:
        oauth_hook = setup_google_drive_oauth(get_mcp_server())
        if oauth_hook:
            logger.warning(
                "Google Drive OAuth enabled - set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"
            )

    # Run server with appropriate transport
    if transport == "http":
        run(transport=transport, host="0.0.0.0", port=8000, post_register_hook=oauth_hook)  # nosec B104
    else:
        run(transport=transport)


if __name__ == "__main__":
    main()
