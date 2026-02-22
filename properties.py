import bpy

PROP_OUTPUT_DIR = "lks_quadgrab_output_dir"
PROP_RENDER_SIZE = "lks_quadgrab_render_size"
PROP_USE_TIMESTAMP = "lks_quadgrab_use_timestamp"
PROP_USE_DEPTH = "lks_quadgrab_use_depth"
PROP_USE_DEPTH_EXR = "lks_quadgrab_use_depth_exr"
PROP_USE_COMPOSITE = "lks_quadgrab_use_composite"
PROP_USE_PBR = "lks_quadgrab_use_pbr"
PROP_MAX_DEPTH = "lks_quadgrab_max_depth"
PROP_USE_PREVIEW_PLANE = "lks_quadgrab_use_preview_plane"
PROP_DISPLACE_PLANE = "lks_quadgrab_displace_plane"
PROP_USE_DEBUG = "lks_quadgrab_use_debug"


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
        name="DepthEXR",
        description="Output ZDepth",
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


def unregister() -> None:
    delattr(bpy.types.Scene, PROP_OUTPUT_DIR)
    delattr(bpy.types.Scene, PROP_RENDER_SIZE)
    delattr(bpy.types.Scene, PROP_USE_TIMESTAMP)
    delattr(bpy.types.Scene, PROP_USE_DEPTH)
    delattr(bpy.types.Scene, PROP_USE_DEPTH_EXR)
    delattr(bpy.types.Scene, PROP_USE_COMPOSITE)
    delattr(bpy.types.Scene, PROP_USE_PBR)
    delattr(bpy.types.Scene, PROP_MAX_DEPTH)
    delattr(bpy.types.Scene, PROP_USE_PREVIEW_PLANE)
    delattr(bpy.types.Scene, PROP_DISPLACE_PLANE)
    delattr(bpy.types.Scene, PROP_USE_DEBUG)
