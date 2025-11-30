"""Tests for SceneManager."""

import pytest

from chuk_mcp_stage.models import (
    BakedAnimation,
    CameraPath,
    CameraPathMode,
    EasingFunction,
    Environment,
    EnvironmentType,
    Lighting,
    LightingPreset,
    Material,
    MaterialPreset,
    ObjectType,
    SceneMetadata,
    SceneObject,
    Shot,
    Transform,
    Vector3,
)
from chuk_mcp_stage.scene_manager import SceneManager
from chuk_artifacts import StorageScope


@pytest.mark.asyncio
async def test_create_scene():
    """Test scene creation."""
    manager = SceneManager()

    scene = await manager.create_scene(scene_id="test-scene", name="Test Scene")

    assert scene.id == "test-scene"
    assert scene.name == "Test Scene"
    assert len(scene.objects) == 0
    assert len(scene.shots) == 0


@pytest.mark.asyncio
async def test_add_object():
    """Test adding objects to scene."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="test-scene")

    # Create object
    obj = SceneObject(
        id="ball",
        type=ObjectType.SPHERE,
        transform=Transform(position=Vector3(x=0, y=5, z=0)),
        radius=1.0,
    )

    # Add to scene
    await manager.add_object(scene.id, obj)

    # Verify
    scene = await manager.get_scene(scene.id)
    assert "ball" in scene.objects
    assert scene.objects["ball"].type == ObjectType.SPHERE
    assert scene.objects["ball"].radius == 1.0


@pytest.mark.asyncio
async def test_add_shot():
    """Test adding camera shots."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="test-scene")

    # Create shot
    shot = Shot(
        id="orbit-shot",
        camera_path=CameraPath(
            mode=CameraPathMode.ORBIT, focus="ball", radius=8.0, elevation=30.0, speed=0.1
        ),
        start_time=0.0,
        end_time=10.0,
        easing=EasingFunction.EASE_IN_OUT_CUBIC,
    )

    # Add to scene
    await manager.add_shot(scene.id, shot)

    # Verify
    scene = await manager.get_scene(scene.id)
    assert "orbit-shot" in scene.shots
    assert scene.shots["orbit-shot"].camera_path.mode == CameraPathMode.ORBIT
    assert scene.shots["orbit-shot"].start_time == 0.0
    assert scene.shots["orbit-shot"].end_time == 10.0


@pytest.mark.asyncio
async def test_bind_physics():
    """Test binding physics to objects."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="test-scene")

    # Add object
    obj = SceneObject(id="ball", type=ObjectType.SPHERE, radius=1.0)
    await manager.add_object(scene.id, obj)

    # Bind physics
    physics_id = "rapier://sim-abc123/body-ball"
    await manager.bind_physics(scene.id, "ball", physics_id)

    # Verify
    scene = await manager.get_scene(scene.id)
    assert scene.objects["ball"].physics_binding == physics_id


@pytest.mark.asyncio
async def test_scene_persistence():
    """Test scene save/load."""
    manager = SceneManager()

    # Create scene with objects
    scene = await manager.create_scene(scene_id="test-scene", name="Persistence Test")

    obj = SceneObject(
        id="box",
        type=ObjectType.BOX,
        transform=Transform(position=Vector3(x=1, y=2, z=3)),
        size=Vector3(x=2, y=2, z=2),
        material=Material(preset=MaterialPreset.METAL_DARK),
    )
    await manager.add_object(scene.id, obj)

    # Clear cache and reload
    manager._scenes.clear()

    # Get scene again (should load from storage)
    loaded_scene = await manager.get_scene("test-scene")

    assert loaded_scene.id == "test-scene"
    assert loaded_scene.name == "Persistence Test"
    assert "box" in loaded_scene.objects
    assert loaded_scene.objects["box"].type == ObjectType.BOX
    assert loaded_scene.objects["box"].transform.position.x == 1
    assert loaded_scene.objects["box"].material.preset == MaterialPreset.METAL_DARK


@pytest.mark.asyncio
async def test_create_scene_with_metadata():
    """Test creating scene with full metadata."""
    manager = SceneManager()

    metadata = SceneMetadata(
        author="Test Author",
        description="Test Description",
        tags=["test", "demo"],
    )

    scene = await manager.create_scene(
        scene_id="meta-scene",
        name="Metadata Test",
        metadata=metadata,
        scope=StorageScope.SESSION,
    )

    assert scene.metadata.author == "Test Author"
    assert scene.metadata.description == "Test Description"
    assert "test" in scene.metadata.tags


@pytest.mark.asyncio
async def test_get_scene_not_found():
    """Test getting non-existent scene raises error."""
    manager = SceneManager()

    with pytest.raises(ValueError, match="Scene not found"):
        await manager.get_scene("nonexistent-scene")


@pytest.mark.asyncio
async def test_set_environment():
    """Test setting scene environment and lighting."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="env-scene")

    env = Environment(
        type=EnvironmentType.GRADIENT,
        intensity=0.8,
    )
    lighting = Lighting(
        preset=LightingPreset.SUNSET,
        ambient_intensity=0.6,
    )

    await manager.set_environment(scene.id, env, lighting)

    # Verify
    scene = await manager.get_scene(scene.id)
    assert scene.environment.type == EnvironmentType.GRADIENT
    assert scene.environment.intensity == 0.8
    assert scene.lighting.preset == LightingPreset.SUNSET
    assert scene.lighting.ambient_intensity == 0.6


