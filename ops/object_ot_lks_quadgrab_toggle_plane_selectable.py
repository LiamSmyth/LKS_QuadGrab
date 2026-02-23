"""Toggle Plane Selectable operator – flip hide_select on the reference plane."""

from __future__ import annotations

import bpy

_PLANE_NAME: str = "QuadGrab Reference Plane"


class OBJECT_OT_lks_quad_grab_toggle_plane_selectable(bpy.types.Operator):
    """Toggle whether the QuadGrab Reference Plane can be selected in the viewport"""
    bl_idname = "object.lks_quad_grab_toggle_plane_selectable"
    bl_label = "Toggle Plane Selectable"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bpy.data.objects.get(_PLANE_NAME) is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        plane: bpy.types.Object | None = bpy.data.objects.get(_PLANE_NAME)
        if plane is None:
            self.report({'WARNING'}, "QuadGrab Reference Plane not found")
            return {'CANCELLED'}
        plane.hide_select = not plane.hide_select
        state: str = "not selectable" if plane.hide_select else "selectable"
        self.report({'INFO'}, f"QuadGrab Reference Plane is now {state}")
        return {'FINISHED'}
