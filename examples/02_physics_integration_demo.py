"""Physics integration demonstration.

Shows how to:
1. Define scene objects
2. Bind them to physics bodies (conceptual - requires chuk-mcp-physics)
3. Bake simulation to keyframes
4. Export to R3F

This is a conceptual demo - actual physics requires chuk-mcp-physics server.
"""

import asyncio

from chuk_mcp_stage import (
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
    SceneManager,
    SceneObject,
    Shot,
    Transform,
    Vector3,
)
from chuk_mcp_stage.exporters import SceneExporter
from chuk_mcp_stage.models import ExportFormat


async def main():
    """Demonstrate full physics → stage → export workflow."""
    print("🎬 Physics Integration Demo")
    print("=" * 60)

    manager = SceneManager()

    # ========================================================================
    # STEP 1: Create Scene
    # ========================================================================
    print("\n📋 Step 1: Creating scene...")

    from chuk_mcp_stage.models import SceneMetadata

    metadata = SceneMetadata(author="Claude", description="Pendulum physics demonstration")
    scene = await manager.create_scene(
        scene_id="pendulum-demo", name="Pendulum Physics Demo", metadata=metadata
    )
    print(f"✓ Scene created: {scene.id}")

    # ========================================================================
    # STEP 2: Define Environment & Lighting
    # ========================================================================
    print("\n🌅 Step 2: Setting up environment...")

    environment = Environment(type=EnvironmentType.GRADIENT, intensity=0.8)
    lighting = Lighting(preset=LightingPreset.THREE_POINT, ambient_intensity=0.5)

    await manager.set_environment(scene.id, environment, lighting)
    print(f"✓ Environment: {environment.type.value}")
    print(f"✓ Lighting: {lighting.preset.value}")

    # ========================================================================
    # STEP 3: Add Scene Objects
    # ========================================================================
    print("\n🎨 Step 3: Adding scene objects...")

    # Pivot point (static)
    pivot = SceneObject(
        id="pivot",
        type=ObjectType.SPHERE,
        transform=Transform(position=Vector3(x=0, y=2, z=0)),
        radius=0.1,
        material=Material(preset=MaterialPreset.METAL_DARK),
    )
    await manager.add_object(scene.id, pivot)
    print("✓ Added pivot sphere")

    # Pendulum bob (dynamic)
    bob = SceneObject(
        id="bob",
        type=ObjectType.SPHERE,
        transform=Transform(position=Vector3(x=1, y=1, z=0)),
        radius=0.5,
        material=Material(preset=MaterialPreset.GLASS_BLUE, color={"r": 0.2, "g": 0.4, "b": 1.0}),
    )
    await manager.add_object(scene.id, bob)
    print("✓ Added pendulum bob")

    # Ground plane (static)
    ground = SceneObject(
        id="ground",
        type=ObjectType.PLANE,
        transform=Transform(position=Vector3(x=0, y=-0.5, z=0)),
        size=Vector3(x=10, y=10, z=1),
        material=Material(preset=MaterialPreset.METAL_LIGHT),
    )
    await manager.add_object(scene.id, ground)
    print("✓ Added ground plane")

    # ========================================================================
    # STEP 4: Bind Physics (Conceptual)
    # ========================================================================
    print("\n⚙️  Step 4: Physics binding (conceptual)...")

    # In real usage, you would:
    # 1. Create physics simulation with chuk-mcp-physics
    # 2. Add rigid bodies matching your scene objects
    # 3. Bind scene objects to physics bodies

    # Conceptual bindings:
    sim_id = "sim-pendulum-001"
    await manager.bind_physics(scene.id, "bob", f"rapier://{sim_id}/body-bob")
    print("✓ Bound 'bob' to physics body")
    print(f"  → rapier://{sim_id}/body-bob")

    # ========================================================================
    # STEP 5: Add Camera Shots
    # ========================================================================
    print("\n📹 Step 5: Setting up camera shots...")

    # Orbit shot around the pendulum
    orbit_shot = Shot(
        id="orbit-shot",
        camera_path=CameraPath(
            mode=CameraPathMode.ORBIT,
            focus="bob",
            radius=5.0,
            elevation=25.0,
            speed=0.05,  # Slow rotation
        ),
        start_time=0.0,
        end_time=10.0,
        easing=EasingFunction.EASE_IN_OUT_CUBIC,
    )
    await manager.add_shot(scene.id, orbit_shot)
    print("✓ Added orbit shot (10s, radius=5.0)")

    # Static side view
    static_shot = Shot(
        id="side-view",
        camera_path=CameraPath(
            mode=CameraPathMode.STATIC,
            position=Vector3(x=3, y=1.5, z=0),
            look_at=Vector3(x=0, y=1.5, z=0),
        ),
        start_time=10.0,
        end_time=15.0,
        easing=EasingFunction.LINEAR,
    )
    await manager.add_shot(scene.id, static_shot)
    print("✓ Added static side view (5s)")

    # ========================================================================
    # STEP 6: Export Scene
    # ========================================================================
    print("\n📦 Step 6: Exporting scene...")

    vfs = await manager.get_scene_vfs(scene.id)

    # Export to JSON
    json_files = await SceneExporter.export_scene(
        scene, ExportFormat.JSON, vfs, output_path="/export/scene.json"
    )
    print(f"✓ Exported JSON: {json_files['scene']}")

    # Export to R3F
    r3f_files = await SceneExporter.export_scene(
        scene, ExportFormat.R3F_COMPONENT, vfs, output_path="/export/r3f"
    )
    print(f"✓ Exported R3F component: {r3f_files['component']}")
    if "camera" in r3f_files:
        print(f"  + Camera controller: {r3f_files['camera']}")

    # ========================================================================
    # SUMMARY
    # ========================================================================
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60)

    final_scene = await manager.get_scene(scene.id)

    print("\n📊 Scene Summary:")
    print(f"   ID: {final_scene.id}")
    print(f"   Name: {final_scene.name}")
    print(f"   Objects: {len(final_scene.objects)}")
    print(f"   Shots: {len(final_scene.shots)}")

    print("\n🎨 Objects:")
    for obj_id, obj in final_scene.objects.items():
        pos = obj.transform.position
        binding = obj.physics_binding or "none"
        print(f"   • {obj_id}")
        print(f"     Type: {obj.type.value}")
        print(f"     Position: ({pos.x}, {pos.y}, {pos.z})")
        print(f"     Material: {obj.material.preset.value}")
        print(f"     Physics: {binding}")

    print("\n📹 Shots:")
    for shot_id, shot in final_scene.shots.items():
        duration = shot.end_time - shot.start_time
        print(f"   • {shot_id}")
        print(f"     Mode: {shot.camera_path.mode.value}")
        print(f"     Duration: {duration}s")
        print(f"     Time range: {shot.start_time}s - {shot.end_time}s")

    print("\n💡 Next Steps (with full physics):")
    print("   1. Run physics simulation (chuk-mcp-physics)")
    print("   2. Bake simulation: stage_bake_simulation(...)")
    print("   3. Export with animation data")
    print("   4. Render with Remotion → MP4!")

    # Cleanup
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
