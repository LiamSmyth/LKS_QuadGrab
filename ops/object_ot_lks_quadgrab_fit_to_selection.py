"""Fit to Selection operator – resize QuadGrab plane to cover selected objects.

Reprojects the bounding-box corners of every selected object into the reference
plane's own rotation frame, computes the 2D extents, then rebuilds the plane at
the correct centroid and size while keeping the plane's rotation unchanged.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

from .. import properties

_PLANE_NAME: str = "QuadGrab Reference Plane"


class OBJECT_OT_lks_quad_grab_fit_to_selection(bpy.types.Operator):
    """Resize the QuadGrab Reference Plane to cover all selected objects"""
    bl_idname = "object.lks_quad_grab_fit_to_selection"
    bl_label = "Fit Plane to Selection"
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

        # Preserve the plane's current rotation for the rebuilt plane.
        stored_rotation: bpy.types.Euler = plane.rotation_euler.copy()

        # Rotation-only matrix of the plane (strips scale + translation).
        rot_mat = plane.matrix_world.to_3x3().normalized()
        rot_mat_inv = rot_mat.inverted()

        # Project every selected (non-plane) object's bbox corners into the
        # plane's rotation frame so we can compute the 2D footprint on the
        # plane regardless of the plane's world-space orientation.
        targets: list[bpy.types.Object] = [
            o for o in context.selected_objects if o is not plane
        ]

        local_xs: list[float] = []
        local_ys: list[float] = []
        local_zs: list[float] = []

        for obj in targets:
            for corner in obj.bound_box:
                world_pt: Vector = obj.matrix_world @ Vector(corner)
                local_pt: Vector = rot_mat_inv @ world_pt
                local_xs.append(local_pt.x)
                local_ys.append(local_pt.y)
                local_zs.append(local_pt.z)

        if not local_xs:
            self.report(
                {'WARNING'}, "No bounding-box corners found on selected objects")
            return {'CANCELLED'}

        min_x, max_x = min(local_xs), max(local_xs)
        min_y, max_y = min(local_ys), max(local_ys)
        min_z, max_z = min(local_zs), max(local_zs)

        # Plane sits flush with the TOP of the selection (max local Z).
        local_centroid: Vector = Vector(
            ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, max_z)
        )
        world_centroid: Vector = rot_mat @ local_centroid

        # Size: largest of X/Y extents + 5 % margin so nothing clips the edge.
        extent_x: float = max_x - min_x
        extent_y: float = max_y - min_y
        new_size: float = max(extent_x, extent_y, 0.01) * 1.05

        # Depth: full Z extent of the selection + 5 % margin.
        depth: float = max(max_z - min_z, 0.01) * 1.05

        # Remove the old plane and recreate with the new size / position,
        # keeping the stored rotation.
        bpy.data.objects.remove(plane, do_unlink=True)

        bpy.ops.mesh.primitive_plane_add(
            size=new_size,
            location=world_centroid,
            rotation=stored_rotation,
        )
        plane_obj: bpy.types.Object = context.view_layer.objects.active
        plane_obj.name = _PLANE_NAME
        if plane_obj.data:
            plane_obj.data.name = _PLANE_NAME

        # Disable all ray visibilities so the plane never appears in renders.
        plane_obj.visible_camera = False
        plane_obj.visible_diffuse = False
        plane_obj.visible_glossy = False
        plane_obj.visible_transmission = False
        plane_obj.visible_volume_scatter = False
        plane_obj.visible_shadow = False
        plane_obj.hide_render = True

        setattr(scene, properties.PROP_MAX_DEPTH, depth)

        self.report(
            {'INFO'},
            f"Plane fitted — size {new_size:.3f} m, MaxDepth auto-set to {depth:.3f} m",
        )
        return {'FINISHED'}
