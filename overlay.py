"""GPU overlay for QuadGrab – draws a wireframe capture-volume box.

When a "QuadGrab Reference Plane" is the active object the overlay renders:

- The plane footprint (top face) as a filled translucent surface.
- The plane footprint outline in cyan.
- Four vertical edges showing the MaxDepth extent downward (local −Z).
- The bottom face at MaxDepth in a darker blue.

The overlay hooks into ``SpaceView3D`` via ``draw_handler_add`` and is
registered/unregistered alongside the rest of the addon.

The overlay can be disabled from the panel via the "Show Capture Volume"
toggle (``PROP_SHOW_OVERLAY``).
"""

from __future__ import annotations

import math

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector

from . import properties

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
# Near plane (surface / top face) — greenish-blue teal
_COLOR_NEAR: tuple[float, float, float, float] = (0.0, 0.85, 0.65, 0.60)
_COLOR_NEAR_FILL: tuple[float, float, float, float] = (0.0, 0.85, 0.65, 0.10)
# Mid plane — blue
_COLOR_MID: tuple[float, float, float, float] = (0.15, 0.40, 1.0, 0.50)
_COLOR_MID_FILL: tuple[float, float, float, float] = (0.15, 0.40, 1.0, 0.08)
# Far plane (bottom face) — purplish-blue
_COLOR_FAR: tuple[float, float, float, float] = (0.50, 0.25, 0.90, 0.50)
_COLOR_FAR_FILL: tuple[float, float, float, float] = (0.50, 0.25, 0.90, 0.08)
# Side edges (neutral)
_COLOR_SIDE: tuple[float, float, float, float] = (0.2, 0.5, 0.7, 0.35)

