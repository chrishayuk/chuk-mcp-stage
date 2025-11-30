"""Tests for chuk-mcp-stage server tools."""

import sys
from unittest.mock import patch, MagicMock
import pytest
from chuk_mcp_stage.server import (
    stage_create_scene,
    stage_add_object,
    stage_set_environment,
    stage_add_shot,
    stage_get_shot,
    stage_bind_physics,
    stage_export_scene,
    stage_get_scene,
    stage_bake_simulation,
)


@pytest.mark.asyncio
async def test_stage_create_scene():
    """Test scene creation."""
    result = await stage_create_scene(
        name="Test Scene",
        author="Test Author",
        description="Test description",
    )

    assert result.scene_id is not None
    assert "scene" in result.scene_id.lower()


@pytest.mark.asyncio
async def test_stage_create_scene_minimal():
    """Test scene creation with minimal params."""
    result = await stage_create_scene()
    assert result.scene_id is not None


@pytest.mark.asyncio
async def test_stage_add_object_box():
    """Test adding a box object."""
    scene_result = await stage_create_scene(name="Object Test")
    scene_id = scene_result.scene_id

    result = await stage_add_object(
        scene_id=scene_id,
        object_id="test-box",
        object_type="box",
        position_y=5.0,
        size_x=2.0,
        size_y=2.0,
        size_z=2.0,
    )

    assert result.object_id == "test-box"
    assert result.scene_id == scene_id


@pytest.mark.asyncio
async def test_stage_add_object_sphere():
    """Test adding a sphere object."""
    scene_result = await stage_create_scene()
    scene_id = scene_result.scene_id

    result = await stage_add_object(
        scene_id=scene_id,
        object_id="test-sphere",
        object_type="sphere",
        radius=1.5,
        material_preset="metal-dark",
    )

    assert result.object_id == "test-sphere"


@pytest.mark.asyncio
async def test_stage_add_object_with_transform():
    """Test adding object with full transform."""
    scene_result = await stage_create_scene()
    scene_id = scene_result.scene_id

    result = await stage_add_object(
        scene_id=scene_id,
        object_id="transformed",
        object_type="box",
        position_x=1.0,
        position_y=2.0,
        position_z=3.0,
        rotation_x=0.0,
        rotation_y=0.707,
        rotation_z=0.0,
        rotation_w=0.707,
        scale_x=2.0,
        scale_y=2.0,
        scale_z=2.0,
    )

    assert result.object_id == "transformed"


@pytest.mark.asyncio
async def test_stage_add_object_cylinder():
    """Test adding a cylinder."""
    scene_result = await stage_create_scene()
    result = await stage_add_object(
        scene_id=scene_result.scene_id,
        object_id="cyl",
        object_type="cylinder",
        radius=0.5,
        height=3.0,
    )
    assert result.object_id == "cyl"


@pytest.mark.asyncio
async def test_stage_add_object_plane():
    """Test adding a plane."""
    scene_result = await stage_create_scene()
    result = await stage_add_object(
        scene_id=scene_result.scene_id,
        object_id="ground",
        object_type="plane",
        size_x=20.0,
        size_y=20.0,
    )
    assert result.object_id == "ground"


@pytest.mark.asyncio
async def test_stage_set_environment():
    """Test setting environment."""
    scene_result = await stage_create_scene()
    scene_id = scene_result.scene_id

    result = await stage_set_environment(
        scene_id=scene_id,
        environment_type="gradient",
        lighting_preset="sunset",
        intensity=0.7,
    )

    assert result.scene_id == scene_id


@pytest.mark.asyncio
async def test_stage_set_environment_defaults():
    """Test setting environment with defaults."""
    scene_result = await stage_create_scene()
    result = await stage_set_environment(scene_id=scene_result.scene_id)
    assert result.scene_id == scene_result.scene_id


@pytest.mark.asyncio
async def test_stage_add_shot_orbit():
    """Test adding orbit shot."""
    scene_result = await stage_create_scene()
    scene_id = scene_result.scene_id

    # Add target object
    await stage_add_object(
        scene_id=scene_id,
        object_id="target",
        object_type="sphere",
    )

    result = await stage_add_shot(
        scene_id=scene_id,
        shot_id="orbit-1",
        camera_mode="orbit",
        start_time=0.0,
        end_time=5.0,
        focus_object="target",
        orbit_radius=10.0,
        orbit_elevation=30.0,
        orbit_speed=0.1,
    )

    assert result.shot_id == "orbit-1"
    assert result.duration == 5.0


