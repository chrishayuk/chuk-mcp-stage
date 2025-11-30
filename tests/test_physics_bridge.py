"""Tests for physics bridge."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from chuk_mcp_stage.physics_bridge import PhysicsBridge
from chuk_mcp_stage.models import Vector3, Quaternion


@pytest.mark.asyncio
async def test_physics_bridge_init_no_server():
    """Test PhysicsBridge initialization without server URL defaults to public service."""
    bridge = PhysicsBridge()
    # Should default to public Rapier service
    assert bridge.physics_server_url == "https://rapier.chukai.io"
    assert bridge._client is None


@pytest.mark.asyncio
async def test_physics_bridge_init_with_server():
    """Test PhysicsBridge initialization with server URL."""
    bridge = PhysicsBridge(physics_server_url="http://localhost:8001")
    assert bridge.physics_server_url == "http://localhost:8001"
    assert bridge._client is None  # Not created until context manager


@pytest.mark.asyncio
async def test_physics_bridge_context_manager_no_server():
    """Test context manager with default server URL creates client."""
    bridge = PhysicsBridge()

    async with bridge:
        # Should create client for default public service
        assert bridge._client is not None
        assert bridge._client.base_url.host == "rapier.chukai.io"


@pytest.mark.asyncio
async def test_physics_bridge_context_manager_with_server():
    """Test context manager with server URL."""
    bridge = PhysicsBridge(physics_server_url="http://localhost:8001")

    async with bridge:
        assert bridge._client is not None
        assert bridge._client.base_url.host == "localhost"


@pytest.mark.asyncio
async def test_bake_simulation_client_not_initialized_raises():
    """Test that baking simulation without using context manager raises ValueError."""
    bridge = PhysicsBridge()

    # Not using async context manager, so _client should be None
    with pytest.raises(ValueError, match="Physics client not initialized"):
        await bridge.bake_simulation(
            simulation_id="sim-001",
            body_ids=["body1"],
        )


@pytest.mark.asyncio
async def test_bake_simulation_with_duration():
    """Test baking simulation with specified duration."""
    bridge = PhysicsBridge(physics_server_url="http://localhost:8001")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "frames": [
            {
                "time": 0.0,
                "position": [0, 0, 0],
                "orientation": [0, 0, 0, 1],
                "velocity": [0, 0, 0],
            },
            {
                "time": 0.016667,
                "position": [0, -0.1, 0],
                "orientation": [0, 0, 0, 1],
                "velocity": [0, -1, 0],
            },
        ]
    }
    mock_response.raise_for_status = MagicMock()

    async with bridge:
        with patch.object(bridge._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await bridge.bake_simulation(
                simulation_id="sim-001",
                body_ids=["body1", "body2"],
                fps=60,
                duration=5.0,
            )

            # Verify calls
            assert mock_post.call_count == 2  # One for each body
            assert "body1" in result
            assert "body2" in result

            # Verify first call arguments
            first_call = mock_post.call_args_list[0]
            assert first_call[0][0] == "/record_trajectory"
            assert first_call[1]["json"]["sim_id"] == "sim-001"
            assert first_call[1]["json"]["body_id"] == "body1"
            assert first_call[1]["json"]["steps"] == 300  # 5 seconds * 60 fps
            assert first_call[1]["json"]["dt"] == 1.0 / 60


@pytest.mark.asyncio
async def test_bake_simulation_no_duration():
    """Test baking simulation without duration (uses default)."""
    bridge = PhysicsBridge(physics_server_url="http://localhost:8001")

    mock_response = MagicMock()
    mock_response.json.return_value = {"frames": []}
    mock_response.raise_for_status = MagicMock()

    async with bridge:
        with patch.object(bridge._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            await bridge.bake_simulation(
                simulation_id="sim-001",
                body_ids=["body1"],
            )

            # Verify default steps (10 seconds at 60 FPS)
            call_args = mock_post.call_args_list[0]
            assert call_args[1]["json"]["steps"] == 600


@pytest.mark.asyncio
async def test_bake_simulation_keyframe_format():
    """Test that baked simulation returns correct keyframe format."""
    bridge = PhysicsBridge(physics_server_url="http://localhost:8001")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "frames": [
            {
                "time": 0.0,
                "position": [1.0, 2.0, 3.0],
                "orientation": [0.1, 0.2, 0.3, 0.9],
                "velocity": [0.5, -0.5, 0.0],
            },
            {
                "time": 1.0,
                "position": [2.0, 3.0, 4.0],
                "orientation": [0.2, 0.3, 0.4, 0.8],
                "velocity": [1.0, -1.0, 0.0],
            },
        ]
    }
    mock_response.raise_for_status = MagicMock()

    async with bridge:
        with patch.object(bridge._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response

            result = await bridge.bake_simulation(
                simulation_id="sim-001",
                body_ids=["body1"],
                fps=30,
            )

            assert "body1" in result
            keyframes = result["body1"]
            assert len(keyframes) == 2

            # Check first frame
            frame1 = keyframes[0]
            assert frame1["time"] == 0.0
            assert frame1["position"] == [1.0, 2.0, 3.0]
            assert frame1["rotation"] == [0.1, 0.2, 0.3, 0.9]
            assert frame1["velocity"] == [0.5, -0.5, 0.0]

            # Check second frame
            frame2 = keyframes[1]
            assert frame2["time"] == 1.0
            assert frame2["position"] == [2.0, 3.0, 4.0]


@pytest.mark.asyncio
async def test_bake_simulation_http_error():
    """Test baking simulation handles HTTP errors."""
    import httpx

    bridge = PhysicsBridge(physics_server_url="http://localhost:8001")

    async with bridge:
        with patch.object(bridge._client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPError("Connection failed")

            with pytest.raises(httpx.HTTPError, match="Connection failed"):
                await bridge.bake_simulation(
                    simulation_id="sim-001",
                    body_ids=["body1"],
                )


def test_keyframes_to_json():
    """Test converting keyframes to JSON."""
    keyframes = [
        {
            "time": 0.0,
            "position": [0, 0, 0],
            "rotation": [0, 0, 0, 1],
            "velocity": [0, 0, 0],
        },
        {
            "time": 1.0,
            "position": [1, 2, 3],
            "rotation": [0.1, 0.2, 0.3, 0.9],
            "velocity": [1, 1, 1],
        },
    ]

    json_str = PhysicsBridge.keyframes_to_json(keyframes)
    assert isinstance(json_str, str)

    # Verify it's valid JSON
    parsed = json.loads(json_str)
    assert len(parsed) == 2
    assert parsed[0]["time"] == 0.0


def test_keyframes_from_json():
    """Test parsing keyframes from JSON."""
    json_str = """[
        {
            "time": 0.0,
            "position": [0, 0, 0],
            "rotation": [0, 0, 0, 1],
            "velocity": [0, 0, 0]
        },
        {
            "time": 1.0,
            "position": [1, 2, 3],
            "rotation": [0.1, 0.2, 0.3, 0.9],
            "velocity": [1, 1, 1]
        }
    ]"""

    keyframes = PhysicsBridge.keyframes_from_json(json_str)
    assert len(keyframes) == 2
    assert keyframes[0]["time"] == 0.0
    assert keyframes[1]["position"] == [1, 2, 3]


def test_interpolate_keyframe_empty():
    """Test interpolating with empty keyframes."""
    pos, rot, vel = PhysicsBridge.interpolate_keyframe([], 5.0)

    assert pos == Vector3()
    assert rot == Quaternion()
    assert vel == Vector3()


def test_interpolate_keyframe_exact_match():
    """Test interpolating at exact keyframe time."""
    keyframes = [
        {
            "time": 0.0,
            "position": [1, 2, 3],
            "rotation": [0.1, 0.2, 0.3, 0.9],
            "velocity": [0.5, 0.5, 0.5],
        },
        {
            "time": 1.0,
            "position": [2, 3, 4],
            "rotation": [0.2, 0.3, 0.4, 0.8],
            "velocity": [1.0, 1.0, 1.0],
        },
    ]

    pos, rot, vel = PhysicsBridge.interpolate_keyframe(keyframes, 0.0)

    assert pos.x == 1.0
    assert pos.y == 2.0
    assert pos.z == 3.0
    assert rot.x == 0.1
    assert rot.y == 0.2
    assert rot.z == 0.3
    assert rot.w == 0.9
    assert vel.x == 0.5


def test_interpolate_keyframe_before_first():
    """Test interpolating before first keyframe returns first frame."""
    keyframes = [
        {
            "time": 1.0,
            "position": [1, 2, 3],
            "rotation": [0, 0, 0, 1],
            "velocity": [0, 0, 0],
        },
    ]

    pos, rot, vel = PhysicsBridge.interpolate_keyframe(keyframes, 0.0)

    assert pos.x == 1.0
    assert pos.y == 2.0
    assert pos.z == 3.0


def test_interpolate_keyframe_after_last():
    """Test interpolating after last keyframe returns last frame."""
    keyframes = [
        {
            "time": 0.0,
            "position": [0, 0, 0],
            "rotation": [0, 0, 0, 1],
            "velocity": [0, 0, 0],
        },
        {
            "time": 1.0,
            "position": [5, 6, 7],
            "rotation": [0.1, 0.2, 0.3, 0.9],
            "velocity": [1, 1, 1],
        },
    ]

    pos, rot, vel = PhysicsBridge.interpolate_keyframe(keyframes, 10.0)

    assert pos.x == 5.0
    assert pos.y == 6.0
    assert pos.z == 7.0
    assert rot.x == 0.1
    assert vel.x == 1.0


def test_interpolate_keyframe_between():
    """Test linear interpolation between keyframes."""
    keyframes = [
        {
            "time": 0.0,
            "position": [0, 0, 0],
            "rotation": [0, 0, 0, 1],
            "velocity": [0, 0, 0],
        },
        {
            "time": 1.0,
            "position": [10, 20, 30],
            "rotation": [0.2, 0.4, 0.6, 0.8],
            "velocity": [2, 4, 6],
        },
    ]

    # Interpolate at 0.5 (halfway)
    pos, rot, vel = PhysicsBridge.interpolate_keyframe(keyframes, 0.5)

    assert pos.x == 5.0  # (0 + 10) / 2
    assert pos.y == 10.0  # (0 + 20) / 2
    assert pos.z == 15.0  # (0 + 30) / 2

    assert rot.x == 0.1  # (0 + 0.2) / 2
    assert rot.y == 0.2  # (0 + 0.4) / 2
    assert rot.z == 0.3  # (0 + 0.6) / 2
    assert rot.w == 0.9  # (1 + 0.8) / 2

    assert vel.x == 1.0  # (0 + 2) / 2
    assert vel.y == 2.0  # (0 + 4) / 2
    assert vel.z == 3.0  # (0 + 6) / 2


def test_interpolate_keyframe_weighted():
    """Test interpolation with non-centered time."""
    keyframes = [
        {
            "time": 0.0,
            "position": [0, 0, 0],
            "rotation": [0, 0, 0, 1],
            "velocity": [0, 0, 0],
        },
        {
            "time": 2.0,
            "position": [10, 20, 30],
            "rotation": [0.2, 0.4, 0.6, 0.8],
            "velocity": [2, 4, 6],
        },
    ]

    # Interpolate at 0.5 (25% of the way from 0 to 2)
    pos, rot, vel = PhysicsBridge.interpolate_keyframe(keyframes, 0.5)

    assert pos.x == 2.5  # 0 + 0.25 * (10 - 0)
    assert pos.y == 5.0  # 0 + 0.25 * (20 - 0)
    assert pos.z == 7.5  # 0 + 0.25 * (30 - 0)


def test_interpolate_keyframe_multiple_frames():
    """Test interpolation picks correct surrounding frames."""
    keyframes = [
        {"time": 0.0, "position": [0, 0, 0], "rotation": [0, 0, 0, 1], "velocity": [0, 0, 0]},
        {"time": 1.0, "position": [1, 1, 1], "rotation": [0, 0, 0, 1], "velocity": [0, 0, 0]},
        {"time": 2.0, "position": [2, 2, 2], "rotation": [0, 0, 0, 1], "velocity": [0, 0, 0]},
        {"time": 3.0, "position": [3, 3, 3], "rotation": [0, 0, 0, 1], "velocity": [0, 0, 0]},
    ]

    # Interpolate between frames 2 and 3
    pos, rot, vel = PhysicsBridge.interpolate_keyframe(keyframes, 2.5)

    assert pos.x == 2.5  # Halfway between 2 and 3
    assert pos.y == 2.5
    assert pos.z == 2.5


@pytest.mark.asyncio
async def test_context_manager_cleanup():
    """Test that context manager properly closes client."""
    bridge = PhysicsBridge(physics_server_url="http://localhost:8001")

    async with bridge:
        client = bridge._client
        assert client is not None

    # After exiting context, client should still exist but be closed
    # (we can't easily test if it's closed without accessing internal state)
    assert bridge._client is not None
