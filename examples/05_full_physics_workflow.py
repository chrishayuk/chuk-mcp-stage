"""Full physics-to-video workflow demonstration.

Shows the complete pipeline:
1. Create scene in chuk-mcp-stage
2. Bind to physics simulation (conceptual - would need chuk-mcp-physics running)
3. Bake physics simulation to keyframes (uses public Rapier service)
4. Export scene with animation data
5. Ready for video rendering in Remotion

NOTE: This example demonstrates the workflow. For actual physics simulation,
you would use chuk-mcp-physics to create and run the simulation first.

The baking step uses the public Rapier service at https://rapier.chukai.io by default.
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
    SceneMetadata,
    SceneObject,
    Shot,
    Transform,
    Vector3,
)
from chuk_mcp_stage.exporters import SceneExporter


async def main():
    """Demonstrate full physics-to-video workflow."""
    print("🎬 Full Physics-to-Video Workflow")
    print("=" * 60)
    print()
    print("This example shows the complete pipeline from physics")
    print("simulation to rendered video output.")
    print()
    print("🌐 Using public Rapier service: https://rapier.chukai.io")
    print("=" * 60)

    manager = SceneManager()

    # Step 1: Create Scene
    print("\n📋 STEP 1: Create 3D Scene")
    print("-" * 60)
    scene = await manager.create_scene(
        scene_id="physics-workflow",
        name="Physics Workflow Demo",
        metadata=SceneMetadata(description="Falling objects with camera tracking"),
    )
    print(f"✓ Scene created: {scene.id}")

    # Add ground plane (static)
    ground = SceneObject(
        id="ground",
        type=ObjectType.PLANE,
        transform=Transform(position=Vector3(x=0, y=0, z=0)),
        size=Vector3(x=20, y=20, z=1),
        material=Material(preset=MaterialPreset.METAL_DARK),
    )
    await manager.add_object(scene.id, ground)
    print("✓ Added ground plane (static)")

    # Add falling sphere
    ball = SceneObject(
        id="ball",
        type=ObjectType.SPHERE,
        transform=Transform(position=Vector3(x=0, y=10, z=0)),
        radius=1.0,
        material=Material(
            preset=MaterialPreset.GLASS_BLUE,
            color={"r": 0.3, "g": 0.6, "b": 1.0},
        ),
    )
    await manager.add_object(scene.id, ball)
    print("✓ Added ball at (0, 10, 0) - will fall")

    # Add a box that will also fall
    box = SceneObject(
        id="box",
        type=ObjectType.BOX,
        transform=Transform(position=Vector3(x=3, y=8, z=0)),
        size=Vector3(x=1, y=1, z=1),
        material=Material(preset=MaterialPreset.PLASTIC_RED),
    )
    await manager.add_object(scene.id, box)
    print("✓ Added box at (3, 8, 0) - will fall")

    # Step 2: Physics Binding (Conceptual)
    print("\n⚙️  STEP 2: Physics Binding (Conceptual)")
    print("-" * 60)
    print("In a real workflow, you would:")
    print("  1. Create physics simulation via chuk-mcp-physics:")
    print("     sim = await create_simulation(gravity_y=-9.81)")
    print()
    print("  2. Add rigid bodies to simulation:")
    print("     await add_rigid_body(sim_id, 'ball', shape='sphere', ...)")
    print("     await add_rigid_body(sim_id, 'box', shape='box', ...)")
    print()
    print("  3. Bind scene objects to physics bodies:")

    # Bind ball to physics (simulation would be created via chuk-mcp-physics)
    simulation_id = "sim-falling-demo"  # Would come from chuk-mcp-physics
    await manager.bind_physics(
        scene_id=scene.id,
        object_id="ball",
        physics_body_id=f"rapier://{simulation_id}/body-ball",
    )
    print(f"✓ Bound 'ball' to physics: rapier://{simulation_id}/body-ball")

    await manager.bind_physics(
        scene_id=scene.id,
        object_id="box",
        physics_body_id=f"rapier://{simulation_id}/body-box",
    )
    print(f"✓ Bound 'box' to physics: rapier://{simulation_id}/body-box")

    print()
    print("  4. Run simulation:")
    print("     await step_simulation(sim_id, steps=600)  # 10 seconds @ 60 FPS")

    # Step 3: Camera Setup
    print("\n📹 STEP 3: Camera Setup")
    print("-" * 60)

    # Orbit shot to see the whole scene
    orbit_shot = Shot(
        id="orbit-overview",
        camera_path=CameraPath(
            mode=CameraPathMode.ORBIT,
            focus="ball",
            radius=15.0,
            elevation=25.0,
            speed=0.05,
        ),
        start_time=0.0,
        end_time=5.0,
        easing=EasingFunction.EASE_IN_OUT_CUBIC,
        label="Wide orbit overview",
    )
    await manager.add_shot(scene.id, orbit_shot)
    print("✓ Added orbit shot (0-5s)")

    # Chase shot following the ball
    chase_shot = Shot(
        id="chase-ball",
        camera_path=CameraPath(
            mode=CameraPathMode.CHASE,
            target="ball",
            offset=Vector3(x=0, y=2, z=-5),
            look_ahead=True,
        ),
        start_time=5.0,
        end_time=10.0,
        easing=EasingFunction.SPRING,
        label="Chase falling ball",
    )
    await manager.add_shot(scene.id, chase_shot)
    print("✓ Added chase shot (5-10s)")

    # Step 4: Bake Simulation
    print("\n🔥 STEP 4: Bake Physics Simulation")
    print("-" * 60)
    print("⚠️  NOTE: This step requires an actual physics simulation.")
    print("    In this demo, we'll show the command but skip execution.")
    print()
    print("Command to bake simulation:")
    print("  await manager.bake_simulation(")
    print(f"      scene_id='{scene.id}',")
    print(f"      simulation_id='{simulation_id}',")
    print("      fps=60,")
    print("      duration=10.0")
    print("  )")
    print()
    print("This would:")
    print("  • Connect to Rapier service (https://rapier.chukai.io)")
    print("  • Fetch trajectory data for bound objects")
    print("  • Save keyframes to VFS: /animations/ball.json")
    print("  • Save keyframes to VFS: /animations/box.json")
    print("  • Add baked animation metadata to scene")
    print()
    print("⏭️  Skipping actual baking (requires live simulation)")

    # In a real workflow, you would do:
    # bake_result = await manager.bake_simulation(
    #     scene_id=scene.id,
    #     simulation_id=simulation_id,
    #     fps=60,
    #     duration=10.0,
    # )
    # print(f"✓ Baked {bake_result.total_frames} frames")
    # print(f"✓ Animated objects: {', '.join(bake_result.baked_objects)}")

    # Step 5: Export
    print("\n📦 STEP 5: Export Scene")
    print("-" * 60)

    final_scene = await manager.get_scene(scene.id)
    vfs = await manager.get_scene_vfs(scene.id)

    # Export to JSON
    print("\n1️⃣  Exporting to JSON...")
    json_result = await SceneExporter.export_scene(
        scene=final_scene,
        format=ExportFormat.JSON,
        vfs=vfs,
        output_path="/exports/physics-scene.json",
    )
    print(f"✓ JSON: {json_result['scene']}")

    # Export to R3F
    print("\n2️⃣  Exporting to React Three Fiber...")
    r3f_result = await SceneExporter.export_scene(
        scene=final_scene,
        format=ExportFormat.R3F_COMPONENT,
        vfs=vfs,
        output_path="/exports/r3f",
    )
    print(f"✓ Component: {r3f_result['component']}")
    if "camera" in r3f_result:
        print(f"✓ Camera:    {r3f_result['camera']}")
    if "animations" in r3f_result:
        print(f"✓ Animations: {r3f_result['animations']}")

    # Export to Remotion
    print("\n3️⃣  Exporting to Remotion project...")
    remotion_result = await SceneExporter.export_scene(
        scene=final_scene,
        format=ExportFormat.REMOTION_PROJECT,
        vfs=vfs,
        output_path="/exports/remotion",
    )
    print(f"✓ Composition: {remotion_result['composition']}")
    print(f"✓ Root:        {remotion_result['root']}")
    print(f"✓ Package:     {remotion_result['package']}")

    # Summary
    print("\n" + "=" * 60)
    print("✅ WORKFLOW COMPLETE")
    print("=" * 60)

    print("\n📊 Scene Summary:")
    print(f"   Name: {final_scene.name}")
    print(f"   Objects: {len(final_scene.objects)}")
    print(f"   Shots: {len(final_scene.shots)}")
    print("   Physics bindings: 2 (ball, box)")
    print("   Duration: 10 seconds")

    print("\n🎨 Objects:")
    for obj_id, obj in final_scene.objects.items():
        pos = obj.transform.position
        physics = "✓" if obj.physics_binding else "✗"
        print(
            f"   • {obj_id:10} {obj.type.value:8} at ({pos.x:4.1f}, {pos.y:4.1f}, {pos.z:4.1f})  Physics: {physics}"
        )

    print("\n📹 Camera Shots:")
    for shot_id, shot in final_scene.shots.items():
        mode = shot.camera_path.mode.value
        label = shot.label or "No label"
        print(f"   • {shot.start_time:4.1f}s - {shot.end_time:4.1f}s  {mode:8}  {label}")

    print("\n🎬 Complete Pipeline:")
    print("   ┌─────────────────────────────────────────────────┐")
    print("   │  1. Physics Simulation (chuk-mcp-physics)      │")
    print("   │     ↓                                           │")
    print("   │  2. Scene Composition (chuk-mcp-stage) ✓       │")
    print("   │     ↓                                           │")
    print("   │  3. Bind Physics ✓                             │")
    print("   │     ↓                                           │")
    print("   │  4. Bake Simulation (Rapier service)           │")
    print("   │     ↓                                           │")
    print("   │  5. Export (R3F/Remotion) ✓                    │")
    print("   │     ↓                                           │")
    print("   │  6. Render Video (Remotion)                    │")
    print("   └─────────────────────────────────────────────────┘")

    print("\n💡 To Complete This Workflow:")
    print()
    print("   1. Install chuk-mcp-physics:")
    print("      uvx chuk-mcp-physics")
    print()
    print("   2. Create simulation:")
    print("      sim = await create_simulation(gravity_y=-9.81)")
    print("      await add_rigid_body(sim.sim_id, 'ball', ...)")
    print("      await add_rigid_body(sim.sim_id, 'box', ...)")
    print("      await step_simulation(sim.sim_id, steps=600)")
    print()
    print("   3. Bake to scene:")
    print("      await stage_bake_simulation(")
    print("          scene_id, sim.sim_id, fps=60, duration=10.0")
    print("      )")
    print()
    print("   4. Render with Remotion:")
    print("      cd exports/remotion")
    print("      npm install")
    print("      npm run build")
    print()
    print("   🎥 Result: MP4 video with physics-driven animation!")

    print("\n🌐 Public Rapier Service Info:")
    print("   URL: https://rapier.chukai.io")
    print("   Status: Available (no auth required)")
    print("   Use case: Physics baking, trajectory recording")
    print("   Rate limits: May apply for heavy usage")
    print()
    print("   To use local service:")
    print("      export RAPIER_SERVICE_URL=http://localhost:9000")
    print("      docker run -p 9000:9000 chuk-rapier-service")

    # Cleanup
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
