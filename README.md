This repository uses a small, local Python scripting framework.

Quick start (Windows, PowerShell):

1. Run the bootstrap installer (mandatory):

	.\install.bat

	- This creates a `.venv` virtual environment and installs dependencies from `requirements.txt`.
	- If your scripts rely on native binaries (ffmpeg, tesseract, etc.), place them in the `bin/` folder.

2. Activate the venv in PowerShell:

	powershell -Command ". .venv\Scripts\Activate.ps1"

3. Run tests:

	python -m pytest -q

---

## Codebase Router (LLM Summary)

Quick reference for LLM agents working with or consuming this repository.

### Repository Type

<!-- Uncomment the appropriate line -->
<!-- This is a **utility module** — a shared package that can be installed as a dependency by other projects. -->
<!-- This is a **project repo** — a standalone application that may consume external utility modules. -->

### Available Modules

_Update this section as modules are added. Format: `package.module` — Brief description, key functions._

- _(No modules yet)_

### Installation (if this is a utility module)

```powershell
# Editable install from local path
pip install -e "C:\path\to\this-repo"

# Then import
# from package_name import module
```

### How to Explore Further

- **Detailed routing**: `.github/instructions/copilot_codebase_router.instructions.md`
- **Style guide**: `.github/instructions/copilot_style_guide.instructions.md`
- **External dependencies**: `.github/instructions/copilot_external_deps.instructions.md`
- **Source code**: `scripts/` (main code), `util/` (helpers)

### Key Entry Points

- `main.py` — Primary entry point (if applicable)
- `scripts/` — Main scripts and submodules
- `util/` — Reusable helper utilities
