"""Export modules for chuk-mcp-stage.

Convert scenes to React Three Fiber (R3F) and Remotion formats.
"""

import json
import logging
from typing import Optional

from .models import (
    ExportFormat,
    ObjectType,
    Scene,
)

logger = logging.getLogger(__name__)


class SceneExporter:
    """Exports scenes to various formats."""

    @staticmethod
    async def _ensure_directory(vfs, path: str) -> None:
        """Ensure directory exists by creating all parent directories.

        Args:
            vfs: VFS instance
            path: Directory path to create
        """
        if path == "/" or not path:
            return

        parts = [p for p in path.split("/") if p]
        current = ""
        for part in parts:
            current = f"{current}/{part}"
            await vfs.mkdir(current)

    @staticmethod
    async def export_scene(
        scene: Scene,
        format: ExportFormat,
        vfs,
        output_path: Optional[str] = None,
    ) -> dict[str, str]:
        """Export scene to specified format.

        Args:
            scene: Scene to export
            format: Export format
            vfs: VFS instance for writing files
            output_path: Optional output path override

        Returns:
            Dict of generated file paths
        """
        if format == ExportFormat.JSON:
            return await SceneExporter._export_json(scene, vfs, output_path)
        elif format == ExportFormat.R3F_COMPONENT:
            return await SceneExporter._export_r3f(scene, vfs, output_path)
        elif format == ExportFormat.REMOTION_PROJECT:
            return await SceneExporter._export_remotion(scene, vfs, output_path)
        elif format == ExportFormat.GLTF:
            return await SceneExporter._export_gltf(scene, vfs, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    @staticmethod
    async def _export_json(scene: Scene, vfs, output_path: Optional[str]) -> dict[str, str]:
        """Export scene as JSON."""
        path = output_path or "/export/scene.json"

        # Ensure parent directory exists
        parent_dir = "/".join(path.rsplit("/", 1)[:-1]) or "/"
        await SceneExporter._ensure_directory(vfs, parent_dir)

        scene_json = scene.model_dump_json(indent=2)
        await vfs.write_text(path, scene_json)
        logger.info(f"Exported scene {scene.id} to JSON at {path}")
        return {"scene": path}

    @staticmethod
    async def _export_r3f(scene: Scene, vfs, output_path: Optional[str]) -> dict[str, str]:
        """Export scene as React Three Fiber component."""
        base_path = output_path or "/export/r3f"
        await SceneExporter._ensure_directory(vfs, base_path)

        # Generate main scene component
        component_code = SceneExporter._generate_r3f_component(scene)
        component_path = f"{base_path}/Scene.tsx"
        await vfs.write_text(component_path, component_code)

        # Generate camera component if there are shots
        if scene.shots:
            camera_code = SceneExporter._generate_camera_component(scene)
            camera_path = f"{base_path}/Camera.tsx"
            await vfs.write_text(camera_path, camera_code)
        else:
            camera_path = None

        # Generate animation data if there are baked animations
        if scene.baked_animations:
            animations_code = SceneExporter._generate_animations_data(scene)
            animations_path = f"{base_path}/animations.json"
            await vfs.write_text(animations_path, animations_code)
        else:
            animations_path = None

        logger.info(f"Exported scene {scene.id} to R3F at {base_path}")

        result = {"component": component_path}
        if camera_path:
            result["camera"] = camera_path
        if animations_path:
            result["animations"] = animations_path

        return result

    @staticmethod
    def _generate_r3f_component(scene: Scene) -> str:
        """Generate R3F scene component code."""
        objects_jsx = []

        for obj_id, obj in scene.objects.items():
            # Generate mesh based on type
            if obj.type == ObjectType.BOX:
                if obj.size:
                    geometry = f"<boxGeometry args={[{obj.size.x}, {obj.size.y}, {obj.size.z}]} />"
                else:
                    geometry = "<boxGeometry args={[1, 1, 1]} />"
            elif obj.type == ObjectType.SPHERE:
                radius = obj.radius or 1.0
                geometry = f"<sphereGeometry args={[{radius}, 32, 32]} />"
            elif obj.type == ObjectType.CYLINDER:
                radius = obj.radius or 1.0
                height = obj.height or 2.0
                geometry = f"<cylinderGeometry args={[{radius}, {radius}, {height}, 32]} />"
            elif obj.type == ObjectType.PLANE:
                if obj.size:
                    geometry = f"<planeGeometry args={[{obj.size.x}, {obj.size.y}]} />"
                else:
                    geometry = "<planeGeometry args={[10, 10]} />"
            else:
                geometry = "<boxGeometry />"

            # Material
            mat = obj.material
            if mat.color:
                color_hex = f"#{int(mat.color.r * 255):02x}{int(mat.color.g * 255):02x}{int(mat.color.b * 255):02x}"
            else:
                color_hex = "#ffffff"

            material = f"""<meshStandardMaterial
        color="{color_hex}"
        roughness={{{mat.roughness}}}
        metalness={{{mat.metalness}}}
        transparent={{{str(mat.opacity < 1.0).lower()}}}
        opacity={{{mat.opacity}}}
      />"""

            # Position and rotation
            pos = obj.transform.position
            rot = obj.transform.rotation

            mesh = f"""
  <mesh
    name="{obj_id}"
    position={[{pos.x}, {pos.y}, {pos.z}]}
    quaternion={[{rot.x}, {rot.y}, {rot.z}, {rot.w}]}
  >
    {geometry}
    {material}
  </mesh>"""
            objects_jsx.append(mesh)

        # Lighting
        lighting_jsx = """
  <ambientLight intensity={0.5} />
  <directionalLight position={[10, 10, 5]} intensity={1} />"""

        component = f"""import React from 'react';
import {{ Canvas }} from '@react-three/fiber';
import {{ OrbitControls }} from '@react-three/drei';

export function Scene() {{
  return (
    <Canvas camera={{ position: [5, 5, 5], fov: 50 }}>
      {lighting_jsx}
      {chr(10).join(objects_jsx)}
      <OrbitControls />
    </Canvas>
  );
}}
"""
        return component

    @staticmethod
    def _generate_camera_component(scene: Scene) -> str:
        """Generate camera controller component for shots."""
        # For now, generate a simple camera that can be keyframed
        camera_code = """import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { PerspectiveCamera } from '@react-three/drei';

export function AnimatedCamera({ shot, currentTime }) {
  const cameraRef = useRef();

  useFrame(() => {
    if (!cameraRef.current || !shot) return;

    // Interpolate camera position based on shot definition
    // This is a placeholder - real implementation would use shot.camera_path
    const t = (currentTime - shot.start_time) / (shot.end_time - shot.start_time);

    if (t >= 0 && t <= 1) {
      // Update camera based on camera path mode
      // TODO: Implement actual camera path interpolation
    }
  });

  return <PerspectiveCamera ref={cameraRef} makeDefault />;
}
"""
        return camera_code

    @staticmethod
    def _generate_animations_data(scene: Scene) -> str:
        """Generate animation keyframe data as JSON."""
        animations = {}

        for obj_id, baked_anim in scene.baked_animations.items():
            animations[obj_id] = {
                "source": baked_anim.source,
                "fps": baked_anim.fps,
                "frames": baked_anim.frames,
                "data_path": baked_anim.data_path,
            }

        return json.dumps(animations, indent=2)

    @staticmethod
    async def _export_remotion(scene: Scene, vfs, output_path: Optional[str]) -> dict[str, str]:
        """Export scene as Remotion project."""
        base_path = output_path or "/export/remotion"
        await SceneExporter._ensure_directory(vfs, base_path)

        # Generate Remotion composition
        composition_code = SceneExporter._generate_remotion_composition(scene)
        composition_path = f"{base_path}/Composition.tsx"
        await vfs.write_text(composition_path, composition_code)

        # Generate Root component
        root_code = SceneExporter._generate_remotion_root(scene)
        root_path = f"{base_path}/Root.tsx"
        await vfs.write_text(root_path, root_code)

        # Generate package.json
        package_json = SceneExporter._generate_package_json(scene)
        package_path = f"{base_path}/package.json"
        await vfs.write_text(package_path, package_json)

        logger.info(f"Exported scene {scene.id} to Remotion at {base_path}")

        return {
            "composition": composition_path,
            "root": root_path,
            "package": package_path,
        }

    @staticmethod
    def _generate_remotion_composition(scene: Scene) -> str:
        """Generate Remotion composition code."""
        # Note: Duration is calculated in _generate_remotion_root
        composition = """import { ThreeCanvas } from '@remotion/three';
import { AbsoluteFill } from 'remotion';

export const MyComposition = () => {
  return (
    <AbsoluteFill>
      <ThreeCanvas>
        {/* Scene objects will be rendered here */}
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} />

        {/* Objects */}
        {/* Camera */}
      </ThreeCanvas>
    </AbsoluteFill>
  );
};
"""
        return composition

    @staticmethod
    def _generate_remotion_root(scene: Scene) -> str:
        """Generate Remotion root configuration."""
        fps = 30
        duration = 300  # 10 seconds default

        if scene.shots:
            max_end = max(shot.end_time for shot in scene.shots.values())
            duration = int(max_end * fps)

        root = f"""import {{ Composition }} from 'remotion';
import {{ MyComposition }} from './Composition';

export const RemotionRoot = () => {{
  return (
    <>
      <Composition
        id="{scene.id}"
        component={{MyComposition}}
        durationInFrames={{{duration}}}
        fps={{{fps}}}
        width={{1920}}
        height={{1080}}
      />
    </>
  );
}};
"""
        return root

    @staticmethod
    def _generate_package_json(scene: Scene) -> str:
        """Generate package.json for Remotion project."""
        package = {
            "name": f"scene-{scene.id}",
            "version": "1.0.0",
            "description": f"Remotion project for scene {scene.name or scene.id}",
            "scripts": {
                "start": "remotion preview",
                "build": "remotion render MyComposition out.mp4",
            },
            "dependencies": {
                "react": "^18.2.0",
                "remotion": "^4.0.0",
                "@remotion/three": "^4.0.0",
                "@react-three/fiber": "^8.0.0",
                "@react-three/drei": "^9.0.0",
                "three": "^0.160.0",
            },
        }
        return json.dumps(package, indent=2)

    @staticmethod
    async def _export_gltf(scene: Scene, vfs, output_path: Optional[str]) -> dict[str, str]:
        """Export scene as glTF file."""
        path = output_path or "/export/scene.gltf"

        # Ensure parent directory exists
        parent_dir = "/".join(path.rsplit("/", 1)[:-1]) or "/"
        await SceneExporter._ensure_directory(vfs, parent_dir)

        # Generate basic glTF structure
        # This is a simplified version - full glTF export would be more complex
        nodes: list[dict] = []
        meshes: list[dict] = []

        # Add objects as nodes
        for i, (obj_id, obj) in enumerate(scene.objects.items()):
            pos = obj.transform.position
            rot = obj.transform.rotation
            scale = obj.transform.scale

            node = {
                "name": obj_id,
                "translation": [pos.x, pos.y, pos.z],
                "rotation": [rot.x, rot.y, rot.z, rot.w],
                "scale": [scale.x, scale.y, scale.z],
                "mesh": i,
            }
            nodes.append(node)

            # Simplified mesh (primitives would need actual geometry data)
            meshes.append({"name": f"{obj_id}-mesh", "primitives": []})

        # Assemble final glTF structure
        gltf = {
            "asset": {"version": "2.0", "generator": "chuk-mcp-stage"},
            "scene": 0,
            "scenes": [{"name": scene.name or scene.id, "nodes": list(range(len(scene.objects)))}],
            "nodes": nodes,
            "meshes": meshes,
            "materials": [],
            "buffers": [],
            "bufferViews": [],
            "accessors": [],
        }

        gltf_json = json.dumps(gltf, indent=2)
        await vfs.write_text(path, gltf_json)

        logger.info(f"Exported scene {scene.id} to glTF at {path}")
        return {"gltf": path}
