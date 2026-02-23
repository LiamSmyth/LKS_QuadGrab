"""Fit to Selection operator – resize QuadGrab plane to cover selected objects.

Reprojects the bounding-box corners of every selected object into the reference
plane's own rotation frame, computes the 2D extents, then rebuilds the plane at
the correct centroid and size while keeping the plane's rotation unchanged.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

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

        # If "From View" is active, override the plane's rotation with the
        # current viewport orientation before computing the fit.  The plane's
        # local −Z then points into the screen so the capture volume faces
        # the camera; bbox projection uses this new frame.
        if getattr(scene, properties.PROP_FIT_FROM_VIEW, False):
            region_3d: bpy.types.RegionView3D | None = getattr(
                context, 'region_data', None)
            if region_3d is None and context.space_data:
                region_3d = getattr(context.space_data, 'region_3d', None)
            if region_3d is not None:
                view_quat: Quaternion = region_3d.view_rotation.copy()
                stored_rotation: Euler = view_quat.to_euler('XYZ')
                # Use the view rotation as the projection frame so the bbox
                # is measured in the same frame we'll rebuild the plane with.
                rot_mat = view_quat.to_matrix().to_3x3()
            else:
                stored_rotation = plane.rotation_euler.copy()
                rot_mat = plane.matrix_world.to_3x3().normalized()
        else:
            # Preserve the plane's current rotation for the rebuilt plane.
            stored_rotation = plane.rotation_euler.copy()
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

        margin: float = getattr(scene, properties.PROP_FIT_MARGIN, 0.0)

        # Plane sits flush with the TOP of the selection, lifted by the margin
        # so there is a visible gap between the mesh surface and the plane.
        local_centroid: Vector = Vector(
            ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, max_z + margin)
        )
        world_centroid: Vector = rot_mat @ local_centroid

        # Size: largest of X/Y extents expanded by margin on every side.
        extent_x: float = max_x - min_x
        extent_y: float = max_y - min_y
        new_size: float = max(extent_x, extent_y, 0.01) + 2.0 * margin

        # Depth: full Z extent + margin at both ends (near lift already done
        # by shifting the centroid up; add margin again for the far end).
        depth: float = max(max_z - min_z, 0.01) + 2.0 * margin

        # Snapshot selection so we can restore it after the plane rebuild.
        prev_selected: list[str] = [
            o.name for o in context.selected_objects if o is not plane
        ]
        active_obj: bpy.types.Object | None = context.view_layer.objects.active
        prev_active: str | None = (
            active_obj.name if active_obj is not None and active_obj is not plane else None
        )

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
        plane_obj.show_wire = True

        # Restore the original selection — deselect the new plane, re-select
        # everything that was selected before the operation.
        plane_obj.select_set(False)
        for name in prev_selected:
            obj = bpy.data.objects.get(name)
            if obj is not None:
                obj.select_set(True)
        if prev_active is not None:
            restored: bpy.types.Object | None = bpy.data.objects.get(
                prev_active)
            if restored is not None:
                context.view_layer.objects.active = restored

        setattr(scene, properties.PROP_MAX_DEPTH, depth)

        self.report(
            {'INFO'},
            f"Plane fitted — size {new_size:.3f} m, MaxDepth auto-set to {depth:.3f} m",
        )
        return {'FINISHED'}
