"""Physics bridge for chuk-mcp-stage.

Integrates physics simulations (Rapier) with scene objects,
allowing simulation data to drive scene animations.
"""

import json
import logging
from typing import Optional

import httpx

from .config import Config
from .models import Vector3, Quaternion

logger = logging.getLogger(__name__)


class PhysicsBridge:
    """Bridge between physics simulations and scene objects."""

    def __init__(self, physics_server_url: Optional[str] = None):
        """Initialize physics bridge.

        Args:
            physics_server_url: URL of Rapier physics HTTP server.
                               If None, uses public Rapier service (https://rapier.chukai.io)
                               or RAPIER_SERVICE_URL environment variable if set.
        """
        # Default to configured Rapier URL (public service or env var)
        self.physics_server_url = physics_server_url or Config.get_rapier_url()
        self._client: Optional[httpx.AsyncClient] = None
        logger.info(f"PhysicsBridge initialized with Rapier service: {self.physics_server_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        if self.physics_server_url:
            timeout = Config.get_rapier_timeout()
            self._client = httpx.AsyncClient(base_url=self.physics_server_url, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    async def bake_simulation(
        self,
        simulation_id: str,
        body_ids: list[str],
        fps: int = 60,
        duration: Optional[float] = None,
    ) -> dict[str, list[dict]]:
        """Bake physics simulation to keyframe data.

        Args:
            simulation_id: Physics simulation ID (e.g., from chuk-mcp-physics)
            body_ids: List of physics body IDs to bake
            fps: Frames per second for sampling
            duration: Duration in seconds (if None, bakes entire simulation)

        Returns:
            Dict mapping body_id to list of keyframes
            Each keyframe: {"time": float, "position": [x,y,z], "rotation": [x,y,z,w]}

        Raises:
            ValueError: If physics server is not configured
            httpx.HTTPError: If physics server request fails
        """
        if not self._client:
            raise ValueError(
                f"Physics client not initialized. Ensure PhysicsBridge is used as async context manager. "
                f"Rapier service URL: {self.physics_server_url}"
            )

        logger.info(f"Baking simulation {simulation_id} for {len(body_ids)} bodies at {fps} FPS")

        # Request trajectory data from physics server
        # This assumes chuk-mcp-physics has a compatible endpoint
        # For now, we'll use the record_trajectory tool via HTTP API

        baked_data: dict[str, list[dict]] = {}

        for body_id in body_ids:
            # Calculate number of steps from duration and fps
            if duration:
                steps = int(duration * fps)
            else:
                # Get current simulation time/steps
                steps = 600  # Default 10 seconds at 60 FPS

            # Call physics server to get trajectory
            # Rapier service endpoint: POST /simulations/{sim_id}/bodies/{body_id}/trajectory
            try:
                response = await self._client.post(
                    f"/simulations/{simulation_id}/bodies/{body_id}/trajectory",
                    json={
                        "steps": steps,
                        "dt": 1.0 / fps,
                    },
                )
                response.raise_for_status()
                trajectory_data = response.json()

                # Convert to our keyframe format
                keyframes = []
                for frame in trajectory_data.get("frames", []):
                    keyframes.append(
                        {
                            "time": frame["time"],
                            "position": frame["position"],
                            "rotation": frame["orientation"],
                            "velocity": frame.get("velocity", [0, 0, 0]),
                        }
                    )

                baked_data[body_id] = keyframes
                logger.info(f"Baked {len(keyframes)} frames for body {body_id}")

            except httpx.HTTPError as e:
                logger.error(f"Failed to bake trajectory for {body_id}: {e}")
                raise

        return baked_data

    @staticmethod
    def keyframes_to_json(keyframes: list[dict]) -> str:
        """Convert keyframes to JSON string.

        Args:
            keyframes: List of keyframe dicts

        Returns:
            JSON string
        """
        return json.dumps(keyframes, indent=2)

    @staticmethod
    def keyframes_from_json(json_str: str) -> list[dict]:
        """Parse keyframes from JSON string.

        Args:
            json_str: JSON string

        Returns:
            List of keyframe dicts
        """
        return json.loads(json_str)

    @staticmethod
    def interpolate_keyframe(
        keyframes: list[dict], time: float
    ) -> tuple[Vector3, Quaternion, Vector3]:
        """Interpolate position/rotation/velocity at a specific time.

        Args:
            keyframes: List of keyframes
            time: Time to interpolate at

        Returns:
            Tuple of (position, rotation, velocity)
        """
        if not keyframes:
            return Vector3(), Quaternion(), Vector3()

        # Find surrounding keyframes
        before = None
        after = None

        for i, kf in enumerate(keyframes):
            if kf["time"] <= time:
                before = kf
            if kf["time"] >= time:
                after = kf
                break

        # If exactly on a keyframe, return it
        if before and before["time"] == time:
            return (
                Vector3(x=before["position"][0], y=before["position"][1], z=before["position"][2]),
                Quaternion(
                    x=before["rotation"][0],
                    y=before["rotation"][1],
                    z=before["rotation"][2],
                    w=before["rotation"][3],
                ),
                Vector3(x=before["velocity"][0], y=before["velocity"][1], z=before["velocity"][2]),
            )

        # If before first keyframe, return first
        if not before:
            kf = keyframes[0]
            return (
                Vector3(x=kf["position"][0], y=kf["position"][1], z=kf["position"][2]),
                Quaternion(
                    x=kf["rotation"][0],
                    y=kf["rotation"][1],
                    z=kf["rotation"][2],
                    w=kf["rotation"][3],
                ),
                Vector3(x=kf["velocity"][0], y=kf["velocity"][1], z=kf["velocity"][2]),
            )

        # If after last keyframe, return last
        if not after:
            kf = keyframes[-1]
            return (
                Vector3(x=kf["position"][0], y=kf["position"][1], z=kf["position"][2]),
                Quaternion(
                    x=kf["rotation"][0],
                    y=kf["rotation"][1],
                    z=kf["rotation"][2],
                    w=kf["rotation"][3],
                ),
                Vector3(x=kf["velocity"][0], y=kf["velocity"][1], z=kf["velocity"][2]),
            )

        # Linear interpolation between before and after
        t = (time - before["time"]) / (after["time"] - before["time"])

        # Lerp position
        pos = Vector3(
            x=before["position"][0] + t * (after["position"][0] - before["position"][0]),
            y=before["position"][1] + t * (after["position"][1] - before["position"][1]),
            z=before["position"][2] + t * (after["position"][2] - before["position"][2]),
        )

        # For quaternions, should use slerp, but linear works for small timesteps
        rot = Quaternion(
            x=before["rotation"][0] + t * (after["rotation"][0] - before["rotation"][0]),
            y=before["rotation"][1] + t * (after["rotation"][1] - before["rotation"][1]),
            z=before["rotation"][2] + t * (after["rotation"][2] - before["rotation"][2]),
            w=before["rotation"][3] + t * (after["rotation"][3] - before["rotation"][3]),
        )

        # Lerp velocity
        vel = Vector3(
            x=before["velocity"][0] + t * (after["velocity"][0] - before["velocity"][0]),
            y=before["velocity"][1] + t * (after["velocity"][1] - before["velocity"][1]),
            z=before["velocity"][2] + t * (after["velocity"][2] - before["velocity"][2]),
        )

        return pos, rot, vel