@pytest.mark.asyncio
async def test_stage_add_shot_static():
    """Test adding static shot."""
    scene_result = await stage_create_scene()

    result = await stage_add_shot(
        scene_id=scene_result.scene_id,
        shot_id="static-1",
        camera_mode="static",
        start_time=0.0,
        end_time=3.0,
        static_position_x=5.0,
        static_position_y=5.0,
        static_position_z=5.0,
        look_at_x=0.0,
        look_at_y=0.0,
        look_at_z=0.0,
    )

    assert result.shot_id == "static-1"
    assert result.duration == 3.0


@pytest.mark.asyncio
async def test_stage_get_shot():
    """Test retrieving a shot."""
    scene_result = await stage_create_scene()
    scene_id = scene_result.scene_id

    await stage_add_shot(
        scene_id=scene_id,
        shot_id="get-test",
        camera_mode="static",
        start_time=0.0,
        end_time=2.0,
    )

    result = await stage_get_shot(scene_id=scene_id, shot_id="get-test")
    assert result.shot.id == "get-test"
    assert result.scene_id == scene_id


@pytest.mark.asyncio
async def test_stage_bind_physics():
    """Test binding physics."""
    scene_result = await stage_create_scene()
    scene_id = scene_result.scene_id

    await stage_add_object(
        scene_id=scene_id,
        object_id="phys-obj",
        object_type="sphere",
    )

    result = await stage_bind_physics(
        scene_id=scene_id,
        object_id="phys-obj",
        physics_body_id="rapier://sim-001/body-1",
    )

    assert result.object_id == "phys-obj"
    assert result.physics_body_id == "rapier://sim-001/body-1"


@pytest.mark.asyncio
async def test_stage_export_json():
    """Test JSON export."""
    scene_result = await stage_create_scene()
    scene_id = scene_result.scene_id

    await stage_add_object(
        scene_id=scene_id,
        object_id="obj1",
        object_type="box",
    )

    result = await stage_export_scene(
        scene_id=scene_id,
        format="json",
    )

    assert result.scene_id == scene_id
    assert result.format.value == "json"
    assert result.output_path is not None


@pytest.mark.asyncio
async def test_stage_export_r3f():
    """Test R3F export."""
    scene_result = await stage_create_scene()
    result = await stage_export_scene(
        scene_id=scene_result.scene_id,
        format="r3f-component",
    )
    assert result.format.value == "r3f-component"


@pytest.mark.asyncio
async def test_stage_export_remotion():
    """Test Remotion export."""
    scene_result = await stage_create_scene()
    result = await stage_export_scene(
        scene_id=scene_result.scene_id,
        format="remotion-project",
    )
    assert result.format.value == "remotion-project"


@pytest.mark.asyncio
async def test_stage_export_gltf():
    """Test glTF export."""
    scene_result = await stage_create_scene()
    result = await stage_export_scene(
        scene_id=scene_result.scene_id,
        format="gltf",
    )
    assert result.format.value == "gltf"


@pytest.mark.asyncio
async def test_stage_get_scene():
    """Test getting complete scene."""
    scene_result = await stage_create_scene(
        name="Get Test",
        author="Author",
        description="Desc",
    )
    scene_id = scene_result.scene_id

    await stage_add_object(
        scene_id=scene_id,
        object_id="obj1",
        object_type="box",
    )

    result = await stage_get_scene(scene_id=scene_id)
    assert result.scene.id == scene_id
    assert result.scene.name == "Get Test"
    assert "obj1" in result.scene.objects


@pytest.mark.asyncio
async def test_complete_workflow():
    """Test complete end-to-end workflow."""
    # Create scene
    scene = await stage_create_scene(name="Workflow Test")
    sid = scene.scene_id

    # Set environment
    await stage_set_environment(
        scene_id=sid,
        environment_type="gradient",
        lighting_preset="three-point",
    )

    # Add objects
    await stage_add_object(sid, "ground", "plane", size_x=20.0, size_y=20.0)
    await stage_add_object(sid, "ball", "sphere", position_y=5.0, radius=1.0)

    # Add shot
    shot = await stage_add_shot(
        scene_id=sid,
        shot_id="main",
        camera_mode="orbit",
        start_time=0.0,
        end_time=10.0,
        focus_object="ball",
        orbit_radius=8.0,
        orbit_elevation=20.0,
        orbit_speed=0.05,
    )
    assert shot.duration == 10.0

    # Bind physics
    await stage_bind_physics(sid, "ball", "rapier://sim/ball-body")

    # Export
    export = await stage_export_scene(sid, format="r3f-component")
    assert export.format.value == "r3f-component"

    # Get final scene
    final = await stage_get_scene(sid)
    assert len(final.scene.objects) == 2
    assert len(final.scene.shots) == 1
    assert final.scene.objects["ball"].physics_binding == "rapier://sim/ball-body"