# Draw handler stored here so we can remove it on unregister.
_draw_handle: object | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sort_verts_winding(verts: list[Vector]) -> list[Vector]:
    """Return *verts* sorted into a consistent counter-clockwise winding order.

    Blender mesh vertices are stored in creation order, which for a plane
    primitive is 0→1→2→3 but that layout draws an X (two crossing lines)
    rather than a rectangle.  Sorting by polar angle around the centroid
    fixes this for any convex quad.
    """
    if len(verts) < 3:
        return verts
    cx: float = sum(v.x for v in verts) / len(verts)
    cy: float = sum(v.y for v in verts) / len(verts)
    return sorted(verts, key=lambda v: math.atan2(v.y - cy, v.x - cx))


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def _draw_capture_volume() -> None:
    """Called every viewport redraw – draws the capture box if applicable.

    Draws three coloured planes inside the capture volume:
      - Near plane  (surface / reference plane) — greenish-blue teal
      - Mid plane   (depth-zero offset plane)   — blue
      - Far plane   (max-depth floor)            — purplish-blue
    Each plane is rendered as a faint filled quad plus a solid outline.
    Side edges of the bounding box connect the near and far planes.
    """
    context = bpy.context

    # --- Overlay visibility toggle ---
    scene: bpy.types.Scene = context.scene
    if not getattr(scene, properties.PROP_SHOW_OVERLAY, True):
        return

    obj: bpy.types.Object | None = (
        context.view_layer.objects.active
        if hasattr(context, 'view_layer') else None
    )
    if obj is None or obj.name != "QuadGrab Reference Plane":
        return

    max_depth: float = getattr(scene, properties.PROP_MAX_DEPTH, 10.0)
    midpoint: float = getattr(scene, properties.PROP_DEPTH_MIDPOINT, 0.0)

    # --- Compute world-space corners of the plane mesh (4 verts) -----------
    mesh: bpy.types.Mesh = obj.data
    if mesh is None or len(mesh.vertices) < 4:
        return

    # Sort in local space (the plane primitive is always flat in local XY,
    # so atan2 is well-defined there regardless of world-space rotation).
    # Sorting in world XY degenerates when the plane is rotated 90° because
    # all vertices share the same world Y, producing an X instead of a quad.
    local_sorted: list[Vector] = _sort_verts_winding(
        [v.co.copy() for v in mesh.vertices]
    )
    world_verts: list[Vector] = [obj.matrix_world @ v for v in local_sorted]

    # Local −Z direction in world space (unit vector), used to project depth.
    local_down: Vector = -(obj.matrix_world.to_3x3() @
                           Vector((0, 0, 1))).normalized()

    # Three key planes of the capture volume:
    #   near = reference plane surface (depth = 0)
    #   mid  = depth-zero offset plane (depth = midpoint × max_depth)
    #   far  = deepest captured layer  (depth = max_depth)
    mid_verts: list[Vector] = [
        v + local_down * midpoint * max_depth for v in world_verts]
    far_verts: list[Vector] = [
        v + local_down * max_depth for v in world_verts]

    # --- Build geometry helpers -----------------------------------------
    n: int = len(world_verts)

    def _outline_loop(verts: list[Vector]) -> list[Vector]:
        """Return line pairs for a closed polygon outline."""
        lines: list[Vector] = []
        for i in range(len(verts)):
            lines.append(verts[i])
            lines.append(verts[(i + 1) % len(verts)])
        return lines

    def _fill_tris(verts: list[Vector]) -> list[Vector]:
        """Return triangle fan from verts[0] (convex CCW quad assumed)."""
        tris: list[Vector] = []
        for i in range(1, len(verts) - 1):
            tris.append(verts[0])
            tris.append(verts[i])
            tris.append(verts[i + 1])
        return tris

    near_lines: list[Vector] = _outline_loop(world_verts)
    mid_lines: list[Vector] = _outline_loop(mid_verts)
    far_lines: list[Vector] = _outline_loop(far_verts)

    near_fill: list[Vector] = _fill_tris(world_verts)
    mid_fill: list[Vector] = _fill_tris(mid_verts)
    far_fill: list[Vector] = _fill_tris(far_verts)

    # Side edges connecting near → far
    side_lines: list[Vector] = []
    for i in range(n):
        side_lines.append(world_verts[i])
        side_lines.append(far_verts[i])

    # --- Draw ----------------------------------------------------------------
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    gpu.state.blend_set('ALPHA')
    gpu.state.depth_test_set('LESS_EQUAL')

    # Faint filled quads — depth mask off so fills look transparent
    gpu.state.depth_mask_set(False)
    for tris, color in (
        (near_fill, _COLOR_NEAR_FILL),
        (mid_fill,  _COLOR_MID_FILL),
        (far_fill,  _COLOR_FAR_FILL),
    ):
        if tris:
            batch = batch_for_shader(shader, 'TRIS', {"pos": tris})
            shader.uniform_float("color", color)
            batch.draw(shader)
    gpu.state.depth_mask_set(True)

    # Outlines
    gpu.state.line_width_set(2.0)
    for lines, color in (
        (near_lines, _COLOR_NEAR),
        (mid_lines,  _COLOR_MID),
        (far_lines,  _COLOR_FAR),
    ):
        batch = batch_for_shader(shader, 'LINES', {"pos": lines})
        shader.uniform_float("color", color)
        batch.draw(shader)

    # Side edges
    batch_side = batch_for_shader(shader, 'LINES', {"pos": side_lines})
    shader.uniform_float("color", _COLOR_SIDE)
    batch_side.draw(shader)

    # Restore defaults
    gpu.state.blend_set('NONE')
    gpu.state.line_width_set(1.0)
    gpu.state.depth_test_set('NONE')


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register() -> None:
    global _draw_handle
    if _draw_handle is None:
        _draw_handle = bpy.types.SpaceView3D.draw_handler_add(
            _draw_capture_volume, (), 'WINDOW', 'POST_VIEW')


def unregister() -> None:
    global _draw_handle
    if _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, 'WINDOW')
        _draw_handle = None
