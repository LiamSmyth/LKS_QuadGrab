"""Make Plane operator – spawn the QuadGrab reference plane from selection.

Creates a quad plane that covers the bounding box of all selected objects
when viewed from above (along the active object's local +Z axis).

Features
--------
- Plane position / rotation / scale matched to selection bounding box.
- All ray-visibility flags disabled so the plane does not appear in renders.
- ``PROP_MAX_DEPTH`` is auto-set to the depth extent of the selection along
  the plane's local −Z axis.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

from .. import properties


# Name used to identify the reference plane throughout the addon.
_PLANE_NAME: str = "QuadGrab Reference Plane"


class OBJECT_OT_lks_quad_grab_make_plane(bpy.types.Operator):
    """Create a QuadGrab reference plane that covers the selected objects"""
    bl_idname = "object.lks_quad_grab_make_plane"
    bl_label = "Make QuadGrab Plane"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not context.area or context.area.type != 'VIEW_3D':
            return False
        if not context.selected_objects:
            cls.poll_message_set("Select at least one object")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene: bpy.types.Scene = context.scene

        # --- 1. Compute world-space AABB of all selected objects ----------
        ws_min = Vector((math.inf, math.inf, math.inf))
        ws_max = Vector((-math.inf, -math.inf, -math.inf))

        for obj in context.selected_objects:
            for corner in obj.bound_box:
                world_pt: Vector = obj.matrix_world @ Vector(corner)
                ws_min.x = min(ws_min.x, world_pt.x)
                ws_min.y = min(ws_min.y, world_pt.y)
                ws_min.z = min(ws_min.z, world_pt.z)
                ws_max.x = max(ws_max.x, world_pt.x)
                ws_max.y = max(ws_max.y, world_pt.y)
                ws_max.z = max(ws_max.z, world_pt.z)

        centroid: Vector = (ws_min + ws_max) / 2.0
        extents: Vector = ws_max - ws_min

        # --- 2. Create a single-face quad plane ---------------------------
        # Snapshot selection so we can restore it after the plane is created.
        prev_selected: list[str] = [o.name for o in context.selected_objects]
        active_obj: bpy.types.Object | None = context.view_layer.objects.active
        prev_active: str | None = active_obj.name if active_obj is not None else None

        # Remove any existing reference plane, preserving its hide_select state.
        existing = bpy.data.objects.get(_PLANE_NAME)
        prev_hide_select: bool = existing.hide_select if existing is not None else False
        if existing is not None:
            bpy.data.objects.remove(existing, do_unlink=True)

        # Plane size = largest XY extent so it covers the entire footprint.
        plane_size: float = max(extents.x, extents.y, 0.01)

        # Place the plane at the TOP of the bounding box so it sits flush
        # with the uppermost surface; the capture volume then extends downward.
        plane_location: Vector = Vector((centroid.x, centroid.y, ws_max.z))

        bpy.ops.mesh.primitive_plane_add(
            size=plane_size, location=plane_location)
        plane_obj: bpy.types.Object = context.view_layer.objects.active
        plane_obj.name = _PLANE_NAME
        if plane_obj.data:
            plane_obj.data.name = _PLANE_NAME

        # --- 3. Disable all ray visibilities ------------------------------
        # The reference plane should be invisible to the renderer and all
        # ray types so it never contaminates the baked textures.
        plane_obj.visible_camera = False
        plane_obj.visible_diffuse = False
        plane_obj.visible_glossy = False
        plane_obj.visible_transmission = False
        plane_obj.visible_volume_scatter = False
        plane_obj.visible_shadow = False
        # hide_render as well for belt-and-braces safety.
        plane_obj.hide_render = True
        plane_obj.show_wire = True
        plane_obj.display_type = 'WIRE'
        # Persist the selectable state from the previous plane.
        plane_obj.hide_select = prev_hide_select

        # Restore the original selection — deselect the new plane, then
        # re-select everything that was selected before the operation.
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

        # --- 4. Auto-set PROP_MAX_DEPTH to match the selection depth -----
        # Project each bbox corner onto the plane's local −Z axis to find
        # how far the geometry extends below the plane.
        # The plane has no rotation (world Z-up), so "depth" is simply the
        # vertical span: ws_max.z - ws_min.z.
        depth: float = max(extents.z, 0.01)
        # Add a small margin (5 %) so nothing clips right at the boundary.
        depth_with_margin: float = depth * 1.05
        setattr(scene, properties.PROP_MAX_DEPTH, depth_with_margin)

        self.report(
            {'INFO'},
            f"QuadGrab plane created. Max depth auto-set to {depth_with_margin:.3f} m"
        )
        return {'FINISHED'}
