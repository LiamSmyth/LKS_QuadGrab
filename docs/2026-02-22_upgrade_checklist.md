# LKS QuadGrab - Upgrade Checklist
**Date:** 2026-02-22

## Phase 1: Selective Remote Git Push
- [x] Create `.remoteignore` file and define patterns for local-only files (e.g., `.github/instructions/`).
- [x] Write `publish_to_github.py` to handle branch management, file filtering, and committing.
- [x] Write `push_remote.bat` to prompt for a commit message and trigger the Python script.
- [x] Test the publishing workflow locally (dry-run) to ensure restricted files are not staged for the remote branch.

## Phase 2: Blender Extension Migration
- [x] Create `blender_manifest.toml` with required extension metadata (id, version, name, maintainer, schema_version, permissions).
- [x] Update `__init__.py` to remove/modify `bl_info` as required by the Extension schema.
- [x] Relocate the project folder to the Blender 5.1 Extensions directory (`extensions/user_default/`).
- [ ] Verify the extension appears in the Blender Extensions panel and can be enabled/disabled without errors.

## Phase 3: Codebase Grooming
- [x] **Type Hinting:**
  - [x] Update `__init__.py`
  - [ ] Update `operators.py`
  - [x] Update `properties.py`
  - [x] Update `ui.py`
  - [x] Update `register_quadgrab.py`
- [x] **Class References:**
  - [x] Replace string operator IDs in `ui.py` with `OperatorClass.bl_idname`.
  - [x] Replace string panel IDs (if any) with `PanelClass.bl_idname`.
- [x] **Property Handles:**
  - [x] Define constants for all Scene properties in `properties.py` (e.g., `PROP_OUTPUT_DIR = "lks_quadgrab_output_dir"`).
  - [x] Update `properties.py` registration to use constants.
  - [x] Update `ui.py` to use constants for `row.prop()`.
  - [x] Update `operators.py` to use constants when accessing `bpy.context.scene`.

## Phase 4: Headless Testing Setup
- [x] Create `tests/` directory.
- [x] Write `tests/run_tests.py` to handle extension registration and test discovery within the Blender Python environment.
- [x] Write `run_tests_headless.bat` to launch Blender with `--background` and `--factory-startup`.
- [x] Write a basic dummy test in `tests/test_basic.py` to verify the headless environment works.
- [x] Execute `run_tests_headless.bat` and confirm tests pass without loading user plugins.