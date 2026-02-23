"""Shared constants and helper functions used across QuadGrab operators."""

from __future__ import annotations

import os

import bpy

from .. import properties

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Near-clip for the ortho capture camera.  Kept at the Blender-safe minimum
# so there is effectively no clip buffer — the fit margin on the plane itself
# provides all the visible overlap needed.
CLIP_START: float = 0.001

# Blender 5.0+ File Output nodes use ``file_name`` + ``file_output_items``
# and do NOT append a frame-number suffix.  4.x uses ``base_path`` +
# ``file_slots`` and DOES append a 4-digit frame number.
_USE_NEW_FILE_OUTPUT: bool = bpy.app.version >= (5, 0, 0)

# Prefix applied to every compositor node created by QuadGrab so cleanup
# can identify and remove them without touching user nodes.
_QG_NODE_PREFIX: str = "QG_"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rendered_filepath(output_dir: str, basename: str, ext: str, frame: int | None = None) -> str:
    """Build the absolute path to a rendered output file.

    Resolves Blender's ``//`` blend-relative prefix.  On 4.x the File Output
    node appends a zero-padded frame number; on 5.0+ it does not.
    """
    abs_dir: str = bpy.path.abspath(output_dir)
    if _USE_NEW_FILE_OUTPUT:
        filename: str = f"{basename}.{ext}"
    else:
        if frame is None:
            frame = bpy.context.scene.frame_current
        filename = f"{basename}{frame:04d}.{ext}"
    return os.path.join(abs_dir, filename)


def _init_file_output_dir(node: bpy.types.CompositorNodeOutputFile, output_dir: str) -> None:
    """Set the output directory on a File Output node (compat 4.x / 5.0+).

    On 5.0+ also clears the default ``file_name`` prefix that would otherwise
    be prepended to every output filename.
    """
    if hasattr(node, 'directory'):
        node.directory = output_dir
        # 5.0+ defaults file_name to "file_name" — clear it so output
        # filenames match the item names exactly.
        if hasattr(node, 'file_name'):
            node.file_name = ""
    else:
        node.base_path = output_dir


def _count_materials_missing_aovs() -> int:
    """Count local Principled BSDF materials *on scene objects* that have no QG_AOV nodes.

    Only scene objects are checked because Setup only processes materials on
    scene objects — checking all of bpy.data.materials would flag orphan or
    unused materials that Setup never touches.  Linked materials are skipped.
    """
    seen: set[str] = set()
    count: int = 0
    for obj in bpy.context.scene.objects:
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None or mat.name in seen:
                continue
            seen.add(mat.name)
            if mat.library is not None:
                continue  # linked — read-only node tree
            if mat.node_tree is None:
                continue
            try:
                node = mat.node_tree.nodes["Material Output"].inputs[0].links[0].from_node
                if node.type != 'BSDF_PRINCIPLED':
                    continue
            except Exception:
                continue
            if not any(n.name == "QG_AOV_BaseColor" for n in mat.node_tree.nodes):
                count += 1
    return count


def get_scene_issues(context: bpy.types.Context) -> list[str]:
    """Return human-readable issues preventing QuadGrab from running.

    Checks output path validity, render engine, film transparency,
    required view-layer passes, and (when PBR is enabled) material AOVs.
    """
    issues: list[str] = []
    scene: bpy.types.Scene = context.scene
    vl: bpy.types.ViewLayer = context.view_layer

    # Output path validation — '//' relative paths require a saved .blend
    output_dir: str = getattr(scene, properties.PROP_OUTPUT_DIR, "//quadgrab/")
    if output_dir.startswith("//") and not bpy.data.filepath:
        issues.append(
            "Save the .blend file first (output path uses '//' relative prefix)"
        )

    if scene.render.engine != 'CYCLES':
        issues.append(
            f"Render engine is '{scene.render.engine}' — run Setup (needs Cycles)")
    if not scene.render.film_transparent:
        issues.append("Film Transparent is off — run Setup")
    if not vl.use_pass_z:
        issues.append("Z pass is disabled — run Setup")
    if not vl.use_pass_normal:
        issues.append("Normal pass is disabled — run Setup")
    if not vl.use_pass_diffuse_color:
        issues.append("Diffuse Color pass is disabled — run Setup")
    if not vl.use_pass_glossy_color:
        issues.append("Glossy Color pass is disabled — run Setup")
    if not vl.use_pass_ambient_occlusion:
        issues.append("AO pass is disabled — run Setup")

    # AOV check — only relevant when PBR output is requested
    if getattr(scene, properties.PROP_USE_PBR, False):
        missing_aovs: int = _count_materials_missing_aovs()
        if missing_aovs > 0:
            issues.append(
                f"{missing_aovs} material(s) missing AOV nodes — run Setup again"
            )

    return issues


def _get_compositor_tree(scene: bpy.types.Scene) -> bpy.types.CompositorNodeTree | None:
    """Return the scene's compositor node tree (compat 4.x / 5.0+)."""
    if hasattr(scene, 'compositing_node_group'):
        return scene.compositing_node_group
    return getattr(scene, 'node_tree', None)
