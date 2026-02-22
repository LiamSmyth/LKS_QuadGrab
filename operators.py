import bpy

import importlib
import math
import mathutils
from . import operators
from . import properties
from . import register_quadgrab
from . import ui
import time
import pathlib
# def ops

CLIP_START = 0.01


def build_comp_graph(timestamp: str):
    # Enable compositor nodes if not already enabled (Blender 4.2 requirement)
    if not bpy.context.scene.use_nodes:
        bpy.context.scene.use_nodes = True
    compgraph: bpy.types.CompositorNodeTree = bpy.context.scene.node_tree
    for compnode in compgraph.nodes:
        compgraph.nodes.remove(compnode)

    n_comp: bpy.types.CompositorNodeComposite = compgraph.nodes.new(
        type="CompositorNodeComposite")
    n_img: bpy.types.CompositorNodeRLayers = compgraph.nodes.new(
        type="CompositorNodeRLayers")
    n_img.location = [-1000, 0]

    compgraph.links.new(n_comp.inputs["Image"], n_img.outputs["Image"])
    compgraph.links.new(n_comp.inputs["Alpha"], n_img.outputs["Alpha"])
    # compgraph.links.new(n_comp.inputs["Z"], n_img.outputs["Depth"])

    # If using timestamp (from scene prop) apped time to filename

    def setup_zdepth_graph() -> bpy.types.CompositorNode:
        """
        DEPTH OUTPUT GRAPH SETUP
        creates nodes "zdepth_inverted" and "zdepth_normalized"
        """
        n_invert_z: bpy.types.CompositorNodeInvert = compgraph.nodes.new(
            "CompositorNodeInvert")
        n_invert_z.name = "zdepth_inverted"
        n_invert_z.label = "zdepth_inverted"
        n_invert_z.location = (-700, 0)
        compgraph.links.new(n_invert_z.inputs[1], n_img.outputs["Depth"])
        n_normalize_z: bpy.types.CompositorNodeNormalize = compgraph.nodes.new(
            "CompositorNodeNormalize")
        n_normalize_z.name = "zdepth_normalized"
        n_normalize_z.label = "zdepth_normalized"
        n_normalize_z.location = (-500, 0)
        compgraph.links.new(n_normalize_z.inputs[0], n_invert_z.outputs[0])
    setup_zdepth_graph()

    def setup_compoutput_png(timestamp: str):
        """
        ##### Setup PNG Linear File Output
        """
        n_file_png: bpy.types.CompositorNodeOutputFile = compgraph.nodes.new(
            type="CompositorNodeOutputFile")
        n_file_png.name = "File Out PNG Linear"
        n_file_png.label = "File Out PNG Linear"

        n_file_png.base_path = getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR)
        n_file_png.location = [0, -150]
        # node settings
        png_settings: bpy.types.ImageFormatSettings = n_file_png.format
        png_settings.file_format = "PNG"
        png_settings.color_depth = "16"
        png_settings.compression = 100
        png_settings.color_management = "OVERRIDE"
        png_settings.view_settings.view_transform = 'Raw'

        n_file_png_slots: bpy.types.CompositorNodeOutputFileFileSlots = n_file_png.file_slots
        # Make file output slots
        png_comp_slot: bpy.types.NodeOutputFileSlotFile = n_file_png_slots["Image"]
        png_comp_slot.path = timestamp + "Composite"
        n_file_png_slots.new(timestamp + "Z")
        n_file_png_slots.new(timestamp + "Normal")
        n_file_png_slots.new(timestamp + "BaseColor")
        n_file_png_slots.new(timestamp + "AO")
        n_file_png_slots.new(timestamp + "Roughness")
        n_file_png_slots.new(timestamp + "Metallic")
        n_file_png_slots.new(timestamp + "Specular")
        n_file_png_slots.new(timestamp + "Alpha")

        # Connect PNG (Linear) Outputs
        if (getattr(bpy.context.scene, properties.PROP_USE_DEPTH)):
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Z"], compgraph.nodes["zdepth_normalized"].outputs[0])
        if (getattr(bpy.context.scene, properties.PROP_USE_PBR)):
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Normal"], n_img.outputs["QG_AOV_Normal"])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "BaseColor"], n_img.outputs["QG_AOV_BaseColor"])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "AO"], n_img.outputs["AO"])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Alpha"], n_img.outputs["Alpha"])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Roughness"], n_img.outputs["QG_AOV_Roughness"])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Metallic"], n_img.outputs["QG_AOV_Metallic"])
            compgraph.links.new(
                n_file_png.inputs[timestamp + "Specular"], n_img.outputs["QG_AOV_specular"])

        """
        ##### Setup PNG SRGB File Output
        """
        n_file_png_srgb: bpy.types.CompositorNodeOutputFile = compgraph.nodes.new(
            type="CompositorNodeOutputFile")
        n_file_png_srgb.name = "File Out PNG SRGB"
        n_file_png_srgb.label = "File Out PNG SRGB"

        png_settings: bpy.types.ImageFormatSettings = n_file_png_srgb.format
        png_settings.file_format = "PNG"
        png_settings.color_depth = "16"
        png_settings.compression = 100
        png_settings.color_management = "OVERRIDE"
        png_settings.view_settings.view_transform = 'Standard'

        n_file_png_srgb.base_path = getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR)
        n_file_png_srgb.location = [0, -250]
        n_file_png_srgb_slots: bpy.types.CompositorNodeOutputFileFileSlots = n_file_png_srgb.file_slots

        # Make file output slots
        png_srgb_comp_slot: bpy.types.NodeOutputFileSlotFile = n_file_png_srgb_slots["Image"]
        png_srgb_comp_slot.path = timestamp + "Composite"
        n_file_png_srgb_slots.new(timestamp + "BaseColor_srgb")

        if (getattr(bpy.context.scene, properties.PROP_USE_PBR)):
            compgraph.links.new(
                n_file_png_srgb.inputs[timestamp + "BaseColor_srgb"], n_img.outputs["QG_AOV_BaseColor"])

    setup_compoutput_png(timestamp=timestamp)

    def setup_compoutput_png_tonemapped():
        """
        # Set up tonemapped PNG File Output


        """
        n_file_png_tonemapped: bpy.types.CompositorNodeOutputFile = compgraph.nodes.new(
            type="CompositorNodeOutputFile")
        n_file_png_tonemapped.name = "File Out PNG Tonemapped"
        n_file_png_tonemapped.label = "File Out PNG Tonemapped"
        n_file_png_tonemapped.location = [0, -400]
        n_file_png_tonemapped.base_path = getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR)
        png_tonemapped_settings: bpy.types.ImageFormatSettings = n_file_png_tonemapped.format
        png_tonemapped_settings.file_format = "PNG"
        png_tonemapped_settings.color_depth = "16"
        png_tonemapped_settings.compression = 100
        n_file_png_tonemapped.file_slots["Image"].path = timestamp + "Composite"
        if (getattr(bpy.context.scene, properties.PROP_USE_COMPOSITE)):
            compgraph.links.new(
                n_file_png_tonemapped.inputs["Image"], n_img.outputs["Image"])
    setup_compoutput_png_tonemapped()

    def setup_compoutput_exr():
        """
        # Setup EXR File Output


        """
        # SETUP HDR Height Graph
        n_max: bpy.types.CompositorNodeMath = compgraph.nodes.new(
            type="CompositorNodeMath")
        n_max.location = (-500, -200)
        n_max.label = "EXR Height Max"
        n_max.name = "EXR Height Max"
        n_max.operation = 'MAXIMUM'
        n_max.inputs[1].default_value = getattr(bpy.context.scene, properties.PROP_MAX_DEPTH) * -1
        compgraph.links.new(
            n_max.inputs[0], compgraph.nodes["zdepth_inverted"].outputs[0])

        n_file_exr: bpy.types.CompositorNodeOutputFile = compgraph.nodes.new(
            type="CompositorNodeOutputFile")
        n_file_exr.name = "File Out EXR"
        n_file_exr.label = "File Out EXR"
        n_file_exr.location = [0, -600]
        n_file_exr.file_slots.new(name="Depth_Normalized")
        n_file_exr.base_path = getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR)
        n_file_exr.format.file_format = "OPEN_EXR"
        n_file_exr.format.color_depth = "32"
        n_file_exr.format.compression = 100
        n_file_exr.file_slots["Image"].path = timestamp + "Depth_Raw"
        n_file_exr.file_slots[1].path = timestamp + "Depth_Normalized_Scale-" + \
            str(getattr(bpy.context.scene, properties.PROP_MAX_DEPTH))
        if (getattr(bpy.context.scene, properties.PROP_USE_DEPTH_EXR)):
            compgraph.links.new(
                n_file_exr.inputs["Image"], n_max.outputs[0])
            compgraph.links.new(
                n_file_exr.inputs["Depth_Normalized"], compgraph.nodes['zdepth_normalized'].outputs[0])
    setup_compoutput_exr()