@pytest.mark.asyncio
async def test_set_environment_no_lighting():
    """Test setting environment without lighting."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="env-scene")

    env = Environment(type=EnvironmentType.HDRI)

    await manager.set_environment(scene.id, env)

    # Verify environment changed but lighting is default
    scene = await manager.get_scene(scene.id)
    assert scene.environment.type == EnvironmentType.HDRI


@pytest.mark.asyncio
async def test_get_shot():
    """Test getting specific shot from scene."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="shot-scene")

    shot = Shot(
        id="test-shot",
        camera_path=CameraPath(mode=CameraPathMode.STATIC),
        start_time=0.0,
        end_time=5.0,
    )

    await manager.add_shot(scene.id, shot)

    # Get the shot
    retrieved_shot = await manager.get_shot(scene.id, "test-shot")

    assert retrieved_shot.id == "test-shot"
    assert retrieved_shot.start_time == 0.0
    assert retrieved_shot.end_time == 5.0


@pytest.mark.asyncio
async def test_get_shot_not_found():
    """Test getting non-existent shot raises error."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="shot-scene")

    with pytest.raises(ValueError, match="Shot not found"):
        await manager.get_shot(scene.id, "nonexistent-shot")


@pytest.mark.asyncio
async def test_bind_physics_object_not_found():
    """Test binding physics to non-existent object raises error."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="physics-scene")

    with pytest.raises(ValueError, match="Object not found"):
        await manager.bind_physics(scene.id, "nonexistent-obj", "rapier://sim/body")


@pytest.mark.asyncio
async def test_add_baked_animation():
    """Test adding baked animation to object."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="anim-scene")

    # Add object
    obj = SceneObject(id="animated-ball", type=ObjectType.SPHERE, radius=1.0)
    await manager.add_object(scene.id, obj)

    # Add baked animation
    animation = BakedAnimation(
        object_id="animated-ball",
        source="physics-sim-001",
        fps=60,
        frames=600,
        data_path="/animations/ball.json",
    )

    await manager.add_baked_animation(scene.id, "animated-ball", animation)

    # Verify
    scene = await manager.get_scene(scene.id)
    assert "animated-ball" in scene.baked_animations
    assert scene.baked_animations["animated-ball"].fps == 60
    assert scene.baked_animations["animated-ball"].frames == 600
    assert scene.baked_animations["animated-ball"].source == "physics-sim-001"


@pytest.mark.asyncio
async def test_add_baked_animation_object_not_found():
    """Test adding animation to non-existent object raises error."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="anim-scene")

    animation = BakedAnimation(
        object_id="nonexistent",
        source="sim",
        fps=60,
        frames=100,
        data_path="/path",
    )

    with pytest.raises(ValueError, match="Object not found"):
        await manager.add_baked_animation(scene.id, "nonexistent", animation)


@pytest.mark.asyncio
async def test_get_scene_vfs():
    """Test getting VFS for scene workspace."""
    manager = SceneManager()
    scene = await manager.create_scene(scene_id="vfs-scene")

    vfs = await manager.get_scene_vfs(scene.id)

    # Test writing/reading via VFS
    await vfs.write_text("/test.txt", "Hello VFS")
    content = await vfs.read_text("/test.txt")

    assert content == "Hello VFS"


@pytest.mark.asyncio
async def test_get_scene_vfs_not_found():
    """Test getting VFS for non-existent scene raises error."""
    manager = SceneManager()

    with pytest.raises(ValueError, match="Scene not found"):
        await manager.get_scene_vfs("nonexistent-scene")


@pytest.mark.asyncio
async def test_close():
    """Test closing scene manager."""
    manager = SceneManager()
    await manager.create_scene(scene_id="close-test")

    await manager.close()

    # Manager should be closed (store closed)
