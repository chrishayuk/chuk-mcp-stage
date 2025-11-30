"""Data models for chuk-mcp-stage.

Strongly typed models for 3D scenes, camera paths, shots, and exports.
No dictionary goop - everything is Pydantic with enums and validation.
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Enums and Constants
# ============================================================================


class ObjectType(str, Enum):
    """3D object primitive types."""

    BOX = "box"
    SPHERE = "sphere"
    CYLINDER = "cylinder"
    CAPSULE = "capsule"
    PLANE = "plane"
    MESH = "mesh"  # Imported glTF/GLB


class MaterialPreset(str, Enum):
    """Material appearance presets."""

    METAL_DARK = "metal-dark"
    METAL_LIGHT = "metal-light"
    GLASS_CLEAR = "glass-clear"
    GLASS_BLUE = "glass-blue"
    GLASS_GREEN = "glass-green"
    PLASTIC_RED = "plastic-red"
    PLASTIC_BLUE = "plastic-blue"
    PLASTIC_WHITE = "plastic-white"
    RUBBER_BLACK = "rubber-black"
    WOOD_OAK = "wood-oak"
    CUSTOM = "custom"


class LightingPreset(str, Enum):
    """Scene lighting presets."""

    STUDIO = "studio"
    THREE_POINT = "three-point"
    NOON = "noon"
    SUNSET = "sunset"
    NIGHT = "night"
    WAREHOUSE = "warehouse"
    CUSTOM = "custom"


class EnvironmentType(str, Enum):
    """Environment/background types."""

    HDRI = "hdri"
    GRADIENT = "gradient"
    SOLID = "solid"
    NONE = "none"


class CameraPathMode(str, Enum):
    """Camera movement modes."""

    ORBIT = "orbit"  # Circular orbit around focus point
    CHASE = "chase"  # Follow target with offset
    DOLLY = "dolly"  # Linear move from A to B
    FLYTHROUGH = "flythrough"  # Follow spline path
    CRANE = "crane"  # Arc movement
    STATIC = "static"  # Fixed position
    TRACK = "track"  # Follow custom path


class EasingFunction(str, Enum):
    """Motion easing functions (compatible with chuk-motion)."""

    LINEAR = "linear"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    EASE_IN_CUBIC = "ease-in-cubic"
    EASE_OUT_CUBIC = "ease-out-cubic"
    EASE_IN_OUT_CUBIC = "ease-in-out-cubic"
    SPRING = "spring"


class ExportFormat(str, Enum):
    """Export template formats."""

    R3F_COMPONENT = "r3f-component"  # React Three Fiber component
    REMOTION_PROJECT = "remotion-project"  # Full Remotion project
    GLTF = "gltf"  # Static glTF scene
    JSON = "json"  # Raw JSON scene data


# ============================================================================
# Core 3D Types
# ============================================================================


class Vector3(BaseModel):
    """3D vector or position."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_list(self) -> list[float]:
        """Convert to [x, y, z] list."""
        return [self.x, self.y, self.z]


