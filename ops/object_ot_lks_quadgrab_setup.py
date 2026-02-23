"""Setup operator – configure scene for QuadGrab capture (debug / manual workflow)."""

from __future__ import annotations

import json
import time

import bpy
from .. import properties
from ..util.scene_setup import apply_quadgrab_setup


class OBJECT_OT_lks_quad_grab_setup(bpy.types.Operator):
    """Configure scene, materials, AOVs, and compositor for QuadGrab"""
    bl_idname = "object.lks_quad_grab_setup"
    bl_label = "Setup QuadGrab"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene: bpy.types.Scene = context.scene
        vl: bpy.types.ViewLayer = context.view_layer

        timestamp: str = ""
        if getattr(scene, properties.PROP_USE_TIMESTAMP):
            timestamp = time.strftime("%H-%M-%S") + "_"

        cache, skipped_linked = apply_quadgrab_setup(scene, vl, timestamp)

        # Persist the cache so the Cleanup operator can restore original settings.
        setattr(scene, properties.PROP_CACHED_SETTINGS, json.dumps(cache))

        if skipped_linked > 0:
            self.report(
                {'WARNING'},
                f"Skipped {skipped_linked} linked material(s) — AOVs cannot be added to linked assets",
            )

        self.report(
            {'INFO'}, "QuadGrab setup complete (settings cached, compositor built)")
        return {'FINISHED'}
