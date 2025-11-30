"""Camera shots and cinematography demonstration.

Shows all camera movement modes and easing functions available in chuk-mcp-stage.
"""

import asyncio

from chuk_mcp_stage import (
    CameraPath,
    CameraPathMode,
    EasingFunction,
    Material,
    MaterialPreset,
    ObjectType,
    SceneManager,
    SceneObject,
    Shot,
    Transform,
    Vector3,
)


async def main():
    """Demonstrate all camera shot types."""
    print("🎬 Camera Shots & Cinematography Demo")
    print("=" * 60)

    manager = SceneManager()

    # Create scene
    print("\n📋 Step 1: Creating scene...")
    scene = await manager.create_scene(
        scene_id="camera-demo",
        name="Camera Shots Showcase",
    )
    print(f"✓ Scene created: {scene.id}")

    # Add a central object to focus on
    print("\n🎨 Step 2: Adding scene objects...")

    # Central sphere
    center = SceneObject(
        id="center",
        type=ObjectType.SPHERE,
        transform=Transform(position=Vector3(x=0, y=1.5, z=0)),
        radius=1.0,
        material=Material(preset=MaterialPreset.GLASS_BLUE),
    )
    await manager.add_object(scene.id, center)
    print("✓ Added center sphere")

    # Ground plane
    ground = SceneObject(
        id="ground",
        type=ObjectType.PLANE,
        transform=Transform(position=Vector3(x=0, y=0, z=0)),
        size=Vector3(x=30, y=30, z=1),
        material=Material(preset=MaterialPreset.METAL_DARK),
    )
    await manager.add_object(scene.id, ground)
    print("✓ Added ground plane")

    # Add some surrounding objects for depth
    for i in range(4):
        angle = i * 90  # 0, 90, 180, 270 degrees
        import math

        rad = math.radians(angle)
        x = math.cos(rad) * 5
        z = math.sin(rad) * 5

        box = SceneObject(
            id=f"box-{i}",
            type=ObjectType.BOX,
            transform=Transform(position=Vector3(x=x, y=0.5, z=z)),
            size=Vector3(x=1, y=1, z=1),
            material=Material(preset=MaterialPreset.PLASTIC_RED),
        )
        await manager.add_object(scene.id, box)
    print("✓ Added 4 surrounding boxes")

    # Add camera shots showcasing different modes
    print("\n📹 Step 3: Adding camera shots...")

    # Shot 1: ORBIT - Classic orbiting camera
    shot1 = Shot(
        id="orbit-shot",
        camera_path=CameraPath(
            mode=CameraPathMode.ORBIT,
            focus="center",
            radius=8.0,
            elevation=25.0,
            speed=0.05,  # Slow orbit (0.05 revolutions/second)
        ),
        start_time=0.0,
        end_time=10.0,
        easing=EasingFunction.EASE_IN_OUT_CUBIC,
        label="Smooth orbit around center",
    )
    await manager.add_shot(scene.id, shot1)
    print("✓ Shot 1: ORBIT (10s, smooth)")

    # Shot 2: STATIC - Fixed camera position
    shot2 = Shot(
        id="static-shot",
        camera_path=CameraPath(
            mode=CameraPathMode.STATIC,
            position=Vector3(x=10, y=3, z=10),
            look_at=Vector3(x=0, y=1.5, z=0),
        ),
        start_time=10.0,
        end_time=15.0,
        easing=EasingFunction.LINEAR,
        label="Static wide angle",
    )
    await manager.add_shot(scene.id, shot2)
    print("✓ Shot 2: STATIC (5s, wide angle)")

    # Shot 3: DOLLY - Camera moves along a path
    shot3 = Shot(
        id="dolly-shot",
        camera_path=CameraPath(
            mode=CameraPathMode.DOLLY,
            start_position=Vector3(x=-10, y=2, z=0),
            end_position=Vector3(x=10, y=2, z=0),
            look_at=Vector3(x=0, y=1.5, z=0),
        ),
        start_time=15.0,
        end_time=22.0,
        easing=EasingFunction.EASE_IN_OUT_CUBIC,
        label="Dolly tracking shot",
    )
    await manager.add_shot(scene.id, shot3)
    print("✓ Shot 3: DOLLY (7s, left to right)")

    # Shot 4: CHASE - Follow a moving object
    shot4 = Shot(
        id="chase-shot",
        camera_path=CameraPath(
            mode=CameraPathMode.CHASE,
            target="center",
            offset=Vector3(x=0, y=2, z=-5),
            look_ahead=True,
        ),
        start_time=22.0,
        end_time=28.0,
        easing=EasingFunction.SPRING,
        label="Chase camera with spring easing",
    )
    await manager.add_shot(scene.id, shot4)
    print("✓ Shot 4: CHASE (6s, spring easing)")

    # Shot 5: ORBIT with different easing - Fast spin
    shot5 = Shot(
        id="fast-orbit",
        camera_path=CameraPath(
            mode=CameraPathMode.ORBIT,
            focus="center",
            radius=6.0,
            elevation=15.0,
            speed=0.2,  # Faster spin
        ),
        start_time=28.0,
        end_time=33.0,
        easing=EasingFunction.LINEAR,
        label="Fast linear orbit",
    )
    await manager.add_shot(scene.id, shot5)
    print("✓ Shot 5: FAST ORBIT (5s, linear)")

    # Shot 6: STATIC - Low angle dramatic
    shot6 = Shot(
        id="low-angle",
        camera_path=CameraPath(
            mode=CameraPathMode.STATIC,
            position=Vector3(x=3, y=0.5, z=3),
            look_at=Vector3(x=0, y=2, z=0),
        ),
        start_time=33.0,
        end_time=38.0,
        easing=EasingFunction.EASE_OUT_CUBIC,
        label="Low angle hero shot",
    )
    await manager.add_shot(scene.id, shot6)
    print("✓ Shot 6: LOW ANGLE STATIC (5s)")

    # Get final scene
    print("\n📊 Step 4: Scene summary...")
    final_scene = await manager.get_scene(scene.id)

    print("\n" + "=" * 60)
    print("✅ CAMERA SHOTS DEMO COMPLETE")
    print("=" * 60)

    print(f"\n📋 Scene: {final_scene.name}")
    print(f"   Objects: {len(final_scene.objects)}")
    print(f"   Shots: {len(final_scene.shots)}")
    print("   Total duration: 38 seconds")

    print("\n🎨 Objects:")
    for obj_id, obj in final_scene.objects.items():
        pos = obj.transform.position
        print(f"   • {obj_id:12} {obj.type.value:8} at ({pos.x:5.1f}, {pos.y:5.1f}, {pos.z:5.1f})")

    print("\n📹 Shot Sequence:")
    total_time = 0
    for shot_id, shot in final_scene.shots.items():
        duration = shot.end_time - shot.start_time
        mode = shot.camera_path.mode.value
        easing = shot.easing.value if shot.easing else "default"
        label = shot.label or "No label"

        print(f"   • {shot.start_time:5.1f}s - {shot.end_time:5.1f}s ({duration:4.1f}s)")
        print(f"     {shot_id:15} Mode: {mode:8} Easing: {easing}")
        print(f"     Label: {label}")
        total_time = max(total_time, shot.end_time)

    print(f"\n⏱️  Total Timeline: {total_time} seconds")

    print("\n💡 Easing Functions Demonstrated:")
    print("   • EASE_IN_OUT_CUBIC - Smooth acceleration/deceleration")
    print("   • LINEAR - Constant speed throughout")
    print("   • SPRING - Bouncy, natural motion")
    print("   • EASE_OUT_CUBIC - Fast start, slow end")

    print("\n🎬 Camera Modes Demonstrated:")
    print("   • ORBIT - Rotate around a focus point")
    print("   • STATIC - Fixed camera position")
    print("   • DOLLY - Linear movement along a path")
    print("   • CHASE - Follow a moving object")

    print("\n💡 Next Steps:")
    print("   1. Export this scene: stage_export_scene(scene_id, format='r3f-component')")
    print("   2. View in R3F preview with timeline controls")
    print("   3. Export to Remotion for final video rendering")
    print("   4. Try different easing functions and timings")

    # Cleanup
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
