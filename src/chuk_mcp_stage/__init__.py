"""chuk-mcp-stage - 3D Scene & Camera MCP Server.

The director layer between physics simulation and motion rendering.

Key exports:
- Models: Scene, Shot, CameraPath, SceneObject
- SceneManager: Core scene management
- PhysicsBridge: Physics integration
- SceneExporter: R3F/Remotion export

Example:
    from chuk_mcp_stage import SceneManager, Scene
    from chuk_mcp_stage.models import ObjectType, CameraPathMode

    async with SceneManager() as manager:
        scene = await manager.create_scene("my-scene")
        # ... build scene
"""

from .exporters import SceneExporter
from .models import (
    BakedAnimation,
    CameraPath,
    CameraPathMode,
    Color,
    EasingFunction,
    Environment,
    EnvironmentType,
    ExportFormat,
    Label,
    Lighting,
    LightingPreset,
    Material,
    MaterialPreset,
    ObjectType,
    Quaternion,
    Scene,
    SceneMetadata,
    SceneObject,
    Shot,
    Trail,
    Transform,
    Vector3,
)
from .physics_bridge import PhysicsBridge
from .scene_manager import SceneManager

__version__ = "0.1.0"

__all__ = [
    # Core
    "SceneManager",
    "PhysicsBridge",
    "SceneExporter",
    # Scene Models
    "Scene",
    "SceneMetadata",
    "SceneObject",
    "Shot",
    # Geometry
    "Vector3",
    "Quaternion",
    "Transform",
    "Color",
    # Materials & Appearance
    "Material",
    "MaterialPreset",
    "Trail",
    "Label",
    # Environment
    "Environment",
    "EnvironmentType",
    "Lighting",
    "LightingPreset",
    # Camera
    "CameraPath",
    "CameraPathMode",
    "EasingFunction",
    # Physics & Animation
    "BakedAnimation",
    # Export
    "ExportFormat",
    "ObjectType",
]