def setup_pbr_aovs_mats():
    for mat in bpy.data.materials:
        mat: bpy.types.Material = mat
        nt: bpy.types.NodeTree = mat.node_tree
        n_shader: bpy.types.ShaderNodeBsdfPrincipled = None
        try:
            n_shader = nt.nodes["Material Output"].inputs[0].links[0].from_node
            # print(n_shader.name)
        except:
            print("Couldn't add PBR AOVs to " +
                  mat.name + ", not Principled BSDF")
            continue

        # Clear old aovs first
        for n in nt.nodes:
            # print(n.name)
            if n.name.count("QG_AOV") != 0:
                nt.nodes.remove(n)

        # Setup AOV Nodes
        n_aov_bc: bpy.types.ShaderNodeOutputAOV = nt.nodes.new(
            type="ShaderNodeOutputAOV")
        n_aov_bc.name = "QG_AOV_BaseColor"
        n_aov_bc.aov_name = "QG_AOV_BaseColor"
        n_aov_bc.label = "QG_AOV_BaseColor"
        n_aov_bc.location = (2000, 0)

        n_aov_normal: bpy.types.ShaderNodeOutputAOV = nt.nodes.new(
            type="ShaderNodeOutputAOV")
        n_aov_normal.name = "QG_AOV_Normal"
        n_aov_normal.aov_name = "QG_AOV_Normal"
        n_aov_normal.label = "QG_AOV_Normal"
        n_aov_normal.location = (2000, -100)

        n_aov_specular: bpy.types.ShaderNodeOutputAOV = nt.nodes.new(
            type="ShaderNodeOutputAOV")
        n_aov_specular.name = "QG_AOV_specular"
        n_aov_specular.aov_name = "QG_AOV_specular"
        n_aov_specular.label = "QG_AOV_specular"
        n_aov_specular.location = (2000, -200)

        n_aov_roughness: bpy.types.ShaderNodeOutputAOV = nt.nodes.new(
            type="ShaderNodeOutputAOV")
        n_aov_roughness.name = "QG_AOV_Roughness"
        n_aov_roughness.aov_name = "QG_AOV_Roughness"
        n_aov_roughness.label = "QG_AOV_Roughness"
        n_aov_roughness.location = (2000, -300)

        n_aov_metallic: bpy.types.ShaderNodeOutputAOV = nt.nodes.new(
            type="ShaderNodeOutputAOV")
        n_aov_metallic.name = "QG_AOV_Metallic"
        n_aov_metallic.aov_name = "QG_AOV_Metallic"
        n_aov_metallic.label = "QG_AOV_Metallic"
        n_aov_metallic.location = (2000, -400)

        bc_input: bpy.types.NodeInputs = n_shader.inputs.get(
            "Base Color") or n_shader.inputs.get("BC")
        normal_input: bpy.types.NodeInputs = n_shader.inputs.get(
            "Normal") or n_shader.inputs.get("NM")
        specular_input: bpy.types.NodeInputs = n_shader.inputs.get(
            "Specular IOR Level") or n_shader.inputs.get("Specular")
        roughness_input: bpy.types.NodeInputs = n_shader.inputs.get(
            "Roughness")
        metallic_input: bpy.types.NodeInputs = n_shader.inputs.get("Metallic")

        if bc_input is not None:
            try:
                nt.links.new(
                    n_aov_bc.inputs[0],  bc_input.links[0].from_socket)
            except:
                n_aov_bc.inputs[0].default_value = bc_input.default_value
                pass
        if normal_input is not None:
            def setup_mat_normal_aov():
                nt.links.new(
                    n_aov_normal.inputs[0],  normal_input.links[0].from_socket)

                n_normal_transform: bpy.types.ShaderNodeVectorTransform = nt.nodes.new(
                    type="ShaderNodeVectorTransform")
                n_normal_transform.name = "QG_AOV_NormalTransform"
                n_normal_transform.label = "QG_AOV_NormalTransform"
                n_normal_transform.convert_from = "WORLD"
                n_normal_transform.convert_to = "CAMERA"
                n_normal_transform.location = (1000, -100)
                nt.links.new(
                    n_normal_transform.inputs[0], normal_input.links[0].from_socket)

                n_normal_mult: bpy.types.ShaderNodeVectorMath = nt.nodes.new(
                    type="ShaderNodeVectorMath")
                n_normal_mult.name = "QG_AOV_NormalMult"
                n_normal_mult.label = "QG_AOV_NormalMult"
                n_normal_mult.location = (1200, -100)
                n_normal_mult.operation = "MULTIPLY"
                n_normal_mult.inputs[1].default_value = [0.5, 0.5, -0.5]
                nt.links.new(
                    n_normal_mult.inputs[0], n_normal_transform.outputs[0])

                n_normal_add: bpy.types.ShaderNodeVectorMath = nt.nodes.new(
                    type="ShaderNodeVectorMath")
                n_normal_add.name = "QG_AOV_NormalAdd"
                n_normal_add.label = "QG_AOV_NormalAdd"
                n_normal_add.location = (1400, -100)
                n_normal_add.operation = "ADD"
                n_normal_add.inputs[1].default_value = [0.5, 0.5, 0.5]
                nt.links.new(
                    n_normal_add.inputs[0], n_normal_mult.outputs[0])

                nt.links.new(
                    input=n_aov_normal.inputs[0], output=n_normal_add.outputs[0], verify_limits=True)

            def setup_geometry_normal_aov():
                print("Setting up geo normal")
                n_normal_geometry: bpy.types.ShaderNodeNewGeometry = nt.nodes.new(
                    type="ShaderNodeNewGeometry")
                n_normal_geometry.name = "QG_AOV_NormalGeometry"
                n_normal_geometry.label = "QG_AOV_NormalGeometry"
                n_normal_geometry.location = (800, -100)

                n_normal_transform: bpy.types.ShaderNodeVectorTransform = nt.nodes.new(
                    type="ShaderNodeVectorTransform")
                n_normal_transform.name = "QG_AOV_NormalTransform"
                n_normal_transform.label = "QG_AOV_NormalTransform"
                n_normal_transform.convert_from = "WORLD"
                n_normal_transform.convert_to = "CAMERA"
                n_normal_transform.location = (1000, -100)
                nt.links.new(
                    n_normal_transform.inputs[0], n_normal_geometry.outputs["Normal"])

                n_normal_mult: bpy.types.ShaderNodeVectorMath = nt.nodes.new(
                    type="ShaderNodeVectorMath")
                n_normal_mult.name = "QG_AOV_NormalMult"
                n_normal_mult.label = "QG_AOV_NormalMult"
                n_normal_mult.location = (1200, -100)
                n_normal_mult.operation = "MULTIPLY"
                n_normal_mult.inputs[1].default_value = [0.5, 0.5, -0.5]
                nt.links.new(
                    n_normal_mult.inputs[0], n_normal_transform.outputs[0])

                n_normal_add: bpy.types.ShaderNodeVectorMath = nt.nodes.new(
                    type="ShaderNodeVectorMath")
                n_normal_add.name = "QG_AOV_NormalAdd"
                n_normal_add.label = "QG_AOV_NormalAdd"
                n_normal_add.location = (1400, -100)
                n_normal_add.operation = "ADD"
                n_normal_add.inputs[1].default_value = [0.5, 0.5, 0.5]
                nt.links.new(
                    n_normal_add.inputs[0], n_normal_mult.outputs[0])

                nt.links.new(
                    input=n_aov_normal.inputs[0], output=n_normal_add.outputs[0], verify_limits=True)

            try:
                setup_mat_normal_aov()
            except:
                setup_geometry_normal_aov()

        if specular_input is not None:
            try:
                nt.links.new(
                    n_aov_specular.inputs[1],  specular_input.links[0].from_socket)
            except:
                n_aov_specular.inputs[1].default_value = specular_input.default_value
                pass
        if roughness_input is not None:
            try:
                nt.links.new(
                    n_aov_roughness.inputs[1],  roughness_input.links[0].from_socket)
            except:
                n_aov_roughness.inputs[1].default_value = roughness_input.default_value
                pass
        if metallic_input is not None:
            try:
                nt.links.new(
                    n_aov_metallic.inputs[1],  metallic_input.links[0].from_socket)
            except:
                n_aov_metallic.inputs[1].default_value = metallic_input.default_value
                pass


