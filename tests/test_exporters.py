"""Tests for scene exporters."""

import json
import pytest
from chuk_artifacts import ArtifactStore

from chuk_mcp_stage.exporters import SceneExporter
from chuk_mcp_stage.models import (
    BakedAnimation,
    CameraPath,
    CameraPathMode,
    Color,
    ExportFormat,
    Material,
    MaterialPreset,
    ObjectType,
    Quaternion,
    Scene,
    SceneMetadata,
    SceneObject,
    Shot,
    Transform,
    Vector3,
)


@pytest.fixture
async def vfs():
    """Create test VFS for export tests."""
    from chuk_artifacts import NamespaceType, StorageScope

    store = ArtifactStore()
    # Create default namespace for tests
    ns = await store.create_namespace(
        type=NamespaceType.WORKSPACE,
        name="test-export",
        scope=StorageScope.SESSION,
    )
    test_vfs = store.get_namespace_vfs(ns.namespace_id)
    yield test_vfs
    await store.close()


@pytest.fixture
def simple_scene():
    """Create a simple test scene."""
    scene = Scene(
        id="test-scene",
        name="Test Scene",
        metadata=SceneMetadata(author="Test Author"),
    )

    # Add a box
    scene.objects["box1"] = SceneObject(
        id="box1",
        type=ObjectType.BOX,
        transform=Transform(
            position=Vector3(x=0, y=1, z=0),
            rotation=Quaternion(x=0, y=0, z=0, w=1),
        ),
        material=Material(
            preset=MaterialPreset.PLASTIC_RED,
            color=Color(r=1.0, g=0.0, b=0.0),
            roughness=0.5,
            metalness=0.0,
        ),
        size=Vector3(x=2, y=2, z=2),
    )

    # Add a sphere
    scene.objects["sphere1"] = SceneObject(
        id="sphere1",
        type=ObjectType.SPHERE,
        transform=Transform(position=Vector3(x=5, y=1, z=0)),
        material=Material(preset=MaterialPreset.METAL_DARK),
        radius=1.5,
    )

    return scene


@pytest.fixture
def scene_with_shots():
    """Create scene with camera shots."""
    scene = Scene(
        id="shot-scene",
        name="Scene with Shots",
    )

    scene.objects["target"] = SceneObject(
        id="target",
        type=ObjectType.SPHERE,
        radius=1.0,
    )

    scene.shots["shot1"] = Shot(
        id="shot1",
        camera_path=CameraPath(
            mode=CameraPathMode.ORBIT,
            focus="target",
            radius=5.0,
            elevation=30.0,
            speed=0.1,
        ),
        start_time=0.0,
        end_time=5.0,
    )

    scene.shots["shot2"] = Shot(
        id="shot2",
        camera_path=CameraPath(
            mode=CameraPathMode.STATIC,
            position=Vector3(x=10, y=5, z=10),
            look_at=Vector3(x=0, y=0, z=0),
        ),
        start_time=5.0,
        end_time=10.0,
    )

    return scene


@pytest.fixture
def scene_with_animations():
    """Create scene with baked animations."""
    scene = Scene(
        id="anim-scene",
        name="Scene with Animations",
    )

    scene.objects["animated-obj"] = SceneObject(
        id="animated-obj",
        type=ObjectType.BOX,
        size=Vector3(x=1, y=1, z=1),
    )

    scene.baked_animations["animated-obj"] = BakedAnimation(
        object_id="animated-obj",
        source="physics-sim-001",
        fps=60,
        frames=300,
        data_path="/animations/obj-anim.json",
    )

    return scene


