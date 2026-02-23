"""ops – Blender operator package for lks_quadgrab.

Re-exports every operator class and registers/unregisters them via the
standard ``register()`` / ``unregister()`` interface expected by
``__init__.py``.

Utility (non-operator) symbols are also re-exported here so that any test
or external code that previously imported from ``lks_quadgrab.operators``
continues to work after changing to ``lks_quadgrab.ops``.
"""

from __future__ import annotations

import bpy

from .object_ot_lks_quadgrab import OBJECT_OT_lks_quad_grab
from .object_ot_lks_quadgrab_setup import OBJECT_OT_lks_quad_grab_setup
from .object_ot_lks_quadgrab_restore import OBJECT_OT_lks_quad_grab_restore
from .object_ot_lks_quadgrab_make_plane import OBJECT_OT_lks_quad_grab_make_plane
from .object_ot_lks_quadgrab_fit_to_selection import OBJECT_OT_lks_quad_grab_fit_to_selection
from .object_ot_lks_quadgrab_toggle_plane_selectable import OBJECT_OT_lks_quad_grab_toggle_plane_selectable

# Utility re-exports – keep test imports working after the operators → ops rename.
from ..util.quadgrab_helpers import (  # noqa: F401
    CLIP_START,
    _USE_NEW_FILE_OUTPUT,
    _QG_NODE_PREFIX,
    _rendered_filepath,
    _init_file_output_dir,
    get_scene_issues,
    _get_compositor_tree,
)
from ..util.comp_graph import build_comp_graph  # noqa: F401
from ..util.pbr_aovs import setup_pbr_aovs_mats  # noqa: F401
from ..util.scene_setup import apply_quadgrab_setup, restore_quadgrab  # noqa: F401

# Ordered registration list.
opsToRegister: tuple[type[bpy.types.Operator], ...] = (
    OBJECT_OT_lks_quad_grab_setup,
    OBJECT_OT_lks_quad_grab_restore,
    OBJECT_OT_lks_quad_grab,
    OBJECT_OT_lks_quad_grab_make_plane,
    OBJECT_OT_lks_quad_grab_fit_to_selection,
    OBJECT_OT_lks_quad_grab_toggle_plane_selectable,
)


def register() -> None:
    for cls in opsToRegister:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(opsToRegister):
        bpy.utils.unregister_class(cls)