@pytest.mark.asyncio
async def test_stage_bake_simulation_no_bound_objects():
    """Test bake simulation raises error when no objects are bound."""
    scene_result = await stage_create_scene()
    scene_id = scene_result.scene_id

    # Add object but don't bind it
    await stage_add_object(
        scene_id=scene_id,
        object_id="obj1",
        object_type="box",
    )

    # Should raise error because no objects are bound to simulation
    with pytest.raises(ValueError, match="No objects bound to simulation"):
        await stage_bake_simulation(
            scene_id=scene_id,
            simulation_id="sim-001",
        )


@pytest.mark.asyncio
async def test_stage_bake_simulation_with_mock():
    """Test bake simulation with mocked physics bridge."""
    scene_result = await stage_create_scene()
    scene_id = scene_result.scene_id

    # Add and bind object
    await stage_add_object(
        scene_id=scene_id,
        object_id="obj1",
        object_type="box",
    )
    await stage_bind_physics(
        scene_id=scene_id,
        object_id="obj1",
        physics_body_id="rapier://sim-001/body-1",
    )

    # Mock PhysicsBridge to avoid external dependency
    mock_keyframes = [
        {"frame": 0, "position": [0, 0, 0], "rotation": [0, 0, 0, 1]},
        {"frame": 1, "position": [0, 1, 0], "rotation": [0, 0, 0, 1]},
    ]

    # Create async mock
    async def async_bake(*args, **kwargs):
        return {"1": mock_keyframes}

    import json

    with patch("chuk_mcp_stage.server.PhysicsBridge") as mock_bridge_class:
        mock_bridge = MagicMock()

        # Fix async context manager
        async def async_enter(*args):
            return mock_bridge

        async def async_exit(*args):
            return None

        mock_bridge.__aenter__ = async_enter
        mock_bridge.__aexit__ = async_exit
        mock_bridge.bake_simulation = async_bake

        # Mock the static method keyframes_to_json
        mock_bridge_class.keyframes_to_json = MagicMock(return_value=json.dumps(mock_keyframes))
        mock_bridge_class.return_value = mock_bridge

        result = await stage_bake_simulation(
            scene_id=scene_id,
            simulation_id="sim-001",
            fps=60,
            duration=10.0,
        )

        assert result.scene_id == scene_id
        assert len(result.baked_objects) == 1
        assert "obj1" in result.baked_objects
        assert result.total_frames == 2
        assert result.fps == 60


def test_main_default_stdio():
    """Test main function defaults to stdio mode."""
    from chuk_mcp_stage.server import main

    with patch("chuk_mcp_stage.server.run") as mock_run:
        with patch.object(sys, "argv", ["chuk-mcp-stage"]):
            main()
            mock_run.assert_called_once_with(transport="stdio")


def test_main_http_mode():
    """Test main function with http mode."""
    from chuk_mcp_stage.server import main

    with patch("chuk_mcp_stage.server.run") as mock_run:
        with patch.object(sys, "argv", ["chuk-mcp-stage", "http"]):
            main()
            mock_run.assert_called_once_with(transport="http", host="0.0.0.0", port=8000)


def test_main_http_mode_with_flag():
    """Test main function with --http flag."""
    from chuk_mcp_stage.server import main

    with patch("chuk_mcp_stage.server.run") as mock_run:
        with patch.object(sys, "argv", ["chuk-mcp-stage", "--http"]):
            main()
            mock_run.assert_called_once_with(transport="http", host="0.0.0.0", port=8000)


def test_main_streamable_mode():
    """Test main function with streamable mode."""
    from chuk_mcp_stage.server import main

    with patch("chuk_mcp_stage.server.run") as mock_run:
        with patch.object(sys, "argv", ["chuk-mcp-stage", "streamable"]):
            main()
            mock_run.assert_called_once_with(transport="streamable")


def test_main_sse_mode():
    """Test main function with sse alias."""
    from chuk_mcp_stage.server import main

    with patch("chuk_mcp_stage.server.run") as mock_run:
        with patch.object(sys, "argv", ["chuk-mcp-stage", "sse"]):
            main()
            mock_run.assert_called_once_with(transport="streamable")


def test_main_streamable_flag():
    """Test main function with --streamable flag."""
    from chuk_mcp_stage.server import main

    with patch("chuk_mcp_stage.server.run") as mock_run:
        with patch.object(sys, "argv", ["chuk-mcp-stage", "--streamable"]):
            main()
            mock_run.assert_called_once_with(transport="streamable")
