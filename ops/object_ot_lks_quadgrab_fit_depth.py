"""Fit Depth operator – set PROP_MAX_DEPTH to match selected objects without
moving the QuadGrab Reference Plane.

Projects every selected object's bounding-box corners into the plane's
rotation frame, measures how far the geometry extends below the plane
surface, and writes the result (+ fit margin) to PROP_MAX_DEPTH.
"""

from __future__ import annotations

import bpy
from mathutils import Vector

from .. import properties

_PLANE_NAME: str = "QuadGrab Reference Plane"


class OBJECT_OT_lks_quad_grab_fit_depth(bpy.types.Operator):
    """Set MaxDepth to match the selected objects without moving the plane"""
    bl_idname = "object.lks_quad_grab_fit_depth"
    bl_label = "Fit Depth to Selection"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not context.area or context.area.type != 'VIEW_3D':
            return False
        plane: bpy.types.Object | None = bpy.data.objects.get(_PLANE_NAME)
        if plane is None:
            cls.poll_message_set(
                "No QuadGrab Reference Plane in scene — click 'Make QuadGrab Plane' first")
            return False
        targets: list[bpy.types.Object] = [
            o for o in context.selected_objects if o is not plane
        ]
        if not targets:
            cls.poll_message_set(
                "Select at least one target object (not the plane itself)")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene: bpy.types.Scene = context.scene
        plane: bpy.types.Object = bpy.data.objects.get(_PLANE_NAME)

        rot_mat = plane.matrix_world.to_3x3().normalized()
        rot_mat_inv = rot_mat.inverted()

        # Plane's own position expressed in the rotation frame.
        plane_top_z: float = (rot_mat_inv @ plane.matrix_world.translation).z

        targets: list[bpy.types.Object] = [
            o for o in context.selected_objects if o is not plane
        ]

        local_zs: list[float] = []
        for obj in targets:
            for corner in obj.bound_box:
                world_pt: Vector = obj.matrix_world @ Vector(corner)
                local_zs.append((rot_mat_inv @ world_pt).z)

        if not local_zs:
            self.report({'WARNING'}, "No bounding-box corners found on selected objects")
            return {'CANCELLED'}

        min_z: float = min(local_zs)
        margin: float = getattr(scene, properties.PROP_FIT_MARGIN, 0.0)

        # Depth = distance from the plane surface down to the deepest point +
        # margin on the far end.  We do NOT move the plane so there is no near
        # margin; only the far end is extended.
        depth: float = max(plane_top_z - min_z, 0.001) + margin

        setattr(scene, properties.PROP_MAX_DEPTH, depth)

        self.report(
            {'INFO'},
            f"MaxDepth set to {depth:.3f} m (plane unchanged)",
        )
        return {'FINISHED'}
