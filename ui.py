import bpy

from . import properties
from . import ops as operators


class VIEW3D_PT_lks_quad_grab(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LKS'
    bl_label = 'LKS QuadGrab'

    def _section(self, parent: bpy.types.UILayout, scene: bpy.types.Scene,
                 prop_name: str, label: str, icon: str
                 ) -> tuple[bpy.types.UILayout, bool]:
        """Draw a collapsible box section.  Returns (box, is_expanded)."""
        expanded: bool = getattr(scene, prop_name, True)
        box: bpy.types.UILayout = parent.box()
        row: bpy.types.UILayout = box.row()
        row.prop(scene, prop_name,
                 icon='TRIA_DOWN' if expanded else 'TRIA_RIGHT',
                 icon_only=True, emboss=False)
        row.label(text=label, icon=icon)
        return box, expanded

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene: bpy.types.Scene = context.scene

        # ── Main actions ─────────────────────────────────────────────────
        col: bpy.types.UILayout = layout.column(align=True)

        output_dir: str = getattr(
            scene, properties.PROP_OUTPUT_DIR, "//quadgrab/")
        path_bad: bool = output_dir.startswith("//") and not bpy.data.filepath
        has_plane: bool = bpy.data.objects.get(
            "QuadGrab Reference Plane") is not None
        has_mesh_sel: bool = (
            context.active_object is not None
            and context.active_object.type == 'MESH'
        )
        no_target: bool = not has_plane and not has_mesh_sel

        row_qg = col.row(align=True)
        row_qg.scale_y = 1.6
        row_qg.enabled = not path_bad and not no_target
        row_qg.operator(operators.OBJECT_OT_lks_quad_grab.bl_idname,
                        text="QuadGrab!", icon='RENDER_STILL')
        row_qg.operator(
            operators.OBJECT_OT_lks_quad_grab_sculpt_alpha.bl_idname,
            text="", icon='SCULPTMODE_HLT')

        if path_bad:
            box: bpy.types.UILayout = col.box()
            box.label(text="Save the .blend file first", icon='ERROR')
            box.label(text="(output path uses '//' prefix)", icon='BLANK1')
        elif no_target:
            box = col.box()
            box.label(
                text="Select a mesh or create a QuadGrab plane", icon='INFO')

        col.separator(factor=0.5)
        row_plane = col.row(align=True)
        row_plane.operator(
            operators.OBJECT_OT_lks_quad_grab_make_plane.bl_idname,
            text="Make QuadGrab Plane", icon='MESH_PLANE')
        row_plane.prop(scene, properties.PROP_FIT_FROM_VIEW,
                       text="", icon='HIDE_OFF', toggle=True)
        row_plane.operator(
            operators.OBJECT_OT_lks_quad_grab_fit_to_selection.bl_idname,
            text="Fit to Selection", icon='FULLSCREEN_ENTER')
        row_margin = col.row(align=True)
        row_margin.prop(scene, properties.PROP_FIT_MARGIN)
        _plane_obj: bpy.types.Object | None = bpy.data.objects.get(
            "QuadGrab Reference Plane")
        if _plane_obj is not None:
            row_plane.operator(
                operators.OBJECT_OT_lks_quad_grab_fit_depth.bl_idname,
                text="", icon='DRIVER_DISTANCE')
            _sel_icon: str = (
                'RESTRICT_SELECT_ON' if _plane_obj.hide_select
                else 'RESTRICT_SELECT_OFF'
            )
            row_plane.operator(
                operators.OBJECT_OT_lks_quad_grab_toggle_plane_selectable.bl_idname,
                text="", icon=_sel_icon)

        # ── Output Settings (default open) ───────────────────────────────
        col.separator(factor=0.5)
        out_box, out_open = self._section(
            col, scene, properties.PROP_OUTPUT_EXPANDED,
            "Output Settings", 'OUTPUT')
        if out_open:
            out_box.prop(scene, properties.PROP_OUTPUT_DIR, text="")
            row = out_box.row(align=True)
            row.prop(scene, properties.PROP_OUTPUT_NAME, text="Name")
            row.prop(scene, properties.PROP_USE_TIMESTAMP, toggle=True)
            row = out_box.row(align=True)
            row.prop(scene, properties.PROP_RENDER_SIZE)
            row.prop(scene, properties.PROP_MAX_DEPTH)

        # ── Grab Options (default open) ──────────────────────────────────
        grab_box, grab_open = self._section(
            col, scene, properties.PROP_GRAB_EXPANDED,
            "Grab Options", 'CAMERA_DATA')
        if grab_open:
            row = grab_box.row(align=True)
            row.prop(scene, properties.PROP_USE_DEPTH, text="Z", toggle=True)
            row.prop(scene, properties.PROP_USE_DEPTH_EXR,
                     text="Z EXR 0-1", toggle=True)
            row.prop(scene, properties.PROP_USE_DEPTH_EXR_RAW,
                     text="Z EXR Raw", toggle=True)
            row.prop(scene, properties.PROP_USE_COMPOSITE,
                     text="Composite", toggle=True)
            row.prop(scene, properties.PROP_USE_PBR, text="PBR", toggle=True)
            grab_box.prop(scene, properties.PROP_DEPTH_MIDPOINT, slider=True)

        # ── Preview Options (default closed) ─────────────────────────────
        prev_box, prev_open = self._section(
            col, scene, properties.PROP_PREVIEW_EXPANDED,
            "Preview Options", 'HIDE_OFF')
        if prev_open:
            row = prev_box.row(align=True)
            row.prop(scene, properties.PROP_USE_PREVIEW_PLANE, toggle=True)
            row.prop(scene, properties.PROP_DISPLACE_PLANE, toggle=True)
            prev_box.prop(scene, properties.PROP_SHOW_OVERLAY,
                          text="Show Capture Volume", icon='OVERLAY')

        # ── Debug (default closed) ───────────────────────────────────────
        dbg_box, dbg_open = self._section(
            col, scene, properties.PROP_DEBUG_EXPANDED, "Debug", 'TOOL_SETTINGS')
        if dbg_open:
            row_ops = dbg_box.row(align=True)
            row_ops.operator(
                operators.OBJECT_OT_lks_quad_grab_setup.bl_idname,
                text="Setup", icon='PREFERENCES')
            row_ops.operator(
                operators.OBJECT_OT_lks_quad_grab_restore.bl_idname,
                text="Cleanup", icon='TRASH')
            dbg_box.prop(scene, properties.PROP_USE_DEBUG, toggle=True)


def register() -> None:
    bpy.utils.register_class(VIEW3D_PT_lks_quad_grab)


def unregister() -> None:
    bpy.utils.unregister_class(VIEW3D_PT_lks_quad_grab)
