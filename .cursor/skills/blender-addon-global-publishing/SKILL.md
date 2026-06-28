---
name: blender-addon-global-publishing
description: Blender addon publishing workflow — addons vs extensions, git architecture (junction-based, not git submodules), the three filter gates (.gitignore / .remoteignore / blender_manifest.toml paths_exclude_pattern), publish scripts (push_remote.bat, release.bat, build_extension.bat), sandbox testing, and the end-to-end dev→publish→verify cycle. Use when publishing, releasing, versioning, testing the extension zip, or working with blender_manifest.toml / addon_config.toml / .remoteignore.
---

# LLM Primer: Publishing Workflow & Version Control

> Attach this document to a fresh LLM chat when working on publishing, version control, or the addon/extension distribution pipeline.

---

## Core Concept: Addons vs. Extensions

| | Addons (local dev) | Extensions (distribution) |
|---|---|---|
| **Format** | Directory in Blender's `addons/` folder | `.zip` file installed via Blender's extension manager |
| **How loaded** | Junction link from dev directory | Extracted zip or remote install |
| **Can have junctions?** | Yes — Python/Blender follow them transparently | No — zip is flat, all real files |
| **Contains dev files?** | Yes — tests, .bat, debug, instructions | No — filtered out during build |

**Workflow:** Develop as an addon (with junctions + dev files) → publish as an extension (flat zip, no dev files).

---

## Git Architecture

Each artifact = its own git repo. Submodule links are Windows junctions, **not** git submodules. Publish scripts resolve junctions with `shutil.copytree`.

- **Commit locally often**
- **Push to remote via scripts** — `push_remote.bat`, `release.bat`
- **Never use raw `git push`** for release workflows

---

## Publishing Scripts

All located in `blender_utils/addon_tools/`. Addons invoke them via thin `.bat` wrappers.

| Script | Purpose |
|--------|---------|
| `push_remote.bat` | Filtered push to GitHub `main` |
| `release.bat` | Bump version → push → build zip → publish to `gh-pages` |
| `build_extension.bat` | Local extension zip only |
| `test_sandbox_extension.bat` | Verify built zip loads in headless Blender |

---

## The Three Filter Gates

| Gate | Config | Controls |
|------|--------|----------|
| Git ignore | `.gitignore` | Local tracking |
| Remote filter | `.gitignore` + `.remoteignore` | GitHub `main` |
| Extension filter | `blender_manifest.toml` `paths_exclude_pattern` | Extension `.zip` |

**Critical:** `submodules/` must NOT be excluded — publish follows junctions into real files.

---

## Configuration Files

| File | Purpose |
|------|---------|
| `addon_config.toml` | Identity, branches, test expectations, submodule list |
| `blender_manifest.toml` | Extension metadata + exclude patterns |
| `local_paths.bat` | Machine-specific paths (gitignored) |

---

## Context Gathering

When working on publishing, read:

1. `blender_utils/addon_tools/publish_to_github.py`
2. `blender_utils/addon_tools/publish_release.py`
3. `blender_utils/addon_tools/test_sandbox.py`
4. The addon's `.remoteignore` and `blender_manifest.toml`
