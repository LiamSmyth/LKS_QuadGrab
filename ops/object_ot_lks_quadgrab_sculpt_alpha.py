"""Sculpt Alpha operator – run QuadGrab then load the depth result as the
active sculpt brush alpha texture.

Depth image priority: Z EXR Raw > Z EXR Unitized > Z PNG.
"""

from __future__ import annotations

import os

import bpy

from .. import properties
from ..util.quadgrab_helpers import _rendered_filepath

_PLANE_NAME: str = "QuadGrab Reference Plane"
_TEX_NAME: str = "QG_SculptAlpha"
_BRUSH_NAME: str = "QG_SculptAlpha"


class OBJECT_OT_lks_quad_grab_sculpt_alpha(bpy.types.Operator):
    """Run QuadGrab and load the depth map as the active sculpt brush alpha"""
    bl_idname = "object.lks_quad_grab_sculpt_alpha"
    bl_label = "QuadGrab Sculpt Alpha"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not context.area or context.area.type != 'VIEW_3D':
            return False
        output_dir: str = getattr(
            context.scene, properties.PROP_OUTPUT_DIR, "//quadgrab/")
        if output_dir.startswith("//") and not bpy.data.filepath:
            cls.poll_message_set(
                "Save the .blend file first (output path uses '//' prefix)")
            return False
        has_plane: bool = bpy.data.objects.get(_PLANE_NAME) is not None
        has_mesh_sel: bool = (
            context.active_object is not None
            and context.active_object.type == 'MESH'
        )
        if not has_plane and not has_mesh_sel:
            cls.poll_message_set(
                "Select a mesh object or create a QuadGrab plane first")
            return False
        # At least one depth output must be enabled so we have something to load.
        scene = context.scene
        has_depth: bool = (
            getattr(scene, properties.PROP_USE_DEPTH_EXR_RAW, False)
            or getattr(scene, properties.PROP_USE_DEPTH_EXR, False)
            or getattr(scene, properties.PROP_USE_DEPTH, False)
        )
        if not has_depth:
            cls.poll_message_set(
                "Enable at least one depth output (Z, Z EXR 0-1, or Z EXR Raw) in Grab Options")
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        # Capture state BEFORE QuadGrab changes context (mode transitions,
        # render setup, etc. can leave sculpt.brush as None and the active
        # object pointing at the camera).
        brush_name: str | None = None
        sculpt_pre = context.tool_settings.sculpt
        if sculpt_pre and sculpt_pre.brush:
            brush_name = sculpt_pre.brush.name
        if not brush_name:
            # Fallback: pick the first sculpt-mode brush in the datablock list.
            for b in bpy.data.brushes:
                if b.use_paint_sculpt:
                    brush_name = b.name
                    break

        # Remember the user's mesh so we can enter sculpt mode on it later.
        mesh_obj_name: str | None = None
        if context.active_object and context.active_object.type == 'MESH':
            mesh_obj_name = context.active_object.name

        # Run the full QuadGrab capture.
        result = bpy.ops.object.lks_quad_grab()
        if 'FINISHED' not in result:
            self.report({'ERROR'}, "QuadGrab failed — sculpt alpha not set")
            return {'CANCELLED'}

        scene: bpy.types.Scene = context.scene
        output_dir: str = getattr(scene, properties.PROP_OUTPUT_DIR)
        prefix: str = getattr(scene, properties.PROP_LAST_GRAB_PREFIX, "")

        # Pick the best available depth image (raw EXR → unitized EXR → PNG).
        candidates: list[tuple[str, str]] = []
        if getattr(scene, properties.PROP_USE_DEPTH_EXR_RAW, False):
            candidates.append((prefix + "Depth_Raw", "exr"))
        if getattr(scene, properties.PROP_USE_DEPTH_EXR, False):
            candidates.append((prefix + "Depth_Unitized", "exr"))
        if getattr(scene, properties.PROP_USE_DEPTH, False):
            candidates.append((prefix + "Z", "png"))

        depth_path: str | None = None
        for basename, ext in candidates:
            p: str = _rendered_filepath(output_dir, basename, ext)
            if os.path.exists(p):
                depth_path = p
                break

        if depth_path is None:
            self.report(
                {'WARNING'},
                "QuadGrab succeeded but no depth file was found on disk")
            return {'FINISHED'}

        img_name: str = os.path.basename(depth_path)

        # Always remove any existing image datablock with this name before
        # reloading.  Blender caches image pixel data internally and
        # img.reload() does not always flush that cache for files that were
        # just written to disk.  Removing + loading fresh is the only
        # reliable way to guarantee the new pixels are used.
        existing: bpy.types.Image | None = bpy.data.images.get(img_name)
        if existing is not None:
            # Unlink from any texture that references it to avoid dangling
            # pointers, then remove.
            for tex_block in bpy.data.textures:
                if getattr(tex_block, 'image', None) is existing:
                    tex_block.image = None  # type: ignore[assignment]
            bpy.data.images.remove(existing)

        img: bpy.types.Image = bpy.data.images.load(
            filepath=depth_path, check_existing=False)

        # Depth maps should be read as raw linear data.
        img.colorspace_settings.name = "Non-Color"

        # Recreate the texture each call so we never carry stale settings.
        old_tex: bpy.types.Texture | None = bpy.data.textures.get(_TEX_NAME)
        if old_tex is not None:
            bpy.data.textures.remove(old_tex)
        tex: bpy.types.Texture = bpy.data.textures.new(
            name=_TEX_NAME, type='IMAGE')
        tex.image = img  # type: ignore[union-attr]
        # Clamp so the texture doesn't tile/repeat at the brush boundary.
        if hasattr(tex, 'extension'):
            tex.extension = 'CLIP'
        if hasattr(tex, 'use_interpolation'):
            tex.use_interpolation = True

        # --- Assign to sculpt brush -----------------------------------------
        # Re-fetch the brush by name using the datablock store — this is safe
        # regardless of what mode/context QuadGrab left us in.
        brush: bpy.types.Brush | None = (
            bpy.data.brushes.get(brush_name) if brush_name else None
        )

        if brush is None:
            self.report(
                {'WARNING'},
                f"Depth loaded as '{_TEX_NAME}' — no active sculpt brush found, assign manually")
            return {'FINISHED'}

        # In Blender 5.x the default sculpt brushes are library-linked assets
        # from the essentials asset library.  Linked datablocks are read-only:
        # ``brush.texture = tex`` silently fails (writes None).  To work
        # around this we:
        #   1. Copy the linked brush → local, editable datablock.
        #   2. Assign the texture to the local copy.
        #   3. Mark the copy as a local asset.
        #   4. Activate it via ``bpy.ops.brush.asset_activate`` (the only way
        #      to change the active sculpt brush in 5.x — ``sculpt.brush`` is
        #      read-only).
        # If the brush is already local we can assign directly.

        is_linked: bool = brush.library is not None

        if is_linked:
            # Remove any previous local copy we created so names stay clean.
            prev_local: bpy.types.Brush | None = bpy.data.brushes.get(
                _BRUSH_NAME)
            if prev_local is not None and prev_local.library is None:
                bpy.data.brushes.remove(prev_local)

            local: bpy.types.Brush = brush.copy()
            local.name = _BRUSH_NAME
            brush = local

        brush.texture = tex
        slot: bpy.types.BrushTextureSlot | None = brush.texture_slot
        if slot is not None:
            slot.map_mode = 'VIEW_PLANE'   # standard alpha projection

        if is_linked:
            # Mark as local asset so asset_activate can find it.
            if brush.asset_data is None:
                brush.asset_mark()

            # asset_activate requires Sculpt mode context.  Re-activate the
            # user's original mesh (QuadGrab may have left active on the
            # camera or reference plane).
            obj: bpy.types.Object | None = None
            if mesh_obj_name:
                obj = bpy.data.objects.get(mesh_obj_name)
            if obj is None or obj.type != 'MESH':
                obj = context.active_object
            if obj is None or obj.type != 'MESH':
                for o in context.selected_objects:
                    if o.type == 'MESH':
                        obj = o
                        break
            if obj is None or obj.type != 'MESH':
                for o in bpy.data.objects:
                    if o.type == 'MESH':
                        obj = o
                        break

            if obj is not None and obj.type == 'MESH':
                context.view_layer.objects.active = obj
                prev_mode: str = obj.mode
                if prev_mode != 'SCULPT':
                    bpy.ops.object.mode_set(mode='SCULPT')
                try:
                    bpy.ops.brush.asset_activate(
                        asset_library_type='LOCAL',
                        relative_asset_identifier=f'Brush/{_BRUSH_NAME}',
                    )
                except RuntimeError as exc:
                    self.report(
                        {'WARNING'},
                        f"Brush ready but activation failed: {exc}")
                if prev_mode != 'SCULPT':
                    bpy.ops.object.mode_set(mode=prev_mode)
            else:
                self.report(
                    {'WARNING'},
                    f"Texture '{_TEX_NAME}' ready on brush '{_BRUSH_NAME}' — "
                    "select it manually in Sculpt mode (no mesh to enter sculpt)")
                return {'FINISHED'}

        self.report(
            {'INFO'},
            f"Sculpt alpha set on brush '{brush.name}' from {img_name}",
        )
        return {'FINISHED'}
