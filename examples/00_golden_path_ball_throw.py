"""Golden path example: Complete ball throw workflow.

This is the canonical "start here" example that demonstrates:
1. Scene creation and object placement
2. Physics simulation setup (conceptual - requires chuk-mcp-physics)
3. Physics binding
4. Baking simulation to keyframes
5. Export to multiple formats
6. Artifact URI usage

This example shows the FULL pipeline from physics to video-ready exports.
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
    """Demonstrate the golden path: physics → stage → export."""
    print("🎯 GOLDEN PATH EXAMPLE: Ball Throw")
    print("=" * 70)
    print()
    print("This example demonstrates the complete pipeline:")
    print("  Physics Simulation → Scene Composition → Baking → Export → Video")
    print()
    print("=" * 70)

    manager = SceneManager()

    # ═══════════════════════════════════════════════════════════════
    # PHASE 1: AUTHORING (Declarative)
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "═" * 70)
    print("PHASE 1: AUTHORING (Define the world)")
    print("═" * 70)

    # Step 1: Create scene
    print("\n📋 Step 1: Create Scene")
    print("-" * 70)
    scene = await manager.create_scene(
        scene_id="golden-path-ball-throw",
        name="Golden Path: Ball Throw",
        metadata=SceneMetadata(
            description="Complete ball throw workflow demonstration",
            author="CHUK Example",
        ),
    )
    print(f"✓ Created scene: {scene.id}")
    print(f"  Workspace: artifact://stage/{scene.id}")

    # Step 2: Add ground plane (static)
    print("\n🌍 Step 2: Add Ground Plane")
    print("-" * 70)
    ground = SceneObject(
        id="ground",
        type=ObjectType.PLANE,
        transform=Transform(position=Vector3(x=0, y=0, z=0)),
        size=Vector3(x=30, y=30, z=1),
        material=Material(preset=MaterialPreset.METAL_DARK),
    )
    await manager.add_object(scene.id, ground)
    print("✓ Added ground plane (30x30m)")
    print("  Position: (0, 0, 0)")
    print("  Material: metal-dark")
    print("  Role: Static - no physics binding needed")

    # Step 3: Add ball (will be thrown)
    print("\n⚾ Step 3: Add Ball (Dynamic Object)")
    print("-" * 70)
    ball = SceneObject(
        id="ball",
        type=ObjectType.SPHERE,
        transform=Transform(position=Vector3(x=0, y=2, z=0)),  # Start at 2m height
        radius=0.5,
        material=Material(
            preset=MaterialPreset.GLASS_BLUE,
            color={"r": 0.2, "g": 0.5, "b": 1.0},
        ),
    )
    await manager.add_object(scene.id, ball)
    print("✓ Added ball (sphere, radius=0.5m)")
    print("  Initial position: (0, 2, 0)")
    print("  Material: glass-blue")
    print("  Role: Dynamic - will be physics-driven")

    # Step 4: Add camera shots
    print("\n📹 Step 4: Add Camera Shots")
    print("-" * 70)

    # Chase shot - follows the ball
    chase_shot = Shot(
        id="chase",
        camera_path=CameraPath(
            mode=CameraPathMode.CHASE,
            target="ball",
            offset=Vector3(x=-3, y=2, z=-5),  # Behind and above
            look_ahead=True,
        ),
        start_time=0.0,
        end_time=3.0,
        easing=EasingFunction.SPRING,
        label="Chase ball in flight",
    )
    await manager.add_shot(scene.id, chase_shot)
    print("✓ Shot 1: CHASE (0-3s)")
    print("  Follows ball with spring easing")
    print("  Offset: (-3, 2, -5) - behind and above")

    # Static wide shot - see the whole trajectory
    static_shot = Shot(
        id="wide",
        camera_path=CameraPath(
            mode=CameraPathMode.STATIC,
            position=Vector3(x=10, y=5, z=10),
            look_at=Vector3(x=0, y=2, z=0),
        ),
        start_time=3.0,
        end_time=5.0,
        easing=EasingFunction.LINEAR,
        label="Wide static view",
    )
    await manager.add_shot(scene.id, static_shot)
    print("✓ Shot 2: STATIC (3-5s)")
    print("  Wide angle from (10, 5, 10)")
    print("  Looking at: (0, 2, 0)")

    # Step 5: Physics binding (metadata only)
    print("\n🔗 Step 5: Bind Physics (Metadata Only)")
    print("-" * 70)
    print("NOTE: This is where you would create a physics simulation")
    print("      using chuk-mcp-physics. For this example, we show")
    print("      the binding step conceptually.")
    print()

    # Conceptual physics setup
    simulation_id = "sim-ball-throw-demo"  # Would come from chuk-mcp-physics
    print("Conceptual physics setup:")
    print(f"  1. create_simulation(sim_id='{simulation_id}', gravity_y=-9.81)")
    print("  2. add_rigid_body(")
    print("       sim_id='{simulation_id}',")
    print("       body_id='ball',")
    print("       shape='sphere',")
    print("       radius=0.5,")
    print("       position=[0, 2, 0],")
    print("       velocity=[5, 8, 0]  # Throw upward and forward")
    print("     )")
    print("  3. step_simulation(sim_id='{simulation_id}', steps=300)  # 5s @ 60 FPS")
    print()

    # Bind the ball to physics body
    await manager.bind_physics(
        scene_id=scene.id,
        object_id="ball",
        physics_body_id=f"rapier://{simulation_id}/body-ball",
    )
    print(f"✓ Bound 'ball' → rapier://{simulation_id}/body-ball")
    print("  ⚠️  This is METADATA ONLY - no motion data yet!")
    print("  The actual motion comes from baking (Phase 2)")

    # ═══════════════════════════════════════════════════════════════
    # PHASE 2: BAKING (Computational)
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "═" * 70)
    print("PHASE 2: BAKING (Generate animation keyframes)")
    print("═" * 70)

    print("\n🔥 Step 6: Bake Simulation to Keyframes")
    print("-" * 70)
    print("⚠️  NOTE: This step requires an ACTUAL physics simulation.")
    print("    In a real workflow, you would:")
    print()
    print("    1. Run the physics simulation (chuk-mcp-physics)")
    print("    2. Call stage_bake_simulation to sample the physics state")
    print("    3. Keyframes would be saved to VFS")
    print()
    print("Command that would be run:")
    print("  await manager.bake_simulation(")
    print(f"      scene_id='{scene.id}',")
    print(f"      simulation_id='{simulation_id}',")
    print("      fps=60,")
    print("      duration=5.0")
    print("  )")
    print()
    print("This would:")
    print("  • Connect to Rapier service (https://rapier.chukai.io)")
    print("  • Sample physics at 60 FPS for 5 seconds (300 frames)")
    print("  • Generate keyframes: {time, position, rotation, velocity}")
    print("  • Save to VFS: /animations/ball.json")
    print()
    print("⏭️  Skipping actual baking (requires live physics simulation)")

    # In a real workflow:
    # bake_result = await manager.bake_simulation(
    #     scene_id=scene.id,
    #     simulation_id=simulation_id,
    #     fps=60,
    #     duration=5.0,
    # )
    # print(f"✓ Baked {bake_result.total_frames} frames")
    # print(f"✓ Objects animated: {', '.join(bake_result.baked_objects)}")

    # ═══════════════════════════════════════════════════════════════
    # PHASE 3: EXPORT (Generate rendering-ready code)
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "═" * 70)
    print("PHASE 3: EXPORT (Generate rendering code)")
    print("═" * 70)

    final_scene = await manager.get_scene(scene.id)
    vfs = await manager.get_scene_vfs(scene.id)

    # Export 1: JSON (scene data)
    print("\n📦 Export 1: JSON (Scene Data)")
    print("-" * 70)
    json_result = await SceneExporter.export_scene(
        scene=final_scene,
        format=ExportFormat.JSON,
        vfs=vfs,
        output_path="/exports/scene.json",
    )
    print(f"✓ Exported: {json_result['scene']}")
    print("  Use case: Backup, API responses, debugging")
    print("  Artifact URI: artifact://stage/{scene.id}/exports/scene.json")

    # Export 2: R3F Component
    print("\n📦 Export 2: React Three Fiber Component")
    print("-" * 70)
    r3f_result = await SceneExporter.export_scene(
        scene=final_scene,
        format=ExportFormat.R3F_COMPONENT,
        vfs=vfs,
        output_path="/exports/r3f",
    )
    print(f"✓ Component: {r3f_result['component']}")
    if "camera" in r3f_result:
        print(f"✓ Camera:    {r3f_result['camera']}")
    print("  Use case: Interactive 3D web experiences")
    print("  Artifact URI: artifact://stage/{scene.id}/exports/r3f/Scene.tsx")

    # Export 3: Remotion Project
    print("\n📦 Export 3: Remotion Project (Video Rendering)")
    print("-" * 70)
    remotion_result = await SceneExporter.export_scene(
        scene=final_scene,
        format=ExportFormat.REMOTION_PROJECT,
        vfs=vfs,
        output_path="/exports/remotion",
    )
    print(f"✓ Composition: {remotion_result['composition']}")
    print(f"✓ Root:        {remotion_result['root']}")
    print(f"✓ Package:     {remotion_result['package']}")
    print("  Use case: MP4 video export, animations")
    print("  Artifact URI: artifact://stage/{scene.id}/exports/remotion/")

    # ═══════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════

    print("\n" + "═" * 70)
    print("✅ GOLDEN PATH COMPLETE")
    print("═" * 70)

    print("\n📊 Scene Summary:")
    print(f"   Name: {final_scene.name}")
    print(f"   Objects: {len(final_scene.objects)}")
    print(f"   Shots: {len(final_scene.shots)}")
    print("   Duration: 5 seconds")

    print("\n🎨 Objects:")
    for obj_id, obj in final_scene.objects.items():
        pos = obj.transform.position
        physics = "✓ Physics-bound" if obj.physics_binding else "✗ Static"
        print(
            f"   • {obj_id:8} {obj.type.value:8} at ({pos.x:4.1f}, {pos.y:4.1f}, {pos.z:4.1f})  {physics}"
        )

    print("\n📹 Camera Shots:")
    for shot_id, shot in final_scene.shots.items():
        mode = shot.camera_path.mode.value
        label = shot.label or "No label"
        print(f"   • {shot.start_time:4.1f}s - {shot.end_time:4.1f}s  {mode:8}  {label}")

    print("\n📂 Artifact URIs (Not file contents!):")
    print(f"   Scene data:  artifact://stage/{scene.id}/exports/scene.json")
    print(f"   R3F:         artifact://stage/{scene.id}/exports/r3f/Scene.tsx")
    print(f"   Remotion:    artifact://stage/{scene.id}/exports/remotion/")

    print("\n🎬 Complete Pipeline:")
    print("   ┌─────────────────────────────────────────────┐")
    print("   │  1. Authoring   - Define scene structure   │")
    print("   │  2. Physics     - Create simulation         │")
    print("   │  3. Binding     - Link objects → bodies     │")
    print("   │  4. Baking      - Physics → keyframes       │")
    print("   │  5. Export      - Scene → R3F/Remotion      │")
    print("   │  6. Render      - Remotion → MP4            │")
    print("   └─────────────────────────────────────────────┘")

    print("\n💡 To Complete This Workflow:")
    print()
    print("   1. Install chuk-mcp-physics:")
    print("      uvx chuk-mcp-physics")
    print()
    print("   2. Create simulation:")
    print("      sim = await create_simulation(gravity_y=-9.81)")
    print("      await add_rigid_body(")
    print("          sim.sim_id,")
    print("          body_id='ball',")
    print("          shape='sphere',")
    print("          radius=0.5,")
    print("          position=[0, 2, 0],")
    print("          velocity=[5, 8, 0]  # Throw!")
    print("      )")
    print("      await step_simulation(sim.sim_id, steps=300)")
    print()
    print("   3. Bake to stage:")
    print("      await manager.bake_simulation(")
    print("          scene_id, sim.sim_id, fps=60, duration=5.0")
    print("      )")
    print()
    print("   4. Render with Remotion:")
    print("      cd exports/remotion")
    print("      npm install")
    print("      npm run build")
    print()
    print("   🎥 Result: MP4 video with physics-driven ball throw!")

    print("\n🌐 Artifact URI Benefits:")
    print("   • No inline bloat - returns URIs, not massive JSON")
    print("   • VFS operations - Use vfs_ls, vfs_read, vfs_cp")
    print("   • Cross-tool sharing - Other MCP servers can access")
    print("   • Persistent storage - Scenes survive across sessions")

    print("\n🚀 What Makes This 'Golden Path':")
    print("   ✓ Shows FULL pipeline (authoring → baking → export)")
    print("   ✓ Demonstrates two-phase model (declarative → computational)")
    print("   ✓ Uses artifact URIs (not inline data)")
    print("   ✓ Integrates with physics oracle (chuk-mcp-physics)")
    print("   ✓ Exports to multiple formats (JSON, R3F, Remotion)")
    print("   ✓ Ready for video rendering (Remotion → MP4)")

    # Cleanup
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