class Quaternion(BaseModel):
    """Quaternion rotation (x, y, z, w)."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0  # Identity rotation

    def to_list(self) -> list[float]:
        """Convert to [x, y, z, w] list."""
        return [self.x, self.y, self.z, self.w]


class Transform(BaseModel):
    """3D transformation."""

    position: Vector3 = Field(default_factory=Vector3)
    rotation: Quaternion = Field(default_factory=Quaternion)
    scale: Vector3 = Field(default_factory=lambda: Vector3(x=1.0, y=1.0, z=1.0))


class Color(BaseModel):
    """RGB color (0-1 range)."""

    r: float = Field(ge=0.0, le=1.0)
    g: float = Field(ge=0.0, le=1.0)
    b: float = Field(ge=0.0, le=1.0)


# ============================================================================
# Materials and Appearance
# ============================================================================


class Material(BaseModel):
    """Material definition."""

    preset: MaterialPreset = MaterialPreset.PLASTIC_WHITE
    color: Optional[Color] = None
    roughness: float = Field(default=0.5, ge=0.0, le=1.0)
    metalness: float = Field(default=0.0, ge=0.0, le=1.0)
    transmission: float = Field(default=0.0, ge=0.0, le=1.0)  # For glass
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)


class Trail(BaseModel):
    """Trajectory trail visualization."""

    length: int = Field(default=120, description="Number of past positions to show")
    color: str = Field(default="accent", description="Trail color (theme color or hex)")
    fade: bool = Field(default=True, description="Fade out older positions")
    width: float = Field(default=0.05, description="Trail line width")


class Label(BaseModel):
    """Text label attached to object."""

    text: str
    font_size: float = 1.0
    color: str = "white"
    offset: Vector3 = Field(default_factory=Vector3)
    always_face_camera: bool = True


# ============================================================================
# Scene Objects
# ============================================================================


class SceneObject(BaseModel):
    """An object in the 3D scene."""

    id: str = Field(description="Unique object identifier")
    type: ObjectType
    transform: Transform = Field(default_factory=Transform)
    material: Material = Field(default_factory=Material)

    # Geometry parameters (type-specific)
    size: Optional[Vector3] = None  # For box
    radius: Optional[float] = None  # For sphere, cylinder, capsule
    height: Optional[float] = None  # For cylinder, capsule
    mesh_path: Optional[str] = None  # For mesh (VFS path or URL)

    # Physics binding
    physics_binding: Optional[str] = Field(
        default=None, description="Physics body ID (e.g., 'rapier://sim-001/body-bob')"
    )

    # Visualization enhancements
    trail: Optional[Trail] = None
    label: Optional[Label] = None

    # Custom metadata
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Environment and Lighting
# ============================================================================


class Environment(BaseModel):
    """Scene environment/background."""

    type: EnvironmentType = EnvironmentType.GRADIENT
    hdri_path: Optional[str] = None  # VFS path for HDRI
    color_top: Color = Field(default_factory=lambda: Color(r=0.5, g=0.7, b=1.0))
    color_bottom: Color = Field(default_factory=lambda: Color(r=1.0, g=1.0, b=1.0))
    intensity: float = Field(default=0.8, ge=0.0)


class Lighting(BaseModel):
    """Scene lighting configuration."""

    preset: LightingPreset = LightingPreset.THREE_POINT
    ambient_intensity: float = Field(default=0.5, ge=0.0)
    custom_lights: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Camera and Shots
# ============================================================================


class CameraPath(BaseModel):
    """Camera animation path definition."""

    mode: CameraPathMode
    focus: Optional[str] = Field(
        default=None, description="Object ID to focus on (for orbit/chase modes)"
    )
    position: Optional[Vector3] = None  # For static mode
    look_at: Optional[Vector3] = None  # For static/dolly modes

    # Orbit parameters
    radius: Optional[float] = None
    elevation: Optional[float] = None  # Degrees
    speed: Optional[float] = None  # Revolutions per second

    # Dolly parameters
    from_position: Optional[Vector3] = None
    to_position: Optional[Vector3] = None

    # Chase parameters
    offset: Optional[Vector3] = None  # Offset from target
    damping: Optional[float] = None  # Smoothing factor

    # Flythrough/track parameters
    waypoints: Optional[list[Vector3]] = None


class Shot(BaseModel):
    """A shot defines camera path + time range."""

    id: str = Field(description="Unique shot identifier")
    camera_path: CameraPath
    start_time: float = Field(ge=0.0, description="Start time in seconds")
    end_time: float = Field(gt=0.0, description="End time in seconds")
    easing: EasingFunction = EasingFunction.EASE_IN_OUT_CUBIC
    label: Optional[str] = None


# ============================================================================
# Physics Integration
# ============================================================================


class PhysicsBinding(BaseModel):
    """Binding between scene object and physics body."""

    object_id: str
    physics_body_id: str  # e.g., "rapier://sim-001/body-bob"
    scene_id: str


class BakedAnimation(BaseModel):
    """Baked animation data from physics simulation."""

    object_id: str
    source: str  # Physics simulation ID
    fps: int = Field(default=60, description="Frames per second")
    frames: int = Field(description="Total number of frames")
    data_path: str = Field(description="VFS path to animation data (binary or JSON)")


# ============================================================================
# Scene Definition
# ============================================================================


class SceneMetadata(BaseModel):
    """Scene metadata."""

    author: Optional[str] = None
    created: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class Scene(BaseModel):
    """Complete 3D scene definition."""

    id: str = Field(description="Unique scene identifier")
    name: Optional[str] = None
    metadata: SceneMetadata = Field(default_factory=SceneMetadata)

    # Scene content
    objects: dict[str, SceneObject] = Field(default_factory=dict)
    environment: Environment = Field(default_factory=Environment)
    lighting: Lighting = Field(default_factory=Lighting)

    # Cinematography
    shots: dict[str, Shot] = Field(default_factory=dict)

    # Physics integration
    baked_animations: dict[str, BakedAnimation] = Field(default_factory=dict)


# ============================================================================
# API Request/Response Models
# ============================================================================


class CreateSceneRequest(BaseModel):
    """Request to create a new scene."""

    name: Optional[str] = None
    metadata: Optional[SceneMetadata] = None


class CreateSceneResponse(BaseModel):
    """Response from creating a scene."""

    scene_id: str
    message: str = "Scene created successfully"


class AddObjectRequest(BaseModel):
    """Request to add an object to a scene."""

    scene_id: str
    object_id: str
    object_type: ObjectType
    transform: Optional[Transform] = None
    material: Optional[Material] = None
    size: Optional[Vector3] = None
    radius: Optional[float] = None
    height: Optional[float] = None
    mesh_path: Optional[str] = None


class AddObjectResponse(BaseModel):
    """Response from adding an object."""

    object_id: str
    scene_id: str
    message: str = "Object added successfully"


class SetEnvironmentRequest(BaseModel):
    """Request to set scene environment."""

    scene_id: str
    environment: Environment
    lighting: Optional[Lighting] = None


class SetEnvironmentResponse(BaseModel):
    """Response from setting environment."""

    scene_id: str
    message: str = "Environment updated successfully"


class CreateCameraPathRequest(BaseModel):
    """Request to create a camera path."""

    scene_id: str
    mode: CameraPathMode
    focus: Optional[str] = None
    position: Optional[Vector3] = None
    look_at: Optional[Vector3] = None
    radius: Optional[float] = None
    elevation: Optional[float] = None
    speed: Optional[float] = None
    from_position: Optional[Vector3] = None
    to_position: Optional[Vector3] = None
    offset: Optional[Vector3] = None
    damping: Optional[float] = None
    waypoints: Optional[list[Vector3]] = None


class AddShotRequest(BaseModel):
    """Request to add a shot."""

    scene_id: str
    shot_id: str
    camera_path: CameraPath
    start_time: float
    end_time: float
    easing: EasingFunction = EasingFunction.EASE_IN_OUT_CUBIC
    label: Optional[str] = None


class AddShotResponse(BaseModel):
    """Response from adding a shot."""

    shot_id: str
    scene_id: str
    duration: float
    message: str = "Shot added successfully"


class GetShotResponse(BaseModel):
    """Response containing shot details."""

    shot: Shot
    scene_id: str


class BindPhysicsRequest(BaseModel):
    """Request to bind object to physics body."""

    scene_id: str
    object_id: str
    physics_body_id: str


class BindPhysicsResponse(BaseModel):
    """Response from binding physics."""

    object_id: str
    physics_body_id: str
    message: str = "Physics binding created successfully"


class BakeSimulationRequest(BaseModel):
    """Request to bake physics simulation to keyframes."""

    scene_id: str
    simulation_id: str
    body_ids: list[str]  # Physics body IDs to bake
    fps: int = 60
    duration: Optional[float] = None  # If None, bake entire simulation


class BakeSimulationResponse(BaseModel):
    """Response from baking simulation."""

    scene_id: str
    baked_objects: list[str]  # Object IDs that got animation data
    total_frames: int
    fps: int
    message: str = "Simulation baked successfully"


class ExportSceneRequest(BaseModel):
    """Request to export scene."""

    scene_id: str
    format: ExportFormat = ExportFormat.R3F_COMPONENT
    output_path: Optional[str] = None  # VFS path, if None creates temp


class ExportSceneResponse(BaseModel):
    """Response from exporting scene."""

    scene_id: str
    format: ExportFormat
    output_path: str  # VFS path to exported content
    artifacts: dict[str, str] = Field(
        default_factory=dict, description="Additional generated files"
    )
    message: str = "Scene exported successfully"


class GetSceneResponse(BaseModel):
    """Response containing complete scene."""

    scene: Scene
