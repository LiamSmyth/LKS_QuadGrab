"""Atomic scene-setup and restore helpers for QuadGrab.

These functions are shared by:

* ``OBJECT_OT_lks_quad_grab`` – the atomic workflow: setup → render → restore
  all happens inside a single ``execute()`` call so the scene is never left
  in a partially-modified state.

* ``OBJECT_OT_lks_quad_grab_setup`` / ``OBJECT_OT_lks_quad_grab_restore`` –
  the manual debug workflow where the user intentionally persists the setup so
  they can inspect the scene.
"""

from __future__ import annotations

import bpy

from .. import properties
from .comp_graph import build_comp_graph
from .pbr_aovs import setup_pbr_aovs_mats
from .quadgrab_helpers import _QG_NODE_PREFIX, _get_compositor_tree

# AOV definitions used by both setup and view-layer initialisation.
_QG_AOV_DEFS: tuple[tuple[str, str], ...] = (
    ("QG_AOV_BaseColor", "COLOR"),
    ("QG_AOV_Normal", "COLOR"),
    ("QG_AOV_specular", "VALUE"),
    ("QG_AOV_Roughness", "VALUE"),
    ("QG_AOV_Metallic", "VALUE"),
)


def apply_quadgrab_setup(
    scene: bpy.types.Scene,
    vl: bpy.types.ViewLayer,
    timestamp: str = "",
) -> tuple[dict[str, object], int]:
    """Apply all QuadGrab scene changes and build the compositor graph.

    Returns ``(cache, skipped_linked)`` where:

    * ``cache`` is a snapshot of the pre-change state that must be passed
      back to :func:`restore_quadgrab` to undo everything.
    * ``skipped_linked`` is the count of linked materials whose AOV nodes
      could not be patched (their node trees are read-only).

    This function is intentionally side-effect-free with respect to the
    scene's ``PROP_CACHED_SETTINGS`` property — the caller decides whether
    to persist the cache (Setup operator) or keep it in memory (atomic QuadGrab).
    """
    # --- 1. Snapshot current state so restore_quadgrab can undo ---
    if hasattr(scene, 'compositing_node_group'):
        had_compositing: bool = scene.render.use_compositing
        had_comp_tree: bool = scene.compositing_node_group is not None
    else:
        had_compositing = getattr(scene, 'use_nodes', False)
        had_comp_tree = scene.node_tree is not None

    cache: dict[str, object] = {
        "render_engine": scene.render.engine,
        "film_transparent": scene.render.film_transparent,
        "use_pass_normal": vl.use_pass_normal,
        "use_pass_z": vl.use_pass_z,
        "use_pass_diffuse_color": vl.use_pass_diffuse_color,
        "use_pass_glossy_color": vl.use_pass_glossy_color,
        "use_pass_ambient_occlusion": vl.use_pass_ambient_occlusion,
        "had_compositing": had_compositing,
        "had_comp_tree": had_comp_tree,
    }

    # --- 2. Render settings ---
    scene.render.engine = 'CYCLES'
    scene.render.film_transparent = True
    vl.use_pass_normal = True
    vl.use_pass_z = True
    vl.use_pass_diffuse_color = True
    vl.use_pass_glossy_color = True
    vl.use_pass_ambient_occlusion = True

    # --- 3. View-layer AOVs ---
    aovs_exist: bool = any(aov.name.startswith("QG_AOV") for aov in vl.aovs)
    if not aovs_exist:
        for aov_name, aov_type in _QG_AOV_DEFS:
            aov: bpy.types.AOV = vl.aovs.add()
            aov.name = aov_name
            aov.type = aov_type

    # --- 4. Material AOV nodes (PBR mode only) ---
    skipped_linked: int = 0
    if getattr(scene, properties.PROP_USE_PBR, False):
        _updated, skipped_linked = setup_pbr_aovs_mats()

    # --- 5. Compositor graph ---
    build_comp_graph(timestamp=timestamp)

    return cache, skipped_linked


def restore_quadgrab(
    scene: bpy.types.Scene,
    vl: bpy.types.ViewLayer,
    cache: dict[str, object],
) -> None:
    """Restore scene render settings and remove all QG_ scene modifications.

    Designed to be called from a ``finally`` block so cleanup is guaranteed
    whether the render succeeded or raised an exception.

    Does **not** remove QuadGrab objects, images, or textures — those are
    managed by the caller (camera removed in atomic mode; preview plane and
    output images are intentionally kept).
    """
    # --- 1. Restore render settings ---
    if cache:
        scene.render.engine = str(
            cache.get("render_engine", scene.render.engine))
        scene.render.film_transparent = bool(
            cache.get("film_transparent", scene.render.film_transparent))
        vl.use_pass_normal = bool(
            cache.get("use_pass_normal", vl.use_pass_normal))
        vl.use_pass_z = bool(cache.get("use_pass_z", vl.use_pass_z))
        vl.use_pass_diffuse_color = bool(
            cache.get("use_pass_diffuse_color", vl.use_pass_diffuse_color))
        vl.use_pass_glossy_color = bool(
            cache.get("use_pass_glossy_color", vl.use_pass_glossy_color))
        vl.use_pass_ambient_occlusion = bool(
            cache.get("use_pass_ambient_occlusion", vl.use_pass_ambient_occlusion))

    # --- 2. Remove QG_ compositor nodes and restore compositing state ---
    compgraph: bpy.types.CompositorNodeTree | None = _get_compositor_tree(
        scene)
    if compgraph is not None:
        for node in list(compgraph.nodes):
            if node.name.startswith(_QG_NODE_PREFIX):
                compgraph.nodes.remove(node)
        if cache:
            had_compositing: bool = bool(cache.get("had_compositing", True))
            had_comp_tree: bool = bool(cache.get("had_comp_tree", True))
            if hasattr(scene, 'compositing_node_group'):
                scene.render.use_compositing = had_compositing
                if not had_comp_tree:
                    scene.compositing_node_group = None
            else:
                scene.use_nodes = had_compositing

    # --- 3. Remove QG_ view-layer AOVs ---
    for aov in list(vl.aovs):
        if aov.name.startswith("QG_AOV"):
            vl.aovs.remove(aov)

    # --- 4. Remove QG_ material AOV nodes (local materials only) ---
    for mat in bpy.data.materials:
        if mat.library is not None:
            continue  # linked — read-only node tree
        if mat.node_tree is None:
            continue
        for node in list(mat.node_tree.nodes):
            if node.name.startswith("QG_AOV"):
                mat.node_tree.nodes.remove(node)