@pytest.mark.asyncio
@pytest.mark.vfs_integration
async def test_export_json(vfs, simple_scene):
    """Test JSON export."""
    result = await SceneExporter.export_scene(
        scene=simple_scene,
        format=ExportFormat.JSON,
        vfs=vfs,
        output_path="/test/scene.json",
    )

    assert "scene" in result
    assert result["scene"] == "/test/scene.json"

    # Verify file was written
    data = await vfs.read_text("/test/scene.json")
    parsed = json.loads(data)
    assert parsed["id"] == "test-scene"
    assert parsed["name"] == "Test Scene"
    assert "box1" in parsed["objects"]
    assert "sphere1" in parsed["objects"]


@pytest.mark.asyncio
@pytest.mark.vfs_integration
async def test_export_json_default_path(vfs, simple_scene):
    """Test JSON export with default path."""

    result = await SceneExporter.export_scene(
        scene=simple_scene,
        format=ExportFormat.JSON,
        vfs=vfs,
    )

    assert result["scene"] == "/export/scene.json"


@pytest.mark.asyncio
@pytest.mark.vfs_integration
async def test_export_r3f_basic(vfs, simple_scene):
    """Test R3F export basic functionality."""
    result = await SceneExporter.export_scene(
        scene=simple_scene,
        format=ExportFormat.R3F_COMPONENT,
        vfs=vfs,
        output_path="/test/r3f",
    )

    assert "component" in result
    assert result["component"] == "/test/r3f/Scene.tsx"

    # Verify component file
    component_code = await vfs.read_text("/test/r3f/Scene.tsx")
    assert "import React from 'react'" in component_code
    assert "Canvas" in component_code
    assert "OrbitControls" in component_code
    assert "boxGeometry" in component_code
    assert "sphereGeometry" in component_code
    assert "meshStandardMaterial" in component_code


@pytest.mark.asyncio
@pytest.mark.vfs_integration
async def test_export_r3f_with_shots(vfs, scene_with_shots):
    """Test R3F export with camera shots."""

    result = await SceneExporter.export_scene(
        scene=scene_with_shots,
        format=ExportFormat.R3F_COMPONENT,
        vfs=vfs,
    )

    assert "component" in result
    assert "camera" in result

    # Verify camera component was generated
    camera_code = await vfs.read_text(result["camera"])
    assert "AnimatedCamera" in camera_code
    assert "useFrame" in camera_code


@pytest.mark.asyncio
@pytest.mark.vfs_integration
async def test_export_r3f_with_animations(vfs, scene_with_animations):
    """Test R3F export with baked animations."""

    result = await SceneExporter.export_scene(
        scene=scene_with_animations,
        format=ExportFormat.R3F_COMPONENT,
        vfs=vfs,
    )

    assert "component" in result
    assert "animations" in result

    # Verify animations data file
    anim_data = await vfs.read_text(result["animations"])
    parsed = json.loads(anim_data)
    assert "animated-obj" in parsed
    assert parsed["animated-obj"]["fps"] == 60
    assert parsed["animated-obj"]["frames"] == 300


@pytest.mark.asyncio
@pytest.mark.vfs_integration
async def test_export_remotion_basic(vfs, simple_scene):
    """Test Remotion export basic functionality."""

    result = await SceneExporter.export_scene(
        scene=simple_scene,
        format=ExportFormat.REMOTION_PROJECT,
        vfs=vfs,
        output_path="/test/remotion",
    )

    assert "composition" in result
    assert "root" in result
    assert "package" in result

    # Verify composition
    composition = await vfs.read_text(result["composition"])
    assert "ThreeCanvas" in composition
    assert "@remotion/three" in composition

    # Verify root
    root = await vfs.read_text(result["root"])
    assert "Composition" in root
    assert "test-scene" in root

    # Verify package.json
    package = await vfs.read_text(result["package"])
    package_data = json.loads(package)
    assert package_data["name"] == "scene-test-scene"
    assert "remotion" in package_data["dependencies"]


@pytest.mark.asyncio
@pytest.mark.vfs_integration
async def test_export_remotion_with_shots(vfs, scene_with_shots):
    """Test Remotion export calculates duration from shots."""

    result = await SceneExporter.export_scene(
        scene=scene_with_shots,
        format=ExportFormat.REMOTION_PROJECT,
        vfs=vfs,
    )

    # Verify duration in root
    root = await vfs.read_text(result["root"])
    assert "durationInFrames={300}" in root  # 10 seconds * 30 fps


