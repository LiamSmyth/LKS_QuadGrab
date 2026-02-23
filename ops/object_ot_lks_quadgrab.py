"""Main QuadGrab render operator – atomic setup → render → restore."""

from __future__ import annotations

import math
import os
import time

import bpy
import mathutils
from mathutils import Vector

from .. import properties
from ..util.quadgrab_helpers import CLIP_START, _rendered_filepath
from ..util.scene_setup import apply_quadgrab_setup, restore_quadgrab


class OBJECT_OT_lks_quad_grab(bpy.types.Operator):
    """QuadGrab!"""
    bl_idname = "object.lks_quad_grab"
    bl_label = "LKS QuadGrab"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not context.area or context.area.type != 'VIEW_3D':
            return False
        # Output-path issue is the only thing we can't fix atomically.
        output_dir: str = getattr(
            context.scene, properties.PROP_OUTPUT_DIR, "//quadgrab/")
        if output_dir.startswith("//") and not bpy.data.filepath:
            cls.poll_message_set(
                "Save the .blend file first (output path uses '//' prefix)")
            return False
        has_plane: bool = bpy.data.objects.get(
            "QuadGrab Reference Plane") is not None
        has_mesh_sel: bool = (
            context.active_object is not None
            and context.active_object.type == 'MESH'
        )
        if not has_plane and not has_mesh_sel:
            cls.poll_message_set(
                "Select a mesh object (plane will be auto-created) or click 'Make QuadGrab Plane'"
            )
            return False
        return True

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene: bpy.types.Scene = context.scene
        vl: bpy.types.ViewLayer = context.view_layer

        # Snapshot selection so we can restore it after the render completes.
        prev_selected: list[str] = [o.name for o in context.selected_objects]
        _prev_active_obj: bpy.types.Object | None = context.view_layer.objects.active
        prev_active: str | None = (
            _prev_active_obj.name if _prev_active_obj is not None else None
        )

        timestamp: str = ""
        if getattr(scene, properties.PROP_USE_TIMESTAMP):
            timestamp = time.strftime("%H-%M-%S") + "_"
        # Prepend the user-supplied name prefix so files are overwritten
        # predictably until the name is explicitly changed.
        output_name: str = getattr(
            scene, properties.PROP_OUTPUT_NAME, "").strip()
        if output_name:
            timestamp = output_name + "_" + timestamp

        # --- Resolve the QuadGrab Reference Plane -----------------------
        # If no plane exists yet but a mesh is selected, auto-spawn it now.
        ref_obj: bpy.types.Object | None = bpy.data.objects.get(
            "QuadGrab Reference Plane")
        if ref_obj is None:
            result = bpy.ops.object.lks_quad_grab_make_plane()
            if 'CANCELLED' in result:
                self.report(
                    {'ERROR'}, "Failed to create QuadGrab Reference Plane")
                return {'CANCELLED'}
            ref_obj = bpy.data.objects.get("QuadGrab Reference Plane")
        if ref_obj is None:
            self.report(
                {'ERROR'}, "QuadGrab Reference Plane not found after creation")
            return {'CANCELLED'}

        def make_camera_and_set_xform(obj: bpy.types.Object) -> bpy.types.Object:
            """Create an ortho camera matching *obj*'s world-space footprint.

            Uses ``obj.matrix_world`` so that location, rotation **and scale**
            are all accounted for.
            """
            # Measure extents in the plane's LOCAL axes (× object scale) so
            # that the ortho_scale equals the plane's actual dimensions.
            # Using the world-space AABB here would be wrong: a rotated
            # plane's AABB is always larger than the plane itself, which
            # would make the camera see more than the plane and cause the
            # rendered content to appear zoomed-out / preview plane smaller.
            local_corners = [Vector(c) for c in obj.bound_box]
            obj_scale: Vector = obj.matrix_world.to_scale()
            extent_local_x: float = (
                max(c.x for c in local_corners) -
                min(c.x for c in local_corners)
            ) * abs(obj_scale.x)
            extent_local_y: float = (
                max(c.y for c in local_corners) -
                min(c.y for c in local_corners)
            ) * abs(obj_scale.y)

            # Camera origin = the plane's world-space pivot exactly.
            # No clip buffer is added here; the fit margin on the plane
            # extends the capture volume past the mesh on all sides so
            # no geometry is clipped by the near plane.
            centroid: Vector = obj.matrix_world.translation.copy()

            cam: bpy.types.Camera = bpy.data.cameras.new(
                name="LKS QuadGrab Cam")
            cam_obj: bpy.types.Object = bpy.data.objects.new(
                "LKS QuadGrab Cam Obj", cam)
            cam.ortho_scale = max(extent_local_x, extent_local_y, 0.01)
            cam.type = 'ORTHO'
            cam_obj.location = centroid
            cam_obj.rotation_euler = obj.rotation_euler
            scene.collection.objects.link(cam_obj)
            return cam_obj

        # ----------------------------------------------------------------
        # Camera
        # ----------------------------------------------------------------
        cam_obj: bpy.types.Object = make_camera_and_set_xform(ref_obj)
        cam: bpy.types.Camera = cam_obj.data
        cam.clip_start = CLIP_START
        cam.clip_end = getattr(scene, properties.PROP_MAX_DEPTH)

        # Snapshot resolution so we can restore it after rendering.
        prev_res_x: int = scene.render.resolution_x
        prev_res_y: int = scene.render.resolution_y
        prev_res_pct: int = scene.render.resolution_percentage
        render_size: int = getattr(scene, properties.PROP_RENDER_SIZE)
        scene.render.resolution_x = render_size
        scene.render.resolution_y = render_size
        scene.render.resolution_percentage = 100
        scene.camera = cam_obj
        ref_obj.hide_render = True

        # Snapshot plain-Python values now, before the finally block may
        # remove cam_obj/cam.  add_preview_plane() runs after the finally
        # block and must not touch a freed StructRNA pointer.
        cam_location_snap = cam_obj.location.copy()
        cam_rotation_snap = cam_obj.rotation_euler.copy()
        cam_ortho_scale_snap: float = cam.ortho_scale

        # ----------------------------------------------------------------
        # Atomic: setup → render → restore (restore guaranteed by finally)
        # ----------------------------------------------------------------
        cache: dict[str, object] = {}
        skipped_linked: int = 0
        try:
            cache, skipped_linked = apply_quadgrab_setup(scene, vl, timestamp)
            scene.frame_set(0)
            bpy.ops.render.render()
        finally:
            ref_obj.hide_render = False
            restore_quadgrab(scene, vl, cache)
            scene.render.resolution_x = prev_res_x
            scene.render.resolution_y = prev_res_y
            scene.render.resolution_percentage = prev_res_pct
            debug: bool = getattr(scene, properties.PROP_USE_DEBUG)
            if not debug:
                bpy.data.objects.remove(cam_obj)
                bpy.data.cameras.remove(cam)

        if skipped_linked > 0:
            self.report(
                {'WARNING'},
                f"Skipped {skipped_linked} linked material(s) — AOV data may be incomplete for those objects",
            )

        # ----------------------------------------------------------------
        # Write metadata file alongside the renders
        # ----------------------------------------------------------------
        _max_depth: float = getattr(scene, properties.PROP_MAX_DEPTH)
        _midpoint: float = getattr(scene, properties.PROP_DEPTH_MIDPOINT, 0.0)
        _output_dir: str = getattr(scene, properties.PROP_OUTPUT_DIR)
        _abs_dir: str = bpy.path.abspath(_output_dir)
        os.makedirs(_abs_dir, exist_ok=True)
        # EXR Raw: surface pixels carry +midpoint×max_depth after the ADD shift.
        _exr_surface: float = _midpoint * _max_depth
        # cm conversions for human-readable output.
        _max_depth_cm: float = _max_depth * 100.0
        _mid_depth_cm: float = _midpoint * _max_depth_cm
        _post_mid_cm: float = (1.0 - _midpoint) * _max_depth_cm
        _cap_width_cm: float = cam_ortho_scale_snap * 100.0
        _meta_path: str = os.path.join(_abs_dir, timestamp + "metadata.txt")
        _meta_lines: list[str] = [
            "QuadGrab Capture Metadata",
            "=========================",
            "",
            f"Capture Width:         {_cap_width_cm:.2f} cm",
            f"Total Depth:           {_max_depth_cm:.2f} cm",
        ]
        if getattr(scene, properties.PROP_USE_DEPTH_EXR_RAW):
            _meta_lines += [
                "",
                "EXR Depth_Raw",
                "  Values are relative to the min depth (capture plane surface).",
                "",
                f"  Unitized Midpoint:   {_midpoint:.4f}",
                f"  Midpoint Depth:      {_mid_depth_cm:.2f} cm",
                f"  Total Depth:         {_max_depth_cm:.2f} cm",
                f"  Midpoint To Max:     {_post_mid_cm:.2f} cm",
                "",
                "  Blender Displace modifier (match source geometry):",
                f"    mid_level:         {_exr_surface:.6f}",
                f"    strength:          1.0",
                f"    axis:              Z (local)",
            ]
        if getattr(scene, properties.PROP_USE_DEPTH_EXR):
            _meta_lines += [
                "",
                "EXR Depth_Unitized",
                "  Unitized (0-1) values across the captured depth range.",
                "",
                f"  Total Depth:         {_max_depth_cm:.2f} cm",
                f"  Scale Factor:        {_max_depth:.6f}  (multiply to restore scene-unit values)",
                f"  Unitized Midpoint:   {_midpoint:.4f}",
                f"  Midpoint Depth:      {_mid_depth_cm:.2f} cm",
                "",
                "  Blender Displace modifier (match source geometry):",
                f"    mid_level:         {_midpoint:.6f}",
                f"    strength:          {_max_depth:.6f}",
                f"    axis:              Z (local)",
            ]
        if getattr(scene, properties.PROP_USE_DEPTH):
            _meta_lines += [
                "",
                "PNG Depth_Unitized",
                "  Unitized (0-1) values across the captured depth range.",
                "",
                f"  Total Depth:         {_max_depth_cm:.2f} cm",
                f"  Scale Factor:        {_max_depth:.6f}  (multiply to restore scene-unit values)",
                f"  Unitized Midpoint:   {_midpoint:.4f}",
                f"  Midpoint Depth:      {_mid_depth_cm:.2f} cm",
            ]
        try:
            with open(_meta_path, "w", encoding="utf-8") as _mf:
                _mf.write("\n".join(_meta_lines) + "\n")
        except OSError as _exc:
            self.report(
                {'WARNING'}, f"QuadGrab: could not write metadata: {_exc}")

        # ----------------------------------------------------------------
        # Post-render: optional preview plane + material
        # ----------------------------------------------------------------
        def add_preview_plane() -> bpy.types.Object:
            bpy.ops.mesh.primitive_grid_add(
                location=cam_location_snap, rotation=cam_rotation_snap, size=cam_ortho_scale_snap)
            ob_grid: bpy.types.Object = bpy.context.view_layer.objects.active
            ob_grid.hide_render = True
            if hasattr(ob_grid, 'display'):
                ob_grid.display.show_shadows = False
            ob_grid.name = "QuadGrab Preview Plane"
            bpy.ops.object.shade_smooth()
            ob_mesh: bpy.types.Mesh = ob_grid.data
            if hasattr(ob_mesh, "use_auto_smooth"):
                ob_mesh.use_auto_smooth = True
                ob_mesh.auto_smooth_angle = math.pi

            if getattr(scene, properties.PROP_DISPLACE_PLANE):
                subsurf: bpy.types.SubsurfModifier = ob_grid.modifiers.new(
                    type="SUBSURF", name="QuadGrab_Subsurf")
                subsurf.subdivision_type = "SIMPLE"
                subsurf.levels = 4
                subsurf.quality = 1
                if hasattr(ob_grid.cycles, 'use_adaptive_subdivision'):
                    ob_grid.cycles.use_adaptive_subdivision = True

                if getattr(scene, properties.PROP_USE_DEPTH_EXR_RAW):
                    displace: bpy.types.DisplaceModifier = ob_grid.modifiers.new(
                        type="DISPLACE", name="QuadGrab_Displace")
                    # Calibrate mid_level so that EXR surface pixels
                    # produce exactly zero displacement on the preview plane
                    # (pivot = camera position = surface zero).
                    # With midpoint=0 → shift=0 → surface EXR value=0 → mid_level=0.
                    # With midpoint>0 → surface EXR value=midpoint×max_depth → mid_level=same.
                    _disp_max_depth: float = getattr(
                        scene, properties.PROP_MAX_DEPTH)
                    _disp_midpoint: float = getattr(
                        scene, properties.PROP_DEPTH_MIDPOINT, 0.0)
                    displace.mid_level = _disp_midpoint * _disp_max_depth
                    displace.strength = 1
                    displace.texture_coords = "UV"
                    disp_tex: bpy.types.ImageTexture = bpy.data.textures.new(
                        name="QuadGrab_DispTex", type="IMAGE")
                    if hasattr(disp_tex, "use_clamp"):
                        disp_tex.use_clamp = False
                    elif hasattr(disp_tex, "extension"):
                        disp_tex.extension = 'EXTEND'
                    disp_img: bpy.types.Image = bpy.data.images.load(
                        filepath=_rendered_filepath(
                            getattr(scene, properties.PROP_OUTPUT_DIR),
                            timestamp + "Depth_Raw", "exr"))
                    displace.texture = disp_tex
                    disp_tex.image = disp_img

            ob_grid.select_set(False)
            ref_obj.select_set(True)
            bpy.context.view_layer.objects.active = ref_obj
            return ob_grid

        def add_preview_mat() -> bpy.types.Material:
            mat = bpy.data.materials.new(name=timestamp + "QG_Preview_Mat")
            mat.use_nodes = True
            nt: bpy.types.NodeTree = mat.node_tree
            shader: bpy.types.ShaderNodeBsdfPrincipled = mat.node_tree.nodes["Principled BSDF"]

            output_dir: str = getattr(scene, properties.PROP_OUTPUT_DIR)
            # BaseColor
            img_basecolor: bpy.types.Image = bpy.data.images.load(
                filepath=_rendered_filepath(output_dir, timestamp + "BaseColor_srgb", "png"))
            n_img_basecolor: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_basecolor.name = "QG_BaseColor"
            n_img_basecolor.location = [-800, 0]
            n_img_basecolor.image = img_basecolor
            nt.links.new(
                input=shader.inputs["Base Color"], output=n_img_basecolor.outputs[0])
            # Normal
            img_normal: bpy.types.Image = bpy.data.images.load(
                filepath=_rendered_filepath(output_dir, timestamp + "Normal", "png"))
            n_img_normal: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_normal.name = "QG_Normal"
            n_img_normal.location = [-800, -400]
            n_img_normal.image = img_normal
            n_img_normal.image.colorspace_settings.name = "Non-Color"
            n_normal: bpy.types.ShaderNodeNormalMap = nt.nodes.new(
                type="ShaderNodeNormalMap")
            n_normal.location = [-500, -400]
            nt.links.new(
                input=n_normal.inputs[1], output=n_img_normal.outputs[0])
            nt.links.new(
                input=shader.inputs["Normal"], output=n_normal.outputs[0])
            # Roughness
            img_roughness: bpy.types.Image = bpy.data.images.load(
                filepath=_rendered_filepath(output_dir, timestamp + "Roughness", "png"))
            n_img_roughness: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_roughness.name = "QG_Roughness"
            n_img_roughness.location = [-800, -800]
            n_img_roughness.image = img_roughness
            n_img_roughness.image.colorspace_settings.name = "Non-Color"
            nt.links.new(
                input=shader.inputs["Roughness"], output=n_img_roughness.outputs[0])
            # Metallic
            img_metallic: bpy.types.Image = bpy.data.images.load(
                filepath=_rendered_filepath(output_dir, timestamp + "Metallic", "png"))
            n_img_metallic: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_metallic.name = "QG_Metallic"
            n_img_metallic.location = [-800, -1200]
            n_img_metallic.image = img_metallic
            n_img_metallic.image.colorspace_settings.name = "Non-Color"
            nt.links.new(
                input=shader.inputs["Metallic"], output=n_img_metallic.outputs[0])
            # Specular
            img_specular: bpy.types.Image = bpy.data.images.load(
                filepath=_rendered_filepath(output_dir, timestamp + "Specular", "png"))
            n_img_specular: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_specular.name = "QG_Specular"
            n_img_specular.location = [-800, -1600]
            n_img_specular.image = img_specular
            n_img_specular.image.colorspace_settings.name = "Non-Color"
            spec_socket = shader.inputs.get(
                "Specular IOR Level") or shader.inputs.get("Specular")
            if spec_socket:
                nt.links.new(input=spec_socket,
                             output=n_img_specular.outputs[0])
            # Alpha
            if hasattr(mat, "show_transparent_back"):
                mat.show_transparent_back = False
            if hasattr(mat, "blend_method"):
                mat.blend_method = "CLIP"
            img_alpha: bpy.types.Image = bpy.data.images.load(
                filepath=_rendered_filepath(output_dir, timestamp + "Alpha", "png"))
            n_img_alpha: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_alpha.name = "QG_Alpha"
            n_img_alpha.location = [-800, -2000]
            n_img_alpha.image = img_alpha
            n_img_alpha.image.colorspace_settings.name = "Non-Color"
            nt.links.new(
                input=shader.inputs["Alpha"], output=n_img_alpha.outputs[0])
            return mat

        if getattr(scene, properties.PROP_USE_PREVIEW_PLANE):
            preview_plane: bpy.types.Object = add_preview_plane()
            if getattr(scene, properties.PROP_USE_PBR):
                preview_mat: bpy.types.Material = add_preview_mat()
                preview_plane.active_material = preview_mat

        # Restore the selection that was active when the user clicked QuadGrab.
        for obj in list(context.selected_objects):
            obj.select_set(False)
        for name in prev_selected:
            obj = bpy.data.objects.get(name)
            if obj is not None:
                obj.select_set(True)
        if prev_active is not None:
            restored: bpy.types.Object | None = bpy.data.objects.get(
                prev_active)
            if restored is not None:
                context.view_layer.objects.active = restored

        return {'FINISHED'}
