---
name: blender-addon-global-new-addon
description: Blender addon creation — scaffolding new addons via the generator CLI (addon_tools.generate), post-scaffold setup (local_paths.bat, setup_junctions.bat, git init), the template file structure, adding operators (LKS_OT_* naming, bl_idname patterns, poll guards), the dev/ module for local-only scaffolding, key naming rules (LKS_ prefix), and linking submodules. Use when creating a new Blender addon, scaffolding from template, or setting up addon_tools/generate.
---

# LLM Primer: Creating a New Blender Addon

> Attach this document to a fresh LLM chat to give it the context needed to scaffold and develop a new Blender addon using the factory tooling in this workspace.

---

## Your Environment

You are working in a multi-root VS Code workspace on Windows. The key workspace folders are:

| Folder | Path | Purpose |
|--------|------|---------|
| **blender_utils** | `C:\BTS_SSD\Work_Scripts\blender_utils` | Shared tooling: generator CLI, build/publish/test scripts, submodule templates |
| **blender_addons** | `C:\BTS_SSD\Work_Scripts\blender_addons` | Where scaffolded dev addons live |
| **Blender scripts** | `C:\BTS_SSD\Software_Blender_Cfg\install_dir\scripts` | Blender's addons directory (dev addons appear here via junction) |

## How Addons Are Created

All new addons are scaffolded from a template using a generator CLI. **Do not create addon files manually.**

### Generator Command

```powershell
cd C:\BTS_SSD\Work_Scripts\blender_utils
python -m addon_tools.generate addon "<addon_id>" "<Addon Display Name>"
```

- `<addon_id>`: snake_case identifier, must start with `lks_` (e.g., `lks_mesh_tools`)
- `<addon_name>`: human-readable name (e.g., `LKS Mesh Tools`)
- Output: `C:\BTS_SSD\Work_Scripts\blender_addons\<addon_id>/`

The generator reads `.template_addon/` and replaces `{{ADDON_ID}}`, `{{ADDON_NAME}}`, `{{ADDON_DISPLAY}}` tokens in all files.

After scaffolding, run shared Cursor sync:

```powershell
python -m addon_tools.sync_cursor_customizations --addon <addon_id>
```

### Post-Scaffold Steps (you must do these)

1. **Edit `local_paths.bat`** in the new addon directory with machine-specific paths.
2. **Run `setup_junctions.bat`** — creates junctions for submodules and links the addon into Blender's addons directory.
3. **Run `git init`** in the new addon directory.
4. **Enable in Blender** — Preferences → Add-ons → enable the addon.

### What the Template Creates

```
<addon_id>/
├── __init__.py
├── register_addon.py
├── properties.py
├── ui.py
├── ops/__init__.py
├── util/__init__.py
├── dev/__init__.py
├── submodules/
├── tests/
├── addon_config.toml
├── blender_manifest.toml
├── local_paths.bat
├── .cursor/                 # populated by sync_cursor_customizations
├── setup_junctions.bat
├── push_remote.bat
├── release.bat
├── build_extension.bat
├── launch_headless_test.bat
└── test_sandbox_extension.bat
```

## Shared Cursor customizations

Canonical Blender-addon rules and skills live in `blender_utils/cursor_addons_shared/`. Sync them into the addon with `python -m addon_tools.sync_cursor_customizations`.

## How to Add an Operator

See `blender-addon-global-operators.mdc` in the addon's `.cursor/rules/` after sync.

## How to Link a Submodule

See skill `blender-addon-global-submodules`.

## Context Gathering Checklist for the LLM

When starting work on an addon, gather context by reading:

1. The generator CLI: `blender_utils/addon_tools/generate.py`
2. The addon's `addon_config.toml`
3. Shared rules under `.cursor/rules/blender-addon-global-*.mdc`
4. Project-specific rules (`project-*.mdc`) when present
5. `blender_utils/docs/` for human-readable workflow summaries
