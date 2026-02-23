import bpy

PROP_OUTPUT_DIR = "lks_quadgrab_output_dir"
PROP_RENDER_SIZE = "lks_quadgrab_render_size"
PROP_USE_TIMESTAMP = "lks_quadgrab_use_timestamp"
PROP_USE_DEPTH = "lks_quadgrab_use_depth"
PROP_USE_DEPTH_EXR = "lks_quadgrab_use_depth_exr"
PROP_USE_DEPTH_EXR_RAW = "lks_quadgrab_use_depth_exr_raw"
PROP_USE_COMPOSITE = "lks_quadgrab_use_composite"
PROP_USE_PBR = "lks_quadgrab_use_pbr"
PROP_MAX_DEPTH = "lks_quadgrab_max_depth"
PROP_USE_PREVIEW_PLANE = "lks_quadgrab_use_preview_plane"
PROP_DISPLACE_PLANE = "lks_quadgrab_displace_plane"
PROP_USE_DEBUG = "lks_quadgrab_use_debug"
PROP_CACHED_SETTINGS = "lks_quadgrab_cached_settings"
PROP_SHOW_OVERLAY = "lks_quadgrab_show_overlay"
PROP_DEBUG_EXPANDED = "lks_quadgrab_debug_expanded"
PROP_OUTPUT_EXPANDED = "lks_quadgrab_output_expanded"
PROP_GRAB_EXPANDED = "lks_quadgrab_grab_expanded"
PROP_PREVIEW_EXPANDED = "lks_quadgrab_preview_expanded"
PROP_DEPTH_MIDPOINT = "lks_quadgrab_depth_midpoint"
PROP_OUTPUT_NAME = "lks_quadgrab_output_name"
PROP_FIT_FROM_VIEW = "lks_quadgrab_fit_from_view"
PROP_FIT_MARGIN = "lks_quadgrab_fit_margin"
PROP_LAST_GRAB_PREFIX = "lks_quadgrab_last_grab_prefix"


