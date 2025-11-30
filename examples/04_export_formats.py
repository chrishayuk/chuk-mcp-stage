"""Export formats demonstration.

Shows how to export the same scene to different formats:
- JSON (scene data)
- R3F Component (React Three Fiber)
- Remotion Project (video rendering)
- glTF (3D model format)
"""

import asyncio

from chuk_mcp_stage import (
    CameraPath,
    CameraPathMode,
    EasingFunction,
    ExportFormat,
    Material,
    MaterialPreset,
    ObjectType,
    SceneManager,
    SceneObject,
    Shot,
    Transform,
    Vector3,
)
from chuk_mcp_stage.exporters import SceneExporter


async def main():
    """Demonstrate exporting to all supported formats."""
    print("📦 Export Formats Demo")
    print("=" * 60)

    manager = SceneManager()

    # Create a simple but complete scene
    print("\n📋 Step 1: Creating demo scene...")
    scene = await manager.create_scene(
        scene_id="export-demo",
        name="Export Formats Showcase",
    )
    print(f"✓ Scene created: {scene.id}")

    # Add objects
    print("\n🎨 Step 2: Adding objects...")

    # Ground
    ground = SceneObject(
        id="ground",
        type=ObjectType.PLANE,
        transform=Transform(position=Vector3(x=0, y=0, z=0)),
        size=Vector3(x=20, y=20, z=1),
        material=Material(preset=MaterialPreset.METAL_DARK),
    )
    await manager.add_object(scene.id, ground)

    # Center sphere
    sphere = SceneObject(
        id="sphere",
        type=ObjectType.SPHERE,
        transform=Transform(position=Vector3(x=0, y=2, z=0)),
        radius=1.5,
        material=Material(
            preset=MaterialPreset.GLASS_BLUE,
            color={"r": 0.2, "g": 0.5, "b": 1.0},
        ),
    )
    await manager.add_object(scene.id, sphere)

    # Boxes
    box1 = SceneObject(
        id="box-red",
        type=ObjectType.BOX,
        transform=Transform(position=Vector3(x=-3, y=0.5, z=0)),
        size=Vector3(x=1, y=1, z=1),
        material=Material(preset=MaterialPreset.PLASTIC_RED),
    )
    await manager.add_object(scene.id, box1)

    box2 = SceneObject(
        id="box-blue",
        type=ObjectType.BOX,
        transform=Transform(position=Vector3(x=3, y=0.5, z=0)),
        size=Vector3(x=1, y=1, z=1),
        material=Material(preset=MaterialPreset.PLASTIC_BLUE),
    )
    await manager.add_object(scene.id, box2)

    print("✓ Added 4 objects (1 plane, 1 sphere, 2 boxes)")

    # Add camera shot
    print("\n📹 Step 3: Adding camera shot...")
    shot = Shot(
        id="main-shot",
        camera_path=CameraPath(
            mode=CameraPathMode.ORBIT,
            focus="sphere",
            radius=8.0,
            elevation=30.0,
            speed=0.1,
        ),
        start_time=0.0,
        end_time=10.0,
        easing=EasingFunction.EASE_IN_OUT_CUBIC,
    )
    await manager.add_shot(scene.id, shot)
    print("✓ Added orbit camera shot")

    # Get the scene for export
    final_scene = await manager.get_scene(scene.id)

    # Get VFS for exports
    vfs = await manager.get_scene_vfs(scene.id)

    # Export to all formats
    print("\n📦 Step 4: Exporting to all formats...")
    print("=" * 60)

    # 1. JSON Export
    print("\n1️⃣  JSON Export")
    print("-" * 60)
    json_result = await SceneExporter.export_scene(
        scene=final_scene,
        format=ExportFormat.JSON,
        vfs=vfs,
        output_path="/exports/scene.json",
    )
    print(f"✓ Exported to: {json_result['scene']}")
    print("   Use case: Scene data backup, API responses, debugging")
    print("   Contains: Full scene graph, materials, transforms, shots")

    # Read and show snippet
    json_content = await vfs.read_text(json_result["scene"])
    print(f"   File size: {len(json_content)} characters")
    print("   Preview: { id, name, objects, shots, environment, ... }")

    # 2. R3F Component Export
    print("\n2️⃣  React Three Fiber (R3F) Component")
    print("-" * 60)
    r3f_result = await SceneExporter.export_scene(
        scene=final_scene,
        format=ExportFormat.R3F_COMPONENT,
        vfs=vfs,
        output_path="/exports/r3f",
    )
    print(f"✓ Component: {r3f_result['component']}")
    if "camera" in r3f_result:
        print(f"✓ Camera:    {r3f_result['camera']}")
    print("   Use case: Interactive 3D web experiences, previews")
    print("   Framework: React + Three.js")
    print("   Features: Camera controls, orbit controls, materials")

    # Show component preview
    component_content = await vfs.read_text(r3f_result["component"])
    print(f"   Lines: {len(component_content.splitlines())}")
    print("   Preview:")
    lines = component_content.splitlines()[:5]
    for line in lines:
        print(f"      {line}")
    print("      ...")

    # 3. Remotion Project Export
    print("\n3️⃣  Remotion Project")
    print("-" * 60)
    remotion_result = await SceneExporter.export_scene(
        scene=final_scene,
        format=ExportFormat.REMOTION_PROJECT,
        vfs=vfs,
        output_path="/exports/remotion",
    )
    print(f"✓ Composition: {remotion_result['composition']}")
    print(f"✓ Root:        {remotion_result['root']}")
    print(f"✓ Package:     {remotion_result['package']}")
    print("   Use case: Video rendering, MP4 export, animations")
    print("   Framework: Remotion (React for video)")
    print("   Features: Timeline, FPS, duration, camera movements")
    print(f"   Duration:  {10 * 30} frames @ 30 FPS (10 seconds)")

    # Show package.json
    package_content = await vfs.read_text(remotion_result["package"])
    import json as json_module

    package_data = json_module.loads(package_content)
    print(f"   Project name: {package_data['name']}")
    print("   Scripts:")
    for script, cmd in package_data["scripts"].items():
        print(f"      {script}: {cmd}")

    # 4. glTF Export
    print("\n4️⃣  glTF (GL Transmission Format)")
    print("-" * 60)
    gltf_result = await SceneExporter.export_scene(
        scene=final_scene,
        format=ExportFormat.GLTF,
        vfs=vfs,
        output_path="/exports/scene.gltf",
    )
    print(f"✓ Exported to: {gltf_result['gltf']}")
    print("   Use case: 3D model exchange, game engines, AR/VR")
    print("   Format: Industry standard 3D interchange")
    print("   Compatible with: Blender, Unity, Unreal, Three.js")
    print("   Contains: Meshes, materials, transforms (simplified)")

    # Summary
    print("\n" + "=" * 60)
    print("✅ EXPORT COMPLETE")
    print("=" * 60)

    print("\n📊 Summary:")
    print(f"   Scene: {final_scene.name}")
    print(f"   Objects: {len(final_scene.objects)}")
    print(f"   Shots: {len(final_scene.shots)}")
    print("   Exports: 4 formats")

    print("\n📂 Export Locations:")
    print(f"   • JSON:     {json_result['scene']}")
    print(f"   • R3F:      {r3f_result['component']}")
    print(f"   • Remotion: {remotion_result['root']}")
    print(f"   • glTF:     {gltf_result['gltf']}")

    print("\n🎯 Format Comparison:")
    print()
    print("   Format      | Use Case                    | Output Type")
    print("   " + "-" * 58)
    print("   JSON        | Data storage/API            | Single .json file")
    print("   R3F         | Interactive web 3D          | .tsx components")
    print("   Remotion    | Video rendering             | Full project folder")
    print("   glTF        | 3D model interchange        | .gltf file")

    print("\n💡 Next Steps:")
    print("   JSON:")
    print("      - Use in APIs, store in database")
    print("      - Import back with stage_get_scene()")
    print()
    print("   R3F:")
    print("      - Copy to React project")
    print("      - Import: import { Scene } from './Scene'")
    print("      - Add to <Canvas> component")
    print()
    print("   Remotion:")
    print("      - cd exports/remotion")
    print("      - npm install")
    print("      - npm run start (preview)")
    print("      - npm run build (render MP4)")
    print()
    print("   glTF:")
    print("      - Open in Blender/Three.js viewer")
    print("      - Import to game engine")
    print("      - Use in AR/VR applications")

    # Cleanup
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