@pytest.mark.asyncio
@pytest.mark.vfs_integration
async def test_export_gltf_basic(vfs, simple_scene):
    """Test glTF export basic functionality."""

    result = await SceneExporter.export_scene(
        scene=simple_scene,
        format=ExportFormat.GLTF,
        vfs=vfs,
        output_path="/test/scene.gltf",
    )

    assert "gltf" in result
    assert result["gltf"] == "/test/scene.gltf"

    # Verify glTF structure
    gltf_data = await vfs.read_text("/test/scene.gltf")
    gltf = json.loads(gltf_data)

    assert gltf["asset"]["version"] == "2.0"
    assert gltf["asset"]["generator"] == "chuk-mcp-stage"
    assert len(gltf["nodes"]) == 2  # box1 and sphere1
    assert len(gltf["meshes"]) == 2


@pytest.mark.asyncio
@pytest.mark.vfs_integration
async def test_export_gltf_default_path(vfs, simple_scene):
    """Test glTF export with default path."""

    result = await SceneExporter.export_scene(
        scene=simple_scene,
        format=ExportFormat.GLTF,
        vfs=vfs,
    )

    assert result["gltf"] == "/export/scene.gltf"


@pytest.mark.asyncio
@pytest.mark.vfs_integration
async def test_export_unsupported_format(vfs, simple_scene):
    """Test error handling for unsupported format."""

    with pytest.raises(ValueError, match="Unsupported export format"):
        await SceneExporter.export_scene(
            scene=simple_scene,
            format="invalid-format",  # type: ignore
            vfs=vfs,
        )


def test_generate_r3f_component_cylinder():
    """Test R3F component generation with cylinder."""
    scene = Scene(id="test", name="Test")
    scene.objects["cyl"] = SceneObject(
        id="cyl",
        type=ObjectType.CYLINDER,
        radius=0.5,
        height=3.0,
    )

    code = SceneExporter._generate_r3f_component(scene)
    assert "cylinderGeometry" in code
    assert "0.5" in code and "3.0" in code


def test_generate_r3f_component_plane():
    """Test R3F component generation with plane."""
    scene = Scene(id="test", name="Test")
    scene.objects["plane"] = SceneObject(
        id="plane",
        type=ObjectType.PLANE,
        size=Vector3(x=10, y=10, z=0),
    )

    code = SceneExporter._generate_r3f_component(scene)
    assert "planeGeometry" in code
    assert "10" in code  # Check for size values


def test_generate_r3f_component_plane_default_size():
    """Test R3F component generation with plane default size."""
    scene = Scene(id="test", name="Test")
    scene.objects["plane"] = SceneObject(
        id="plane",
        type=ObjectType.PLANE,
    )

    code = SceneExporter._generate_r3f_component(scene)
    assert "planeGeometry args={[10, 10]}" in code


def test_generate_r3f_component_unknown_type():
    """Test R3F component generation with unknown type."""
    scene = Scene(id="test", name="Test")
    scene.objects["unknown"] = SceneObject(
        id="unknown",
        type=ObjectType.MESH,  # Will use default geometry
    )

    code = SceneExporter._generate_r3f_component(scene)
    assert "boxGeometry" in code  # Falls back to box


def test_generate_r3f_component_material_colors():
    """Test R3F component material color conversion."""
    scene = Scene(id="test", name="Test")
    scene.objects["obj"] = SceneObject(
        id="obj",
        type=ObjectType.BOX,
        material=Material(
            preset=MaterialPreset.CUSTOM,
            color=Color(r=0.5, g=0.8, b=0.2),
            roughness=0.3,
            metalness=0.7,
            opacity=0.9,
        ),
    )

    code = SceneExporter._generate_r3f_component(scene)
    assert "#7fcc33" in code  # RGB to hex
    assert "roughness={0.3}" in code
    assert "metalness={0.7}" in code
    assert "opacity={0.9}" in code
    assert "transparent={true}" in code


