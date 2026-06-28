---
name: blender-addon-global-submodules
description: Blender shared submodules — creating, linking into addons via junctions, the register/unregister/reload contract, naming conventions (LKS_ prefix, bl_idname patterns), auto-discovery, and testing through dev wrapper addons. Use when scaffolding a new submodule, linking an existing submodule into an addon, extracting reusable code, or working in blender_utils/submodules/.
---

# LLM Primer: Blender Submodules — Creating, Linking, and Developing

> Attach this document to a fresh LLM chat when working with shared Blender submodules. It provides all the context needed to scaffold, develop, link, and test submodules.

Also see rule `blender-addon-global-submodule-workflow.mdc` (symlinked from `blender_utils/cursor_addons_shared/`).

---

## What Is a Submodule?

A submodule is a standalone, reusable Blender Python package that:
- Lives at `C:\BTS_SSD\Work_Scripts\blender_utils\submodules\<module_id>/`
- Has its own git repo
- Is completely standalone — **never imports from any consuming addon**
- Can be junction-linked into any addon's `submodules/` directory
- Follows a strict contract: `register()`, `unregister()`, `reload()`

Addons consume submodules via Windows directory junctions. The addon's `register_addon.py` auto-discovers them.

---

## Creating a New Submodule

### Generator Command

```powershell
cd C:\BTS_SSD\Work_Scripts\blender_utils
python -m addon_tools.generate submodule "<module_id>" "<Module Name>"
```

Example:
```powershell
python -m addon_tools.generate submodule "mesh_cleanup" "Mesh Cleanup"
```

This creates:
1. **Submodule source:** `blender_utils/submodules/mesh_cleanup/`
2. **Dev wrapper addon:** `blender_addons/lks_mesh_cleanup_dev/`
3. **Junction link:** `lks_mesh_cleanup_dev/submodules/mesh_cleanup/` → canonical source
4. **Config update:** `addon_config.toml` in the dev addon lists the submodule

### Post-Scaffold Steps

```powershell
cd C:\BTS_SSD\Work_Scripts\blender_utils\submodules\mesh_cleanup
git init

cd C:\BTS_SSD\Work_Scripts\blender_addons\lks_mesh_cleanup_dev
git init

setup_junctions.bat
```

---

## Submodule File Structure

```
submodules/mesh_cleanup/
├── __init__.py          # Contract: register(), unregister(), reload()
├── register.py          # Class tuples + bpy registration loop
├── ui.py                # Panel (bl_parent_id set dynamically by consuming addon)
├── ops/
│   ├── __init__.py
│   └── lks_ot_clean.py  # Operator files
└── .gitignore
```

### The Contract (`__init__.py`)

```python
def register(parent_panel_id: str | None = None) -> None:
    """Register classes. Optionally parent the UI panel."""
    _get_registrar().register(parent_panel_id=parent_panel_id)

def unregister() -> None:
    """Unregister all classes (reverse order)."""
    _get_registrar().unregister()

def reload() -> None:
    """importlib.reload all child modules for hot-reload."""
    _get_registrar().reload()
```

---

## Linking Into an Existing Addon

```powershell
cd C:\BTS_SSD\Work_Scripts\blender_utils
python -m addon_tools.generate link "C:\path\to\my_addon" "mesh_cleanup"
```

---

## Naming Conventions

| Artifact | Pattern | Example |
|----------|---------|---------|
| Submodule directory | `<module_id>` | `mesh_cleanup` |
| Dev addon directory | `lks_<module_id>_dev` | `lks_mesh_cleanup_dev` |
| Operator class | `LKS_OT_<CamelAction>` | `LKS_OT_CleanMesh` |
| Operator `bl_idname` | `<ctx>.lks_<module>_<action>` | `mesh.lks_mesh_cleanup_clean` |
| Panel class | `VIEW3D_PT_<module_id>` | `VIEW3D_PT_mesh_cleanup` |

---

## Critical Rules

1. **Submodules never import from the consuming addon.**
2. **Submodules never call `bpy.ops.*` for their own operators.**
3. **ALL registered classes use the `LKS_` prefix.**
4. **`bl_options = {'REGISTER', 'UNDO'}`** for state-mutating operators.
5. **`poll()` guards:** `return context.area and context.area.type == 'VIEW_3D'`

---

## Working Example

The `keymap_conflict_resolver` submodule at `blender_utils/submodules/keymap_conflict_resolver/`.
