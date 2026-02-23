"""Compositor graph construction for QuadGrab."""

from __future__ import annotations

import bpy
from .. import properties
from .quadgrab_helpers import _QG_NODE_PREFIX, _init_file_output_dir


def build_comp_graph(timestamp: str) -> None:
    """Build the full QuadGrab compositor node graph."""
    scene = bpy.context.scene
    # Blender 5.0+ removed scene.node_tree / scene.use_nodes in favour of
    # scene.compositing_node_group / scene.render.use_compositing.
    if hasattr(scene, 'compositing_node_group'):
        # Blender 5.0+
        scene.render.use_compositing = True
        compgraph: bpy.types.CompositorNodeTree = scene.compositing_node_group
        if compgraph is None:
            # Factory-startup or fresh scene: create and assign a new tree.
            compgraph = bpy.data.node_groups.new(
                'Compositing Nodetree', 'CompositorNodeTree')
            scene.compositing_node_group = compgraph
    else:
        # Blender 4.x
        if not scene.use_nodes:
            scene.use_nodes = True
        compgraph = scene.node_tree
        if compgraph is None:
            raise RuntimeError(
                "LKS QuadGrab: compositor node tree is None after enabling compositing.")

    # Remove only previously-created QG nodes (preserve user nodes).
    for compnode in list(compgraph.nodes):
        if compnode.name.startswith(_QG_NODE_PREFIX):
            compgraph.nodes.remove(compnode)

    # CompositorNodeComposite was removed in Blender 5.1.  It only
    # drives the built-in render result preview; all actual file output
    # goes through CompositorNodeOutputFile nodes created below.
    try:
        n_comp: bpy.types.CompositorNodeComposite = compgraph.nodes.new(
            type="CompositorNodeComposite")
        n_comp.name = _QG_NODE_PREFIX + "Composite"
        n_comp.label = "QG Composite"
        _has_composite = True
    except RuntimeError:
        _has_composite = False

    n_img: bpy.types.CompositorNodeRLayers = compgraph.nodes.new(
        type="CompositorNodeRLayers")
    n_img.name = _QG_NODE_PREFIX + "RenderLayers"
    n_img.label = "QG Render Layers"
    n_img.location = [-1000, 0]

    if _has_composite:
        compgraph.links.new(n_comp.inputs["Image"], n_img.outputs["Image"])
        compgraph.links.new(n_comp.inputs["Alpha"], n_img.outputs["Alpha"])

    def setup_zdepth_graph() -> None:
        """Create nodes ``zdepth_inverted`` and ``zdepth_unitized``.

        Uses MULTIPLY(−1) rather than INVERT (which does 1−x) so that the
        surface pixel (raw depth ≈ 0) maps to 0 and increasing depth maps to
        increasingly negative values.  The NORMALIZE node that follows re-maps
        the monotonic range to [0, 1] (unitized output).
        """
        try:
            n_invert_z = compgraph.nodes.new(type="ShaderNodeMath")
        except RuntimeError:
            n_invert_z = compgraph.nodes.new(type="CompositorNodeMath")
        n_invert_z.name = _QG_NODE_PREFIX + "zdepth_inverted"
        n_invert_z.label = "QG zdepth_inverted"
        n_invert_z.location = (-700, 0)
        n_invert_z.operation = 'MULTIPLY'
        n_invert_z.inputs[1].default_value = -1.0
        compgraph.links.new(n_invert_z.inputs[0], n_img.outputs["Depth"])
        n_normalize_z: bpy.types.CompositorNodeNormalize = compgraph.nodes.new(
            "CompositorNodeNormalize")
        n_normalize_z.name = _QG_NODE_PREFIX + "zdepth_unitized"
        n_normalize_z.label = "QG zdepth_unitized"
        n_normalize_z.location = (-500, 0)
        compgraph.links.new(n_normalize_z.inputs[0], n_invert_z.outputs[0])
    setup_zdepth_graph()

    def setup_compoutput_png(timestamp: str) -> None:
        """Set up PNG Linear and PNG SRGB File Output nodes."""
        n_file_png: bpy.types.CompositorNodeOutputFile = compgraph.nodes.new(
            type="CompositorNodeOutputFile")
        n_file_png.name = _QG_NODE_PREFIX + "File Out PNG Linear"
        n_file_png.label = "QG File Out PNG Linear"

        n_file_png.location = [0, -150]
        output_dir: str = getattr(
            bpy.context.scene, properties.PROP_OUTPUT_DIR)
        _init_file_output_dir(n_file_png, output_dir)
        # node settings
        png_settings: bpy.types.ImageFormatSettings = n_file_png.format
        if hasattr(png_settings, 'media_type'):
            png_settings.media_type = 'IMAGE'
        png_settings.file_format = "PNG"
        png_settings.color_depth = "16"
        png_settings.compression = 100
        png_settings.color_management = "OVERRIDE"
        png_settings.view_settings.view_transform = 'Raw'

        # Create file output slots (5.0+: file_output_items, 4.x: file_slots)
        slot_names: list[str] = [
            timestamp + "Composite", timestamp + "Z", timestamp + "Normal",
            timestamp + "BaseColor", timestamp + "AO", timestamp + "Roughness",
            timestamp + "Metallic", timestamp + "Specular", timestamp + "Alpha",
        ]
        if hasattr(n_file_png, 'file_output_items'):
            for sname in slot_names:
                n_file_png.file_output_items.new('RGBA', name=sname)
        else:
            n_file_png.file_slots["Image"].path = slot_names[0]
            for sname in slot_names[1:]:
                n_file_png.file_slots.new(sname)

        # Connect PNG (Linear) Outputs
        if getattr(bpy.context.scene, properties.PROP_USE_DEPTH):
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Z"], compgraph.nodes[_QG_NODE_PREFIX + "zdepth_unitized"].outputs[0])
        if getattr(bpy.context.scene, properties.PROP_USE_PBR):
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Normal"], n_img.outputs["QG_AOV_Normal"])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "BaseColor"], n_img.outputs["QG_AOV_BaseColor"])
            ao_output_name: str = "AO" if "AO" in n_img.outputs else "Ambient Occlusion"
            compgraph.links.new(
                n_file_png.inputs[timestamp + "AO"], n_img.outputs[ao_output_name])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Alpha"], n_img.outputs["Alpha"])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Roughness"], n_img.outputs["QG_AOV_Roughness"])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Metallic"], n_img.outputs["QG_AOV_Metallic"])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Specular"], n_img.outputs["QG_AOV_specular"])

        # --- PNG SRGB ---
        n_file_png_srgb: bpy.types.CompositorNodeOutputFile = compgraph.nodes.new(
            type="CompositorNodeOutputFile")
        n_file_png_srgb.name = _QG_NODE_PREFIX + "File Out PNG SRGB"
        n_file_png_srgb.label = "QG File Out PNG SRGB"

        png_srgb_settings: bpy.types.ImageFormatSettings = n_file_png_srgb.format
        if hasattr(png_srgb_settings, 'media_type'):
            png_srgb_settings.media_type = 'IMAGE'
        png_srgb_settings.file_format = "PNG"
        png_srgb_settings.color_depth = "16"
        png_srgb_settings.compression = 100
        png_srgb_settings.color_management = "OVERRIDE"
        png_srgb_settings.view_settings.view_transform = 'Standard'

        _init_file_output_dir(n_file_png_srgb, getattr(
            bpy.context.scene, properties.PROP_OUTPUT_DIR))
        n_file_png_srgb.location = [0, -250]

        # Create file output slots (5.0+: file_output_items, 4.x: file_slots)
        if hasattr(n_file_png_srgb, 'file_output_items'):
            n_file_png_srgb.file_output_items.new(
                'RGBA', name=timestamp + "Composite")
            n_file_png_srgb.file_output_items.new(
                'RGBA', name=timestamp + "BaseColor_srgb")
        else:
            n_file_png_srgb.file_slots["Image"].path = timestamp + "Composite"
            n_file_png_srgb.file_slots.new(timestamp + "BaseColor_srgb")

        if getattr(bpy.context.scene, properties.PROP_USE_PBR):
            compgraph.links.new(
                n_file_png_srgb.inputs[timestamp + "BaseColor_srgb"], n_img.outputs["QG_AOV_BaseColor"])

    setup_compoutput_png(timestamp=timestamp)

    def setup_compoutput_png_tonemapped() -> None:
        """Set up tonemapped PNG File Output."""
        n_file_png_tonemapped: bpy.types.CompositorNodeOutputFile = compgraph.nodes.new(
            type="CompositorNodeOutputFile")
        n_file_png_tonemapped.name = _QG_NODE_PREFIX + "File Out PNG Tonemapped"
        n_file_png_tonemapped.label = "QG File Out PNG Tonemapped"
        n_file_png_tonemapped.location = [0, -400]
        _init_file_output_dir(n_file_png_tonemapped, getattr(
            bpy.context.scene, properties.PROP_OUTPUT_DIR))
        png_tonemapped_settings: bpy.types.ImageFormatSettings = n_file_png_tonemapped.format
        if hasattr(png_tonemapped_settings, 'media_type'):
            png_tonemapped_settings.media_type = 'IMAGE'
        png_tonemapped_settings.file_format = "PNG"
        png_tonemapped_settings.color_depth = "16"
        png_tonemapped_settings.compression = 100
        # Create file output slot (5.0+: file_output_items, 4.x: file_slots)
        comp_input_name: str = timestamp + "Composite"
        if hasattr(n_file_png_tonemapped, 'file_output_items'):
            n_file_png_tonemapped.file_output_items.new(
                'RGBA', name=comp_input_name)
        else:
            n_file_png_tonemapped.file_slots["Image"].path = comp_input_name
            comp_input_name = "Image"  # 4.x: input socket keeps original name
        if getattr(bpy.context.scene, properties.PROP_USE_COMPOSITE):
            compgraph.links.new(
                n_file_png_tonemapped.inputs[comp_input_name], n_img.outputs["Image"])
    setup_compoutput_png_tonemapped()

    def setup_compoutput_exr() -> None:
        """Set up EXR File Output."""
        max_depth_val: float = getattr(
            bpy.context.scene, properties.PROP_MAX_DEPTH)
        midpoint_val: float = getattr(
            bpy.context.scene, properties.PROP_DEPTH_MIDPOINT, 0.0)

        # MAXIMUM: floor at −max_depth so out-of-range / sky pixels clip cleanly.
        try:
            n_max = compgraph.nodes.new(type="ShaderNodeMath")
        except RuntimeError:
            n_max = compgraph.nodes.new(type="CompositorNodeMath")
        n_max.location = (-500, -200)
        n_max.label = "QG EXR Height Max"
        n_max.name = _QG_NODE_PREFIX + "EXR Height Max"
        n_max.operation = 'MAXIMUM'
        n_max.inputs[1].default_value = -max_depth_val
        compgraph.links.new(
            n_max.inputs[0], compgraph.nodes[_QG_NODE_PREFIX + "zdepth_inverted"].outputs[0])

        # Shift zero point: ADD(midpoint × max_depth).
        # Default midpoint=0 → shift=0 → range [−max_depth, 0], surface=0.
        # midpoint=0.5 → shift=max_depth/2 → range [−max_depth/2, +max_depth/2],
        # midplane=0, geometry in front is positive, behind is negative.
        try:
            n_shift = compgraph.nodes.new(type="ShaderNodeMath")
        except RuntimeError:
            n_shift = compgraph.nodes.new(type="CompositorNodeMath")
        n_shift.location = (-280, -200)
        n_shift.label = "QG EXR Height Shift"
        n_shift.name = _QG_NODE_PREFIX + "EXR Height Shift"
        n_shift.operation = 'ADD'
        n_shift.inputs[1].default_value = midpoint_val * max_depth_val
        compgraph.links.new(n_shift.inputs[0], n_max.outputs[0])

        n_file_exr: bpy.types.CompositorNodeOutputFile = compgraph.nodes.new(
            type="CompositorNodeOutputFile")
        n_file_exr.name = _QG_NODE_PREFIX + "File Out EXR"
        n_file_exr.label = "QG File Out EXR"
        n_file_exr.location = [0, -600]
        _init_file_output_dir(n_file_exr, getattr(
            bpy.context.scene, properties.PROP_OUTPUT_DIR))
        exr_settings: bpy.types.ImageFormatSettings = n_file_exr.format
        if hasattr(exr_settings, 'media_type'):
            exr_settings.media_type = 'IMAGE'
        exr_settings.file_format = "OPEN_EXR"
        exr_settings.color_depth = "32"
        exr_settings.compression = 100
        # Create file output slots and track input names for linking
        depth_raw_name: str = timestamp + "Depth_Raw"
        depth_unit_name: str = timestamp + "Depth_Unitized"
        if hasattr(n_file_exr, 'file_output_items'):
            n_file_exr.file_output_items.new('FLOAT', name=depth_raw_name)
            n_file_exr.file_output_items.new('FLOAT', name=depth_unit_name)
            depth_raw_input: str = depth_raw_name
            depth_unit_input: str = depth_unit_name
        else:
            n_file_exr.file_slots.new(name="Depth_Unitized")
            n_file_exr.file_slots["Image"].path = depth_raw_name
            n_file_exr.file_slots[1].path = depth_unit_name
            depth_raw_input = "Image"
            depth_unit_input = "Depth_Unitized"
        if getattr(bpy.context.scene, properties.PROP_USE_DEPTH_EXR_RAW):
            # Depth_Raw: signed world-space values, zero at surface + midpoint shift.
            compgraph.links.new(
                n_file_exr.inputs[depth_raw_input], n_shift.outputs[0])
        if getattr(bpy.context.scene, properties.PROP_USE_DEPTH_EXR):
            # Depth_Unitized: 0-1 range from the Normalize node.
            compgraph.links.new(
                n_file_exr.inputs[depth_unit_input], compgraph.nodes[_QG_NODE_PREFIX + 'zdepth_unitized'].outputs[0])
    setup_compoutput_exr()

    # --- Viewer node so the compositor backdrop isn't blank ---
    try:
        n_viewer = compgraph.nodes.new(type="CompositorNodeViewer")
        n_viewer.name = _QG_NODE_PREFIX + "Viewer"
        n_viewer.label = "QG Viewer"
        n_viewer.location = (300, 200)
        compgraph.links.new(n_viewer.inputs["Image"], n_img.outputs["Image"])
        if "Alpha" in n_viewer.inputs:
            compgraph.links.new(
                n_viewer.inputs["Alpha"], n_img.outputs["Alpha"])
    except RuntimeError:
        pass  # Viewer node may be removed in a future Blender version
