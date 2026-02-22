# LKS QuadGrab - Upgrade Feature Specification
**Date:** 2026-02-22

## 1. Selective Remote Git Push (Local vs. Remote Git)
**Problem:** The repository contains local development files, instructions, and boilerplate that should be tracked in local Git history but must not be pushed to the public GitHub remote.
**Solution:** Implement a custom Python-based publishing workflow.
*   **Mechanism:** 
    *   Create a `.remoteignore` (or `.gitignore_remote`) file that lists patterns of files to exclude from the remote repository (e.g., `.github/instructions/`, local test blends).
    *   Develop a Python script (`publish_to_github.py`) that automates the process of pushing a filtered subset of the codebase.
    *   **Proposed Workflow:** The script will manage a separate local branch (e.g., `github-publish`). It will copy/sync the allowed files from the main working tree to this branch, commit them with a user-provided message, and push *only* that branch to the remote.
    *   Create a batch file (`push_remote.bat`) that prompts the user for a commit message and executes the Python script.

## 2. Blender Extension Migration (Blender 4.2+)
**Problem:** Blender has transitioned from legacy "Add-ons" to "Extensions", which support in-app updates and better dependency management.
**Solution:** Convert LKS QuadGrab into a standard Blender Extension.
*   **Manifest Creation:** Author a `blender_manifest.toml` file at the root of the project containing the metadata previously stored in `bl_info` (name, version, schema version, permissions, etc.).
*   **Codebase Adjustment:** Remove or adapt the `bl_info` dictionary in `__init__.py` to comply with the new Extension guidelines.
*   **Workspace Relocation:** Move the development directory to the Blender Extensions folder (`%APPDATA%\Blender Foundation\Blender\5.1\extensions\user_default\lks_quadgrab`) to allow live testing of the extension architecture.

## 3. Codebase Grooming & Refactoring
**Problem:** The codebase relies on hardcoded strings for references and lacks comprehensive type hinting, making it prone to typos and harder to maintain.
**Solution:** Perform a strict grooming pass across all Python files.
*   **Strict Type Hinting:** Ensure all variables, function arguments, and return types use Python type hints (e.g., `obj: bpy.types.Object`, `def my_func() -> bool:`).
*   **Class Reference Variables:** Replace hardcoded string references for operators, panels, and UI elements with their direct class attributes. 
    *   *Example:* Instead of `layout.operator("object.lks_quad_grab")`, use `layout.operator(OBJECT_OT_LKS_QuadGrab.bl_idname)`.
*   **Centralized Property Handles:** Declare string handles for `bpy.types.Scene` properties once as constants at the module level, and reference those constants throughout the UI and operator code to prevent string duplication and typos.

## 4. Headless Testing Boilerplate
**Problem:** Launching tests via standard IDE plugins crashes in headless mode because it attempts to load the user's default, heavily-customized Blender plugins.
**Solution:** Create an isolated, factory-startup testing environment.
*   **Batch Launcher:** Author a `run_tests_headless.bat` script that accepts a path to a specific Blender executable.
*   **Factory Startup:** The script will launch Blender using the `--background` (`-b`) and `--factory-startup` arguments to ensure a clean environment without user plugins.
*   **Test Runner Script:** The batch file will execute a Python script (`tests/run_tests.py`) inside the Blender runtime. This script will manually append the extension path to `sys.path`, register the extension, and execute the test suite (e.g., using `unittest` or `pytest`), outputting the results to the terminal.