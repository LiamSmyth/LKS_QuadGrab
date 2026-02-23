"""PBR AOV material setup for QuadGrab."""

from __future__ import annotations

import bpy


def setup_pbr_aovs_mats() -> tuple[int, int]:
    """Hook AOV output nodes into every local Principled BSDF material.

    Returns ``(updated, skipped_linked)`` counts so callers can report
    to the user how many linked materials were skipped.
    """
    updated: int = 0
    skipped_linked: int = 0
    for mat in bpy.data.materials:
        mat: bpy.types.Material = mat

        # Linked materials have read-only node trees — skip them.
        if mat.library is not None:
            skipped_linked += 1
            print(f"QuadGrab: skipping linked material '{mat.name}'")
            continue

        nt: bpy.types.NodeTree = mat.node_tree
        n_shader: bpy.types.ShaderNodeBsdfPrincipled | None = None
        try:
            n_shader = nt.nodes["Material Output"].inputs[0].links[0].from_node
        except Exception:
            print("Couldn't add PBR AOVs to " +
                  mat.name + ", not Principled BSDF")
            continue

        # Clear old aovs first
        for n in nt.nodes:
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

        bc_input = n_shader.inputs.get(
            "Base Color") or n_shader.inputs.get("BC")
        normal_input = n_shader.inputs.get(
            "Normal") or n_shader.inputs.get("NM")
        specular_input = n_shader.inputs.get(
            "Specular IOR Level") or n_shader.inputs.get("Specular")
        roughness_input = n_shader.inputs.get("Roughness")
        metallic_input = n_shader.inputs.get("Metallic")

        if bc_input is not None:
            try:
                nt.links.new(n_aov_bc.inputs[0], bc_input.links[0].from_socket)
            except Exception:
                n_aov_bc.inputs[0].default_value = bc_input.default_value

        if normal_input is not None:
            def _setup_mat_normal_aov() -> None:
                nt.links.new(
                    n_aov_normal.inputs[0], normal_input.links[0].from_socket)

                n_normal_transform = nt.nodes.new(
                    type="ShaderNodeVectorTransform")
                n_normal_transform.name = "QG_AOV_NormalTransform"
                n_normal_transform.label = "QG_AOV_NormalTransform"
                n_normal_transform.convert_from = "WORLD"
                n_normal_transform.convert_to = "CAMERA"
                n_normal_transform.location = (1000, -100)
                nt.links.new(
                    n_normal_transform.inputs[0], normal_input.links[0].from_socket)

                n_normal_mult = nt.nodes.new(type="ShaderNodeVectorMath")
                n_normal_mult.name = "QG_AOV_NormalMult"
                n_normal_mult.label = "QG_AOV_NormalMult"
                n_normal_mult.location = (1200, -100)
                n_normal_mult.operation = "MULTIPLY"
                n_normal_mult.inputs[1].default_value = [0.5, 0.5, -0.5]
                nt.links.new(
                    n_normal_mult.inputs[0], n_normal_transform.outputs[0])

                n_normal_add = nt.nodes.new(type="ShaderNodeVectorMath")
                n_normal_add.name = "QG_AOV_NormalAdd"
                n_normal_add.label = "QG_AOV_NormalAdd"
                n_normal_add.location = (1400, -100)
                n_normal_add.operation = "ADD"
                n_normal_add.inputs[1].default_value = [0.5, 0.5, 0.5]
                nt.links.new(n_normal_add.inputs[0], n_normal_mult.outputs[0])

                nt.links.new(
                    input=n_aov_normal.inputs[0], output=n_normal_add.outputs[0], verify_limits=True)

            def _setup_geometry_normal_aov() -> None:
                print("Setting up geo normal")
                n_normal_geometry = nt.nodes.new(type="ShaderNodeNewGeometry")
                n_normal_geometry.name = "QG_AOV_NormalGeometry"
                n_normal_geometry.label = "QG_AOV_NormalGeometry"
                n_normal_geometry.location = (800, -100)

                n_normal_transform = nt.nodes.new(
                    type="ShaderNodeVectorTransform")
                n_normal_transform.name = "QG_AOV_NormalTransform"
                n_normal_transform.label = "QG_AOV_NormalTransform"
                n_normal_transform.convert_from = "WORLD"
                n_normal_transform.convert_to = "CAMERA"
                n_normal_transform.location = (1000, -100)
                nt.links.new(
                    n_normal_transform.inputs[0], n_normal_geometry.outputs["Normal"])

                n_normal_mult = nt.nodes.new(type="ShaderNodeVectorMath")
                n_normal_mult.name = "QG_AOV_NormalMult"
                n_normal_mult.label = "QG_AOV_NormalMult"
                n_normal_mult.location = (1200, -100)
                n_normal_mult.operation = "MULTIPLY"
                n_normal_mult.inputs[1].default_value = [0.5, 0.5, -0.5]
                nt.links.new(
                    n_normal_mult.inputs[0], n_normal_transform.outputs[0])

                n_normal_add = nt.nodes.new(type="ShaderNodeVectorMath")
                n_normal_add.name = "QG_AOV_NormalAdd"
                n_normal_add.label = "QG_AOV_NormalAdd"
                n_normal_add.location = (1400, -100)
                n_normal_add.operation = "ADD"
                n_normal_add.inputs[1].default_value = [0.5, 0.5, 0.5]
                nt.links.new(n_normal_add.inputs[0], n_normal_mult.outputs[0])

                nt.links.new(
                    input=n_aov_normal.inputs[0], output=n_normal_add.outputs[0], verify_limits=True)

            try:
                _setup_mat_normal_aov()
            except Exception:
                _setup_geometry_normal_aov()

        if specular_input is not None:
            try:
                nt.links.new(
                    n_aov_specular.inputs[1], specular_input.links[0].from_socket)
            except Exception:
                n_aov_specular.inputs[1].default_value = specular_input.default_value

        if roughness_input is not None:
            try:
                nt.links.new(
                    n_aov_roughness.inputs[1], roughness_input.links[0].from_socket)
            except Exception:
                n_aov_roughness.inputs[1].default_value = roughness_input.default_value

        if metallic_input is not None:
            try:
                nt.links.new(
                    n_aov_metallic.inputs[1], metallic_input.links[0].from_socket)
            except Exception:
                n_aov_metallic.inputs[1].default_value = metallic_input.default_value

        updated += 1

    return updated, skipped_linked
