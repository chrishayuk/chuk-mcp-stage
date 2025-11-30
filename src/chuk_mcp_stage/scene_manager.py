"""Scene manager for chuk-mcp-stage.

Manages 3D scenes using chuk-artifacts for storage.
Each scene is a workspace namespace with structured scene data.
"""

import logging
from typing import Optional

from chuk_artifacts import ArtifactStore, NamespaceType, StorageScope

from .models import (
    BakedAnimation,
    Environment,
    Lighting,
    Scene,
    SceneMetadata,
    SceneObject,
    Shot,
)

logger = logging.getLogger(__name__)


class SceneManager:
    """Manages 3D scenes with chuk-artifacts storage."""

    def __init__(self, store: Optional[ArtifactStore] = None):
        """Initialize scene manager.

        Args:
            store: ArtifactStore instance. If None, creates a new one.
        """
        self._store = store or ArtifactStore()
        self._scenes: dict[str, Scene] = {}  # In-memory cache
        self._scene_to_namespace: dict[str, str] = {}  # scene_id -> namespace_id

    async def create_scene(
        self,
        scene_id: str,
        name: Optional[str] = None,
        metadata: Optional[SceneMetadata] = None,
        scope: StorageScope = StorageScope.SESSION,
        user_id: Optional[str] = None,
    ) -> Scene:
        """Create a new scene.

        Args:
            scene_id: Unique scene identifier
            name: Optional scene name
            metadata: Optional scene metadata
            scope: Storage scope (SESSION, USER, or SANDBOX)
            user_id: User ID (required for USER scope)

        Returns:
            Created Scene object
        """
        logger.info(f"Creating scene: {scene_id}")

        # Create workspace namespace for this scene
        namespace = await self._store.create_namespace(
            type=NamespaceType.WORKSPACE,
            name=name or scene_id,
            scope=scope,
            user_id=user_id,
        )

        # Create scene object
        scene = Scene(
            id=scene_id,
            name=name,
            metadata=metadata or SceneMetadata(),
        )

        # Save to storage
        await self._save_scene(scene, namespace.namespace_id)

        # Cache
        self._scenes[scene_id] = scene
        self._scene_to_namespace[scene_id] = namespace.namespace_id

        logger.info(f"Scene created: {scene_id} -> namespace {namespace.namespace_id}")
        return scene

    async def get_scene(self, scene_id: str) -> Scene:
        """Get scene by ID.

        Args:
            scene_id: Scene identifier

        Returns:
            Scene object

        Raises:
            ValueError: If scene not found
        """
        # Check cache first
        if scene_id in self._scenes:
            return self._scenes[scene_id]

        # Check if we have namespace mapping
        if scene_id not in self._scene_to_namespace:
            raise ValueError(f"Scene not found: {scene_id}")

        # Load from storage
        namespace_id = self._scene_to_namespace[scene_id]
        scene = await self._load_scene(namespace_id)
        self._scenes[scene_id] = scene
        return scene

    async def add_object(self, scene_id: str, obj: SceneObject) -> None:
        """Add object to scene.

        Args:
            scene_id: Scene identifier
            obj: SceneObject to add
        """
        scene = await self.get_scene(scene_id)
        scene.objects[obj.id] = obj
        await self._save_scene(scene, self._scene_to_namespace[scene_id])

    async def set_environment(
        self, scene_id: str, environment: Environment, lighting: Optional[Lighting] = None
    ) -> None:
        """Set scene environment and lighting.

        Args:
            scene_id: Scene identifier
            environment: Environment configuration
            lighting: Optional lighting configuration
        """
        scene = await self.get_scene(scene_id)
        scene.environment = environment
        if lighting:
            scene.lighting = lighting
        await self._save_scene(scene, self._scene_to_namespace[scene_id])

    async def add_shot(self, scene_id: str, shot: Shot) -> None:
        """Add shot to scene.

        Args:
            scene_id: Scene identifier
            shot: Shot definition
        """
        scene = await self.get_scene(scene_id)
        scene.shots[shot.id] = shot
        await self._save_scene(scene, self._scene_to_namespace[scene_id])

    async def get_shot(self, scene_id: str, shot_id: str) -> Shot:
        """Get shot from scene.

        Args:
            scene_id: Scene identifier
            shot_id: Shot identifier

        Returns:
            Shot object

        Raises:
            ValueError: If shot not found
        """
        scene = await self.get_scene(scene_id)
        if shot_id not in scene.shots:
            raise ValueError(f"Shot not found: {shot_id}")
        return scene.shots[shot_id]

    async def bind_physics(self, scene_id: str, object_id: str, physics_body_id: str) -> None:
        """Bind scene object to physics body.

        Args:
            scene_id: Scene identifier
            object_id: Object identifier
            physics_body_id: Physics body identifier (e.g., "rapier://sim-001/body-bob")

        Raises:
            ValueError: If object not found
        """
        scene = await self.get_scene(scene_id)
        if object_id not in scene.objects:
            raise ValueError(f"Object not found: {object_id}")

        scene.objects[object_id].physics_binding = physics_body_id
        await self._save_scene(scene, self._scene_to_namespace[scene_id])

    async def add_baked_animation(
        self, scene_id: str, object_id: str, animation: BakedAnimation
    ) -> None:
        """Add baked animation data for an object.

        Args:
            scene_id: Scene identifier
            object_id: Object identifier
            animation: BakedAnimation data

        Raises:
            ValueError: If object not found
        """
        scene = await self.get_scene(scene_id)
        if object_id not in scene.objects:
            raise ValueError(f"Object not found: {object_id}")

        scene.baked_animations[object_id] = animation
        await self._save_scene(scene, self._scene_to_namespace[scene_id])

    async def get_scene_vfs(self, scene_id: str):
        """Get VFS access for scene workspace.

        Args:
            scene_id: Scene identifier

        Returns:
            AsyncVirtualFileSystem for the scene
        """
        if scene_id not in self._scene_to_namespace:
            raise ValueError(f"Scene not found: {scene_id}")

        namespace_id = self._scene_to_namespace[scene_id]
        return self._store.get_namespace_vfs(namespace_id)

    # ============================================================================
    # Private Storage Methods
    # ============================================================================

    async def _save_scene(self, scene: Scene, namespace_id: str) -> None:
        """Save scene to storage.

        Args:
            scene: Scene to save
            namespace_id: Namespace ID for storage
        """
        # Convert scene to JSON
        scene_json = scene.model_dump_json(indent=2)

        # Write to namespace
        await self._store.write_namespace(
            namespace_id, path="/scene.json", data=scene_json.encode("utf-8")
        )

        logger.debug(f"Saved scene {scene.id} to namespace {namespace_id}")

    async def _load_scene(self, namespace_id: str) -> Scene:
        """Load scene from storage.

        Args:
            namespace_id: Namespace ID to load from

        Returns:
            Loaded Scene object
        """
        # Read from namespace
        scene_data = await self._store.read_namespace(namespace_id, path="/scene.json")
        scene_json = scene_data.decode("utf-8")

        # Parse JSON to Scene
        scene = Scene.model_validate_json(scene_json)

        logger.debug(f"Loaded scene {scene.id} from namespace {namespace_id}")
        return scene

    async def close(self) -> None:
        """Close the scene manager and underlying store."""
        if self._store:
            await self._store.close()