def test_generate_r3f_component_material_no_color():
    """Test R3F component with material without color."""
    scene = Scene(id="test", name="Test")
    scene.objects["obj"] = SceneObject(
        id="obj",
        type=ObjectType.BOX,
        material=Material(preset=MaterialPreset.METAL_DARK),
    )

    code = SceneExporter._generate_r3f_component(scene)
    assert "#ffffff" in code  # Default white


def test_generate_camera_component():
    """Test camera component generation."""
    scene = Scene(id="test", name="Test")
    scene.shots["shot1"] = Shot(
        id="shot1",
        camera_path=CameraPath(mode=CameraPathMode.ORBIT, radius=5.0),
        start_time=0.0,
        end_time=5.0,
    )

    code = SceneExporter._generate_camera_component(scene)
    assert "AnimatedCamera" in code
    assert "useFrame" in code
    assert "PerspectiveCamera" in code


def test_generate_animations_data():
    """Test animations data generation."""
    scene = Scene(id="test", name="Test")
    scene.baked_animations["obj1"] = BakedAnimation(
        object_id="obj1",
        source="physics-001",
        fps=60,
        frames=600,
        data_path="/anim/obj1.json",
    )
    scene.baked_animations["obj2"] = BakedAnimation(
        object_id="obj2",
        source="physics-002",
        fps=30,
        frames=300,
        data_path="/anim/obj2.json",
    )

    data = SceneExporter._generate_animations_data(scene)
    parsed = json.loads(data)

    assert "obj1" in parsed
    assert parsed["obj1"]["fps"] == 60
    assert parsed["obj1"]["frames"] == 600
    assert "obj2" in parsed
    assert parsed["obj2"]["fps"] == 30


def test_generate_remotion_composition():
    """Test Remotion composition generation."""
    scene = Scene(id="test", name="Test")

    code = SceneExporter._generate_remotion_composition(scene)
    assert "ThreeCanvas" in code
    assert "AbsoluteFill" in code
    assert "ambientLight" in code
    assert "directionalLight" in code


def test_generate_remotion_root_default_duration():
    """Test Remotion root with default duration."""
    scene = Scene(id="test-id", name="Test Scene")

    code = SceneExporter._generate_remotion_root(scene)
    assert "test-id" in code
    assert "durationInFrames={300}" in code  # 10 seconds default
    assert "fps={30}" in code


def test_generate_remotion_root_with_shots():
    """Test Remotion root calculates duration from shots."""
    scene = Scene(id="test-id", name="Test")
    scene.shots["shot1"] = Shot(
        id="shot1",
        camera_path=CameraPath(mode=CameraPathMode.STATIC),
        start_time=0.0,
        end_time=15.0,
    )

    code = SceneExporter._generate_remotion_root(scene)
    assert "durationInFrames={450}" in code  # 15 seconds * 30 fps


def test_generate_package_json():
    """Test package.json generation."""
    scene = Scene(id="my-scene", name="My Cool Scene")

    package_str = SceneExporter._generate_package_json(scene)
    package = json.loads(package_str)

    assert package["name"] == "scene-my-scene"
    assert package["description"] == "Remotion project for scene My Cool Scene"
    assert "remotion" in package["dependencies"]
    assert "@remotion/three" in package["dependencies"]
    assert "react" in package["dependencies"]
    assert "start" in package["scripts"]
    assert "build" in package["scripts"]


def test_generate_package_json_no_name():
    """Test package.json generation without scene name."""
    scene = Scene(id="scene-id")

    package_str = SceneExporter._generate_package_json(scene)
    package = json.loads(package_str)

    assert package["description"] == "Remotion project for scene scene-id"
