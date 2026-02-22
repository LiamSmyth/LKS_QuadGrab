---
applyTo: '**'
---

# External Dependencies Router

This document describes external local repositories containing shared utilities that can be used instead of writing new code locally. These are Python packages with `pyproject.toml` that can be installed via pip.

## 📋 Dual-Use Pattern

This template supports two repository types:

1. **Utility module** — A shared package that other projects install as a dependency. Must maintain a "Codebase Router" section in README.md so external LLM agents can discover available functionality.

2. **Project repo** — A standalone application that consumes external utility modules. Uses this file to track which external repos are available and how to use them.

In either case, **maintain both**:
- `README.md` with a "Codebase Router" section (for external discovery)
- `.github/instructions/copilot_codebase_router.instructions.md` (for direct workspace use)

## 🛠️ Making This Repo a Shared Utility Module

If this repository will be installed as a dependency by other projects, you must create and maintain a `pyproject.toml` for pip installation.

### Required: Create `pyproject.toml`

Create a `pyproject.toml` at the repository root:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "your-package-name"
version = "0.1.0"
description = "Brief description of what this utility provides"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

dependencies = [
    # Add runtime dependencies here (same as requirements.txt runtime deps)
    # "requests>=2.30.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["util*", "scripts*"]  # Adjust to match your package structure
```

### Package Structure Options

Choose the structure that fits your utility:

**Option A: Flat structure (simple utilities)**
```
repo/
├── pyproject.toml
├── util/
│   ├── __init__.py
│   ├── path_utils.py
│   └── json_utils.py
└── ...
```
Install: `from util.path_utils import safe_filename`

**Option B: Named package (recommended for larger utilities)**
```
repo/
├── pyproject.toml
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── path_utils.py
│       └── json_utils.py
└── ...
```
With `[tool.setuptools.packages.find] where = ["src"]`
Install: `from package_name.path_utils import safe_filename`

### Maintenance Checklist

When this repo is a shared utility module:

- [ ] `pyproject.toml` exists and has correct package name/version
- [ ] `__init__.py` files exist in all importable directories
- [ ] Dependencies in `pyproject.toml` match `requirements.txt` runtime deps
- [ ] README.md "Codebase Router" section lists available modules and key functions
- [ ] Version is bumped when making breaking changes
- [ ] Consuming projects can reinstall via `pip install -e "path/to/this/repo"`

### Testing the Install

```powershell
# From another project, test the editable install
pip install -e "C:\path\to\this-repo"

# Verify import works
python -c "from package_name import module; print('OK')"
```

## 🔑 Key Principles

The LLM agent is **authorized and encouraged** to:
1. **Read code and documentation** in external shared repos before writing new utilities
2. **Use existing utilities** instead of duplicating functionality locally
3. **Contribute generic utilities upstream** to shared repos rather than adding them here
4. **Install shared packages** when they provide functionality needed by local scripts

### How File Tools Work with External Repos

**Important limitation**: VS Code's file tools are typically restricted to the current workspace. To read/edit external repos, you have two options:

**Option A: Multi-root workspace (recommended)**
Add the external repo as a folder in your VS Code workspace:
1. File → Add Folder to Workspace
2. Select `C:\path\to\shared-utils`
3. Now file tools work on both folders

**Option B: Open file in editor**
Files opened in the editor (even from outside workspace) become accessible:
1. Open the external file manually in VS Code
2. The LLM can now read/edit it

Once accessible, file tools work with absolute paths:

```python
# Reading from external repo
read_file("C:/path/to/shared-utils/README.md")
read_file("C:/path/to/shared-utils/.github/instructions/copilot_codebase_router.instructions.md")

# Editing external repo (when contributing upstream)
replace_string_in_file("C:/path/to/shared-utils/util/path_utils.py", ...)
```
```

The LLM can freely read any registered external repo. **Edits** should follow the contribution workflow below.

## 📖 How to Discover External Repo Contents

External repos may not have `.github/instructions/` auto-loaded into context. To understand what's available:

1. **Read `README.md` first** — External repos should maintain a "Codebase Router" section in their README that summarizes available modules, key functions, and how to dig deeper.
2. **Check for `.github/instructions/copilot_codebase_router.instructions.md`** — If the repo follows this template pattern, read the router file for detailed inventory.
3. **Explore the source** — Use `read_file` and `grep_search` on the external repo to understand available utilities.

### Expected README Structure for External Repos

External shared repos should include a section like this in their README:

```markdown
## Codebase Router (LLM Summary)

Quick reference for available modules and functionality.

### Available Modules
- `package.module_a` — Brief description, key functions
- `package.module_b` — Brief description, key functions

### How to Explore Further
- Detailed routing: `.github/instructions/copilot_codebase_router.instructions.md`
- Source code: `src/package/`
```

## 📦 Registered External Repos

<!-- 
Add external shared repos here as they become available.
For each repo, include:
- Name and location
- Package name (after pip install)
- What it provides (high-level)
- How to install
- Where to find its router/README
-->

### Example Entry (Template)

```markdown
### `shared-utils`
- **Location**: `C:/path/to/shared-utils`
- **Package name**: `shared_utils` (after install: `from shared_utils import ...`)
- **Provides**: Common utilities for paths, JSON, logging, validation
- **Install**: `pip install -e "C:/path/to/shared-utils"`
- **Router**: Read `README.md` first, then `.github/instructions/copilot_codebase_router.instructions.md`

#### Key Modules
- `shared_utils.path_ops` — Windows-safe path utilities, filename sanitization
- `shared_utils.json_utils` — JSON validation, schema helpers
- `shared_utils.logging_utils` — Shared logging configuration
```

### Currently Registered Repos

### `lks-utils`
- **Location**: `C:/BTS_SSD/Work_Scripts/lib/lks_utils`
- **Package name**: `lks_utils` (after install: `from lks_utils import ...`)
- **Provides**: Shared utilities for logging, file I/O, text processing, JSON helpers, and progress reporting
- **Install**: `pip install -e "C:/BTS_SSD/Work_Scripts/lib/lks_utils"` (or with extras: `[image]`, `[video]`, `[all]`)
- **Router**: Read `README.md` "Codebase Router" section, then `.github/instructions/copilot_codebase_router.instructions.md`

#### Key Modules
| Module | Description | Key Functions |
|--------|-------------|---------------|
| `lks_utils` | Root exports | `log_info`, `log_warn`, `log_error`, `log_debug`, `safe_print`, `timed` |
| `lks_utils.core` | File I/O utilities | `atomic_write`, `hash_from_config`, `ensure_directory_exists` |
| `lks_utils.text` | Text processing | `normalize_text_for_console`, `sanitize_filename`, `sanitize_video_filename`, `clamp_length` |
| `lks_utils.json` | JSON utilities | `json_loads_safe`, `json_dumps_compact`, `merge_deep`, `get_value_at_path` |
| `lks_utils.logging` | Logging helpers | `log_info`, `log_warn`, `log_error`, `log_debug`, `safe_print` |
| `lks_utils.progress` | Progress reporting | `ProgressReporter` |

#### Optional Dependency Groups
- `[image]` — numpy, Pillow, pillow-heif, opencv-python
- `[video]` — opencv-python, ffmpeg-python, yt-dlp
- `[schema]` — jsonschema
- `[web]` — requests, urllib3
- `[all]` — All optional dependencies

#### Configuration
| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `LKS_VERBOSE_LOGGING` | `0` | Set to `1` to enable debug logging |
| `LKS_PATCH_PRINT` | `1` | Set to `0` to disable global print normalization |

## 🔧 Installation

External packages can be installed in two ways:

### Pre-configured (in requirements.txt)
```txt
# External shared utilities (editable install from local path)
-e C:/path/to/shared-utils
```

### On-demand (when needed)
```powershell
# Install from local path (editable)
pip install -e "C:\path\to\shared-utils"

# Or install from git
pip install -e "git+https://github.com/org/shared-utils.git#egg=shared_utils"
```

## 🔀 Decision Tree: Write Here vs. Contribute Upstream

| Scenario | Action |
|----------|--------|
| Need project-specific utility | Write locally in `util/` |
| Need general-purpose utility (paths, JSON, logging) | Check external repos first |
| Utility already exists in external repo | Import and use it |
| Writing generic utility that others could use | **Contribute to external repo** |
| Local utility becomes generic over time | **Refactor and move upstream** |

## 🚀 Contributing to External Repos

When writing utility code that is **not project-specific**:

1. **Check first** — Read the external repo's README/router to see if similar functionality exists
2. **Create in external repo** — Add the utility to the shared repo (not locally)
3. **Follow external repo's style** — Each repo has its own conventions; read its style guide
4. **Add tests** — Tests belong in the external repo alongside the new utility
5. **Install/update locally** — After contributing, reinstall the package: `pip install -e "C:\path\to\repo"`
6. **Import and use** — Reference the new utility from this project
7. **Update this file** — If the external repo's capabilities changed significantly, update the "Key Modules" section

### LLM Workflow for Contributing Upstream

When the LLM needs to add or modify code in an external repo:

1. **Read the external repo's style guide first**:
   ```
   read_file("C:/path/to/shared-utils/.github/instructions/copilot_style_guide.instructions.md")
   ```

2. **Read existing related code** to understand patterns:
   ```
   read_file("C:/path/to/shared-utils/util/existing_module.py")
   ```

3. **Make edits using absolute paths**:
   ```
   create_file("C:/path/to/shared-utils/util/new_module.py", content)
   replace_string_in_file("C:/path/to/shared-utils/util/existing.py", old, new)
   ```

4. **Add tests in the external repo**:
   ```
   create_file("C:/path/to/shared-utils/util/test/new_module_test.py", test_content)
   ```

5. **Run external repo's tests**:
   ```
   run_in_terminal("cd C:/path/to/shared-utils ; python -m pytest")
   ```

6. **Return to current project and use the new code**:
   ```python
   from shared_utils.new_module import new_function
   ```

### Terminal Workflow Example

```powershell
# 1. Navigate to external repo
cd "C:\path\to\shared-utils"

# 2. Add utility (following that repo's patterns)
# ... edit files ...

# 3. Run external repo's tests
python -m pytest

# 4. Return to this project
cd "C:\path\to\this-project"

# 5. Reinstall to pick up changes
pip install -e "C:\path\to\shared-utils"

# 6. Use the new utility
# from shared_utils.new_module import new_function
```

## ⚠️ Keeping This Document Updated

Update this file when:
- A new external shared repo becomes available
- An external repo adds significant new functionality
- Installation paths or package names change
- A repo is deprecated or replaced

When registering a new external repo, ensure it has:
- A `pyproject.toml` for pip installation
- A README with a "Codebase Router" section (or equivalent summary)
- Clear module organization that can be summarized here
