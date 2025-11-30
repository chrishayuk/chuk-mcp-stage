"""Simple scene creation example.

Demonstrates basic scene creation, object placement, and camera setup.
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
    """Create a simple scene with a falling ball."""
    print("Creating simple falling ball scene...")

    # Create scene manager
    manager = SceneManager()

    # 1. Create scene
    scene = await manager.create_scene(
        scene_id="falling-ball",
        name="Falling Ball Demo",
    )
    print(f"✓ Created scene: {scene.id}")

    # 2. Add ground plane
    ground = SceneObject(
        id="ground",
        type=ObjectType.PLANE,
        transform=Transform(position=Vector3(x=0, y=0, z=0)),
        size=Vector3(x=20, y=20, z=1),
        material=Material(preset=MaterialPreset.METAL_DARK),
    )
    await manager.add_object(scene.id, ground)
    print("✓ Added ground plane")

    # 3. Add falling ball
    ball = SceneObject(
        id="ball",
        type=ObjectType.SPHERE,
        transform=Transform(position=Vector3(x=0, y=5, z=0)),
        radius=1.0,
        material=Material(
            preset=MaterialPreset.GLASS_BLUE,
            color={"r": 0.3, "g": 0.5, "b": 1.0},
        ),
    )
    await manager.add_object(scene.id, ball)
    print("✓ Added ball at (0, 5, 0)")

    # 4. Add orbiting camera shot
    shot = Shot(
        id="orbit-shot",
        camera_path=CameraPath(
            mode=CameraPathMode.ORBIT,
            focus="ball",
            radius=8.0,
            elevation=30.0,
            speed=0.1,  # 0.1 revolutions per second
        ),
        start_time=0.0,
        end_time=10.0,
        easing=EasingFunction.EASE_IN_OUT_CUBIC,
    )
    await manager.add_shot(scene.id, shot)
    print("✓ Added orbit camera shot (10s)")

    # 5. Get final scene
    final_scene = await manager.get_scene(scene.id)
    print("\n📋 Final scene summary:")
    print(f"   Name: {final_scene.name}")
    print(f"   Objects: {len(final_scene.objects)}")
    print(f"   Shots: {len(final_scene.shots)}")

    for obj_id, obj in final_scene.objects.items():
        print(
            f"   - {obj_id}: {obj.type.value} at ({obj.transform.position.x}, {obj.transform.position.y}, {obj.transform.position.z})"
        )

    for shot_id, shot in final_scene.shots.items():
        duration = shot.end_time - shot.start_time
        print(f"   - {shot_id}: {shot.camera_path.mode.value} ({duration}s)")

    print("\n✅ Scene created successfully!")

    # Cleanup
    await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
