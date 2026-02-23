"""Restore / Cleanup operator – undo QuadGrab scene changes (debug / manual workflow)."""

from __future__ import annotations

import json

import bpy
from .. import properties
from ..util.quadgrab_helpers import _QG_NODE_PREFIX
from ..util.scene_setup import restore_quadgrab


class OBJECT_OT_lks_quad_grab_restore(bpy.types.Operator):
    """Restore scene settings and clean up QuadGrab compositor/AOV setup"""
    bl_idname = "object.lks_quad_grab_restore"
    bl_label = "Cleanup QuadGrab"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene: bpy.types.Scene = context.scene
        vl: bpy.types.ViewLayer = context.view_layer

        # Read cache written by Setup (or empty if Setup was never run).
        cached: str = getattr(scene, properties.PROP_CACHED_SETTINGS, "")
        cache: dict[str, object] = json.loads(cached) if cached else {}

        # Restore render settings + remove QG_ compositor/AOV/material nodes.
        restore_quadgrab(scene, vl, cache)
        if cache:
            setattr(scene, properties.PROP_CACHED_SETTINGS, "")

        # Remove QuadGrab objects, textures, images, and any QG_ materials.
        for obj in list(bpy.data.objects):
            if "QuadGrab" in obj.name:
                bpy.data.objects.remove(obj, do_unlink=True)

        for texture in list(bpy.data.textures):
            if "QuadGrab" in texture.name:
                bpy.data.textures.remove(texture, do_unlink=True)

        for image in list(bpy.data.images):
            if "QuadGrab" in image.name:
                bpy.data.images.remove(image, do_unlink=True)

        for mat in list(bpy.data.materials):
            if mat.library is not None:
                continue  # linked — skip
            if "QG_" in mat.name:
                bpy.data.materials.remove(mat, do_unlink=True)

        for s in list(bpy.data.scenes):
            if "quadgrab" in s.name:
                bpy.data.scenes.remove(s, do_unlink=True)

        bpy.ops.outliner.orphans_purge(do_recursive=True)

        self.report({'INFO'}, "QuadGrab cleanup complete")
        return {'FINISHED'}