def register() -> None:
    setattr(bpy.types.Scene, PROP_OUTPUT_DIR, bpy.props.StringProperty(
        name="Image Export Path",
        subtype='DIR_PATH',
        default='//quadgrab/'))

    setattr(bpy.types.Scene, PROP_RENDER_SIZE, bpy.props.IntProperty(
        name="Resolution",
        description="Output Texture Size",
        default=128,
        soft_min=128,
        soft_max=8192,
        step=64
    ))
    setattr(bpy.types.Scene, PROP_USE_TIMESTAMP, bpy.props.BoolProperty(
        name="Use Timestamp",
        description="Enable Add Timestamp to filename",
        default=False
    ))
    setattr(bpy.types.Scene, PROP_USE_DEPTH, bpy.props.BoolProperty(
        name="Depth",
        description="Output ZDepth",
        default=True
    ))
    setattr(bpy.types.Scene, PROP_USE_DEPTH_EXR, bpy.props.BoolProperty(
        name="Z EXR 0-1",
        description="Output unitized (0-1) Z depth as EXR",
        default=True
    ))
    setattr(bpy.types.Scene, PROP_USE_DEPTH_EXR_RAW, bpy.props.BoolProperty(
        name="Z EXR Raw",
        description="Output signed world-space Z depth as EXR (required for metrically accurate displacement)",
        default=True
    ))
    setattr(bpy.types.Scene, PROP_USE_COMPOSITE, bpy.props.BoolProperty(
        name="Composite",
        description="Output Composite",
        default=False
    ))
    setattr(bpy.types.Scene, PROP_USE_PBR, bpy.props.BoolProperty(
        name="PBR",
        description="Output PBR maps",
        default=False
    ))
    setattr(bpy.types.Scene, PROP_MAX_DEPTH, bpy.props.FloatProperty(
        name="MaxDepth",
        description="Max Depth for ZGrab",
        default=10.0
    ))
    setattr(bpy.types.Scene, PROP_USE_PREVIEW_PLANE, bpy.props.BoolProperty(
        name="Create Preview Plane",
        description="Create a plane to preview generated textures",
        default=False
    ))
    setattr(bpy.types.Scene, PROP_DISPLACE_PLANE, bpy.props.BoolProperty(
        name="Displace Plane",
        description="If preview plane is created, displace it with zgrab?",
        default=False
    ))
    setattr(bpy.types.Scene, PROP_USE_DEBUG, bpy.props.BoolProperty(
        name="Debug",
        description="Debug will disable removing of intermediate objects",
        default=False
    ))
    setattr(bpy.types.Scene, PROP_CACHED_SETTINGS, bpy.props.StringProperty(
        name="Cached Settings",
        description="JSON cache of original scene settings before QuadGrab setup",
        default="",
        options={'HIDDEN'},
    ))
    setattr(bpy.types.Scene, PROP_SHOW_OVERLAY, bpy.props.BoolProperty(
        name="Show Capture Volume",
        description="Draw the QuadGrab capture-volume overlay in the viewport",
        default=True,
    ))
    setattr(bpy.types.Scene, PROP_DEBUG_EXPANDED, bpy.props.BoolProperty(
        name="Debug",
        description="Expand the Debug section",
        default=False,
        options={'HIDDEN'},
    ))
    setattr(bpy.types.Scene, PROP_OUTPUT_EXPANDED, bpy.props.BoolProperty(
        name="Output Settings",
        description="Expand Output Settings",
        default=True,
        options={'HIDDEN'},
    ))
    setattr(bpy.types.Scene, PROP_GRAB_EXPANDED, bpy.props.BoolProperty(
        name="Grab Options",
        description="Expand Grab Options",
        default=True,
        options={'HIDDEN'},
    ))
    setattr(bpy.types.Scene, PROP_PREVIEW_EXPANDED, bpy.props.BoolProperty(
        name="Preview Options",
        description="Expand Preview Options",
        default=False,
        options={'HIDDEN'},
    ))
    setattr(bpy.types.Scene, PROP_DEPTH_MIDPOINT, bpy.props.FloatProperty(
        name="Depth Zero Offset",
        description=(
            "Shift the EXR depth zero-point into the capture volume. "
            "0 = surface is zero (all depths negative). "
            "0.5 = midplane is zero (geometry in front is positive, behind is negative). "
            "Has no effect on the normalised PNG Z output."
        ),
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
    ))
    setattr(bpy.types.Scene, PROP_OUTPUT_NAME, bpy.props.StringProperty(
        name="Name",
        description="Filename prefix for all outputs of this grab (overrides previous files when unchanged)",
        default="",
    ))
    setattr(bpy.types.Scene, PROP_FIT_FROM_VIEW, bpy.props.BoolProperty(
        name="From View",
        description="Align the plane to the current viewport before fitting to selection",
        default=False,
    ))
    setattr(bpy.types.Scene, PROP_FIT_MARGIN, bpy.props.FloatProperty(
        name="Fit Margin",
        description=(
            "Expand the capture plane by this distance (metres) on every side when "
            "using Fit to Selection. Adds visible buffer gap between the mesh edge "
            "and the plane edge, and extends the capture depth by the same amount "
            "at both ends."
        ),
        default=0.0,
        min=0.0,
        soft_max=1.0,
        unit='LENGTH',
    ))
    setattr(bpy.types.Scene, PROP_LAST_GRAB_PREFIX, bpy.props.StringProperty(
        name="Last Grab Prefix",
        description="Filename prefix used by the most recent QuadGrab (used by Sculpt Alpha)",
        default="",
        options={'HIDDEN'},
    ))


def unregister() -> None:
    delattr(bpy.types.Scene, PROP_OUTPUT_DIR)
    delattr(bpy.types.Scene, PROP_RENDER_SIZE)
    delattr(bpy.types.Scene, PROP_USE_TIMESTAMP)
    delattr(bpy.types.Scene, PROP_USE_DEPTH)
    delattr(bpy.types.Scene, PROP_USE_DEPTH_EXR)
    delattr(bpy.types.Scene, PROP_USE_DEPTH_EXR_RAW)
    delattr(bpy.types.Scene, PROP_USE_COMPOSITE)
    delattr(bpy.types.Scene, PROP_USE_PBR)
    delattr(bpy.types.Scene, PROP_MAX_DEPTH)
    delattr(bpy.types.Scene, PROP_USE_PREVIEW_PLANE)
    delattr(bpy.types.Scene, PROP_DISPLACE_PLANE)
    delattr(bpy.types.Scene, PROP_USE_DEBUG)
    delattr(bpy.types.Scene, PROP_CACHED_SETTINGS)
    delattr(bpy.types.Scene, PROP_SHOW_OVERLAY)
    delattr(bpy.types.Scene, PROP_DEBUG_EXPANDED)
    delattr(bpy.types.Scene, PROP_OUTPUT_EXPANDED)
    delattr(bpy.types.Scene, PROP_GRAB_EXPANDED)
    delattr(bpy.types.Scene, PROP_PREVIEW_EXPANDED)
    delattr(bpy.types.Scene, PROP_DEPTH_MIDPOINT)
    delattr(bpy.types.Scene, PROP_OUTPUT_NAME)
    delattr(bpy.types.Scene, PROP_FIT_FROM_VIEW)
    delattr(bpy.types.Scene, PROP_FIT_MARGIN)
    delattr(bpy.types.Scene, PROP_LAST_GRAB_PREFIX)
