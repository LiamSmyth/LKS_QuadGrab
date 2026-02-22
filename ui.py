import mathutils
import math
import sys
import pathlib
import os
import bpy
import types

from . import properties
from . import operators


class VIEW3D_PT_LKS_QuadGrab(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LKS'
    bl_label = 'LKS QuadGrab'

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        col: bpy.types.UILayout = layout.column(align=True)
        row = col.row()
        row.prop(context.scene, properties.PROP_OUTPUT_DIR)
        row.prop(context.scene, properties.PROP_USE_TIMESTAMP)
        row.prop(context.scene, properties.PROP_USE_DEBUG)
        row = col.row()
        row.prop(context.scene, properties.PROP_MAX_DEPTH)
        row.prop(context.scene, properties.PROP_RENDER_SIZE)
        row = col.row()
        row.prop(context.scene, properties.PROP_USE_PREVIEW_PLANE)
        row.prop(context.scene, properties.PROP_DISPLACE_PLANE)

        row = col.row()
        row.prop(context.scene, properties.PROP_USE_DEPTH, text="Z")
        row.prop(context.scene, properties.PROP_USE_DEPTH_EXR, text="Z EXR")
        row.prop(context.scene, properties.PROP_USE_COMPOSITE)
        row.prop(context.scene, properties.PROP_USE_PBR)

        col.operator(operators.OBJECT_OT_LKS_QuadGrabMakePlane.bl_idname,
                     text="Make QuadGrab Plane")
        col.operator(operators.OBJECT_OT_LKS_QuadGrab.bl_idname,
                     text="QuadGrab")
        col.operator(operators.OBJECT_OT_LKS_QuadGrabCleanup.bl_idname,
                     text="Cleanup QuadGrab Objects")


def register() -> None:
    bpy.utils.register_class(VIEW3D_PT_LKS_QuadGrab)


def unregister() -> None:
    bpy.utils.unregister_class(VIEW3D_PT_LKS_QuadGrab)
