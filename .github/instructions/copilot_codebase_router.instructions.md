---
applyTo: '**'
---

# Blender Add-on Workspace Router

A ledger of existing code, utilities, and resources for this Blender 5.0+ add-on. This file provides quick links to what currently exists in the repository. For engineering rules and patterns, see `copilot_style_guide.instructions.md`.

## 🚦 Start Here
- `copilot_style_guide.instructions.md`: canonical engineering rules and Blender Python scripting policy.
- `copilot_ui_creation.instructions.md`: rules for creating Blender UI panels and menus.
- `copilot_external_deps.instructions.md`: handling external dependencies in a Blender environment.
- `__init__.py`: Add-on metadata (`bl_info`) and root registration lifecycle.

## 🖥️ Environment Defaults
- **Target API**: Blender 5.0+
- **Execution Context**: Code runs within Blender's embedded Python interpreter.
- **Testing**: Tests are executed via terminal by launching Blender in background mode (`blender -b -P <test_script.py>`).

## 🗺️ Folder Structure
- `__init__.py` – Add-on entry point. Contains `bl_info` and delegates registration to submodules.
- `constants.py` – Global magic strings, default values, and shared constants.
- `operators/` – Blender Operators (`bpy.types.Operator`). **Strictly one operator per file.**
- `ui/` – Blender UI classes (`bpy.types.Panel`, `bpy.types.Menu`). **Strictly one class per file.** Submodules get their own submenus.
- `properties/` – Blender PropertyGroups (`bpy.types.PropertyGroup`) and `bpy.props` definitions.
- `utils/` – Pure Python utility code that does not constitute a full Blender class.
- `<module>/` – Feature-specific submodules.
  - `<module>/register.py` – Handles `register()` and `unregister()` for all classes within the module.
  - `<module>/test/` – Tests for the module, e.g., `test_<script>.py`.

## 🧩 Modules & Registration
Each logical module or folder MUST contain a `register.py` file exposing `register()` and `unregister()` functions. The root `__init__.py` imports and calls these module-level registration functions.

## 🛠️ Utility Modules
Utility code that does not inherit from Blender types (e.g., math helpers, file I/O, pure data processing) must be placed in `utils/` or a module-specific `utils` folder.

## ⚠️ Keeping This Router Updated
**This is a living inventory.** Update this file whenever you add a new major submodule, utility category, or architectural pattern.