class OBJECT_OT_LKS_QuadGrab(bpy.types.Operator):
    """QuadGrab!"""
    bl_idname = "object.lks_quad_grab"
    bl_label = "LKS QuadGrab"

    @classmethod
    def poll(self, context):
        if context.area.type == 'VIEW_3D':
            return True
        return False

    def execute(self, context):
        timestamp = ""
        if getattr(bpy.context.scene, properties.PROP_USE_TIMESTAMP):
            timestamp = time.strftime("%H-%M-%S") + "_"

        new_scene: bpy.types.Scene = bpy.context.scene.copy()
        new_scene.name = "quadgrab_scene"

        ref_obj = bpy.context.view_layer.objects.active
        if ref_obj is None:
            return ("CANCELLED")

        def make_camera_and_set_xform(obj) -> bpy.types.Object:
            rot = obj.rotation_euler
            min_x = math.inf
            min_y = math.inf
            min_z = math.inf
            max_x = -math.inf
            max_y = -math.inf
            max_z = -math.inf

            for vec in obj.bound_box:
                min_x = min(vec[0], min_x)
                min_y = min(vec[1], min_y)
                min_z = min(vec[2], min_z)
                max_x = max(vec[0], max_x)
                max_y = max(vec[1], max_y)
                max_z = max(vec[2], max_z)

            scale = ((max_x - min_x) * obj.scale[0], (max_y - min_y)
                     * obj.scale[1], (max_z - min_z) * obj.scale[2])
            centroid = ((max_x - min_x) / 2 + min_x + obj.location[0], (
                max_y - min_y) / 2 + min_y + obj.location[1], (max_z - min_z) / 2 + min_z + obj.location[2])

            cam: bpy.types.Camera = bpy.data.cameras.new(
                name="LKS QuadGrab Cam")
            cam_obj: bpy.types.Object = bpy.data.objects.new(
                "LKS QuadGrab Cam Obj", cam)

            cam.ortho_scale = max(obj.dimensions[0], obj.dimensions[2])
            cam.type = 'ORTHO'

            # Move the camera above the object
            cam_obj.location = (centroid)
            # cam_obj.location = (centroid[0], centroid[1], max_z + scale[2])
            cam_obj.rotation_euler = rot
            # Move the camera back along its local forward vector z axis to prevent z fighting by a constant of 0.01
            # cam_obj.location = cam_obj.location - \
            #    cam_obj.matrix_world.to_3x3() @ mathutils.Vector((0, 0, -CLIP_START * 2.0))

            bpy.context.scene.collection.objects.link(cam_obj)
            return (cam_obj)

        cam_obj: bpy.types.Object = make_camera_and_set_xform(ref_obj)
        cam: bpy.types.Camera = cam_obj.data
        cam.clip_start = CLIP_START
        cam.clip_end = getattr(bpy.context.scene, properties.PROP_MAX_DEPTH)
        rendersettings: bpy.types.RenderSettings = bpy.context.scene.render

        rendersettings.resolution_x = getattr(bpy.context.scene, properties.PROP_RENDER_SIZE)
        rendersettings.resolution_y = getattr(bpy.context.scene, properties.PROP_RENDER_SIZE)
        rendersettings.resolution_percentage = 100
        rendersettings.engine = 'CYCLES'
        rendersettings.film_transparent = True

        vl: bpy.types.ViewLayer = bpy.context.view_layer
        vl.use_pass_normal = True
        vl.use_pass_z = True
        vl.use_pass_diffuse_color = True
        vl.use_pass_glossy_color = True
        vl.use_pass_ambient_occlusion = True

        # if aovs are not already added, add them
        aovs_exist = False
        for aov in vl.aovs:
            if aov.name.count("QG_AOV") != 0:
                aovs_exist = True
                break
        if aovs_exist == False:
            aov_bc: bpy.types.AOV = vl.aovs.add()
            aov_bc.name = "QG_AOV_BaseColor"
            aov_normal: bpy.types.AOV = vl.aovs.add()
            aov_normal.name = "QG_AOV_Normal"
            aov_specular: bpy.types.AOV = vl.aovs.add()
            aov_specular.name = "QG_AOV_specular"
            aov_specular.type = "VALUE"
            aov_roughness: bpy.types.AOV = vl.aovs.add()
            aov_roughness.name = "QG_AOV_Roughness"
            aov_roughness.type = "VALUE"
            aov_metallic: bpy.types.AOV = vl.aovs.add()
            aov_metallic.name = "QG_AOV_Metallic"
            aov_metallic.type = "VALUE"

        bpy.context.scene.camera = cam_obj

        setup_pbr_aovs_mats()
        build_comp_graph(timestamp=timestamp)

        # Hide active object so it doesn't contribute to lighting
        ref_obj.hide_render = True

        # Ensure timeline is at frame 0 before rendering to generate filenames with 0000 suffix
        bpy.context.scene.frame_set(0)

        print("rendering    ")
        bpy.ops.render.render()
        print("finished rendering")

        ref_obj.hide_render = False

        def add_preview_plane() -> bpy.types.Object:
            bpy.ops.mesh.primitive_grid_add(
                location=cam_obj.location, rotation=cam_obj.rotation_euler, size=cam.ortho_scale,)
            ob_grid: bpy.types.Object = bpy.context.view_layer.objects.active
            ob_grid.hide_render = True
            ob_grid.name = "QuadGrab Preview Plane"
            bpy.ops.object.shade_smooth()
            ob_mesh: bpy.types.Mesh = ob_grid.data
            if hasattr(ob_mesh, "use_auto_smooth"):
                ob_mesh.use_auto_smooth = True
                ob_mesh.auto_smooth_angle = math.pi

            if getattr(bpy.context.scene, properties.PROP_DISPLACE_PLANE):
                subsurf: bpy.types.SubsurfModifier = ob_grid.modifiers.new(
                    type="SUBSURF", name="QuadGrab_Subsurf")

                subsurf.subdivision_type = "SIMPLE"
                subsurf.levels = 4
                subsurf.quality = 1
                ob_grid.cycles.use_adaptive_subdivision = True

                if getattr(bpy.context.scene, properties.PROP_USE_DEPTH_EXR):
                    displace: bpy.types.DisplaceModifier = ob_grid.modifiers.new(
                        type="DISPLACE", name="QuadGrab_Displace")
                    displace.mid_level = 1
                    displace.strength = 1
                    displace.texture_coords = "UV"
                    disp_tex: bpy.types.ImageTexture = bpy.data.textures.new(
                        name="QuadGrab_DispTex", type="IMAGE")
                    if hasattr(disp_tex, "use_clamp"):
                        disp_tex.use_clamp = False
                    elif hasattr(disp_tex, "extension"):
                        disp_tex.extension = 'EXTEND'
                    disp_img: bpy.types.Image = bpy.data.images.load(
                        filepath=getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR) + timestamp + "Depth_Raw0000.exr")
                    displace.texture = disp_tex
                    # bpy.ops.image.open(
                    #    filepath=getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR) + timestamp + "Depth_Raw0000.exr")
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

            # Basecolor
            img_basecolor: bpy.types.Image = bpy.data.images.load(
                filepath=getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR) + timestamp + "BaseColor_srgb0000.png")
            n_img_basecolor: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_basecolor.name = "QG_BaseColor"
            n_img_basecolor.location = [-800, 0]
            n_img_basecolor.image = img_basecolor
            nt.links.new(input=shader.inputs["Base Color"],
                         output=n_img_basecolor.outputs[0])
            # Normal
            img_normal: bpy.types.Image = bpy.data.images.load(
                filepath=getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR) + timestamp + "Normal0000.png")
            n_img_normal: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_normal.name = "QG_Normal"
            n_img_normal.location = [-800, -400]
            n_img_normal.image = img_normal
            n_img_normal.image.colorspace_settings.name = "Non-Color"

            n_normal: bpy.types.ShaderNodeNormalMap = nt.nodes.new(
                type="ShaderNodeNormalMap")
            n_normal.location = [-500, -400]

            nt.links.new(input=n_normal.inputs[1],
                         output=n_img_normal.outputs[0])
            nt.links.new(input=shader.inputs["Normal"],
                         output=n_normal.outputs[0])
            # Hookup Roughness
            img_roughness: bpy.types.Image = bpy.data.images.load(
                filepath=getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR) + timestamp + "Roughness0000.png")
            n_img_roughness: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_roughness.name = "QG_Roughness"
            n_img_roughness.location = [-800, -800]
            n_img_roughness.image = img_roughness
            n_img_roughness.image.colorspace_settings.name = "Non-Color"
            nt.links.new(input=shader.inputs["Roughness"],
                         output=n_img_roughness.outputs[0])
            # Hookup Metallic
            img_metallic: bpy.types.Image = bpy.data.images.load(
                filepath=getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR) + timestamp + "Metallic0000.png")
            n_img_metallic: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_metallic.name = "QG_Metallic"
            n_img_metallic.location = [-800, -1200]
            n_img_metallic.image = img_metallic
            n_img_metallic.image.colorspace_settings.name = "Non-Color"
            nt.links.new(input=shader.inputs["Metallic"],
                         output=n_img_metallic.outputs[0])
            # Hookup Specular
            img_specular: bpy.types.Image = bpy.data.images.load(
                filepath=getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR) + timestamp + "Specular0000.png")
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
            # Hookup Alpha
            if hasattr(mat, "show_transparent_back"):
                mat.show_transparent_back = False
            if hasattr(mat, "blend_method"):
                mat.blend_method = "CLIP"
            img_alpha: bpy.types.Image = bpy.data.images.load(
                filepath=getattr(bpy.context.scene, properties.PROP_OUTPUT_DIR) + timestamp + "Alpha0000.png")
            n_img_alpha: bpy.types.ShaderNodeTexImage = nt.nodes.new(
                type="ShaderNodeTexImage")
            n_img_alpha.name = "QG_Alpha"
            n_img_alpha.location = [-800, -2000]
            n_img_alpha.image = img_alpha
            n_img_alpha.image.colorspace_settings.name = "Non-Color"
            nt.links.new(input=shader.inputs["Alpha"],
                         output=n_img_alpha.outputs[0])
            return mat
        if getattr(bpy.context.scene, properties.PROP_USE_PREVIEW_PLANE):
            preview_plane: bpy.types.Object = add_preview_plane()
            if getattr(bpy.context.scene, properties.PROP_USE_PBR):
                mat: bpy.types.Material = add_preview_mat()
                preview_plane.active_material = mat

        debug = getattr(bpy.context.scene, properties.PROP_USE_DEBUG)
        if not debug:
            bpy.data.objects.remove(cam_obj)
            bpy.data.cameras.remove(cam)
            bpy.data.scenes.remove(new_scene)

        return {'FINISHED'}


class OBJECT_OT_LKS_QuadGrabMakePlane(bpy.types.Operator):
    """QuadGrab!"""
    bl_idname = "object.lks_quad_grab_make_plane"
    bl_label = "Make a reference plane for use with QuadGrab"

    @classmethod
    def poll(self, context):
        if context.area.type == 'VIEW_3D':
            return True
        return False

    def execute(self, context):
        # Make a plane exactly 1 unit in size and select it, and make it active
        # Cache the location of the active object
        ref_obj = bpy.context.view_layer.objects.active
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        bpy.context.view_layer.objects.active.name = "QuadGrab Reference Plane"
        bpy.context.view_layer.objects.active.select_set(True)
        # Move the quadgrab plane to the location of the active object
        if ref_obj:
            bpy.context.view_layer.objects.active.location = ref_obj.location

        return {'FINISHED'}


class OBJECT_OT_LKS_QuadGrabCleanup(bpy.types.Operator):
    """QuadGrab!"""
    bl_idname = "object.lks_quad_grab_cleanup"
    bl_label = "Cleanup QuadGrab Objects"

    @classmethod
    def poll(self, context):
        # if context.area.type == 'VIEW_3D':
        # return True
        # return False
        return True

    def execute(self, context):
        for obj in bpy.data.objects:
            obj: bpy.types.Object = obj
            if obj.name.count("QuadGrab") != 0:
                bpy.data.objects.remove(obj, do_unlink=True)

        for texture in bpy.data.textures:
            if texture.name.count("QuadGrab") != 0:
                bpy.data.textures.remove(texture, do_unlink=True)

        for image in bpy.data.images:
            if image.name.count("QuadGrab") != 0:
                bpy.data.images.remove(image, do_unlink=True)

        for mat in bpy.data.materials:
            if mat.name.count("QG_") != 0:
                bpy.data.materials.remove(mat, do_unlink=True)

            else:
                if mat:
                    if mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.name.count("QG_AOV") != 0:
                                mat.node_tree.nodes.remove(node)
                else:
                    continue

        for scene in bpy.data.scenes:
            if scene.name.count("quadgrab") != 0:
                bpy.data.scenes.remove(scene, do_unlink=True)

        for aov in list(bpy.context.view_layer.aovs):
            if aov.name.count("QG_AOV") != 0:
                bpy.context.view_layer.aovs.remove(aov)

        bpy.ops.outliner.orphans_purge(do_recursive=True)
        return {'FINISHED'}


# def ops to register
opsToRegister = (
    OBJECT_OT_LKS_QuadGrab,
    OBJECT_OT_LKS_QuadGrabCleanup,
    OBJECT_OT_LKS_QuadGrabMakePlane
)

# register ops


def register():
    # Register classes
    for op in opsToRegister:
        bpy.utils.register_class(op)
    pass


def unregister():
    for op in reversed(opsToRegister):
        bpy.utils.unregister_class(op)
