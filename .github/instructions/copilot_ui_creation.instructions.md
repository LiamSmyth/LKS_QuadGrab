------

applyTo: '**'

------

# GUI Creation Instructions

When this file is present in the `.instructions/` folder, **GUIs are mandatory** for all user-facing functionality. Users should interact with batch scripts that launch GUIs, not command-line interfaces.

> **📁 Templates Available:** All code templates are in the `templates/` folder. Copy and customize as needed instead of writing from scratch.

## Key Principle: Separation of Logic and Presentation

**All modules MUST maintain strict separation between business logic and GUI:**

- **`<module>.py`** - Pure logic, CLI-compatible, fully testable without GUI
- **`<module>_gui.py`** - Thin GUI wrapper that calls `<module>.py` functions
- **`run_<module>_gui.bat`** - Batch launcher for GUI

This architecture ensures:
- ✅ Core logic is testable in isolation via unit tests
- ✅ Power users can access functionality via command line
- ✅ GUI issues don't block logic testing/debugging
- ✅ Logic can be reused in other contexts (APIs, batch scripts, other GUIs)
- ✅ Changes to UI don't require changing business logic

## Framework: ttkbootstrap

This project uses **ttkbootstrap**, a modern theming extension for Python's tkinter that provides:
- Beautiful, contemporary themes out-of-the-box
- Bootstrap-inspired widget styling
- Cross-platform consistency
- Drop-in replacement for standard tkinter widgets

Install via `requirements.txt` (already included):
```
ttkbootstrap>=1.10.1
```

## Architecture Principles

### 1. Separation of Concerns: Logic vs. GUI

**Critical principle:** GUI code and functional logic must be strictly separated to ensure testability and maintainability.

#### File Structure Pattern
For each module, create:
- `scripts/<module>/<module>.py` - Core functional logic (CLI-compatible)
- `scripts/<module>/<module>_gui.py` - GUI wrapper that calls the core logic
- `run_<module>_gui.bat` - Batch launcher for the GUI

#### Core Logic Script (`<module>.py`)
- Contains all functional implementation
- Provides a CLI interface using `argparse` or similar
- Should be fully testable via command line
- No GUI imports or dependencies
- Can be imported and called programmatically
- Example:
  ```python
  # scripts/converter/converter.py
  import argparse
  from pathlib import Path
  
  def convert_file(input_path: Path, output_path: Path, options: dict) -> bool:
      """Core conversion logic - pure function."""
      # Implementation here
      return True
  
  def main():
      """CLI entry point."""
      parser = argparse.ArgumentParser(description="File converter")
      parser.add_argument("input", type=Path, help="Input file")
      parser.add_argument("output", type=Path, help="Output file")
      parser.add_argument("--format", default="json", help="Output format")
      args = parser.parse_args()
      
      success = convert_file(args.input, args.output, {"format": args.format})
      return 0 if success else 1
  
  if __name__ == "__main__":
      exit(main())
  ```

#### GUI Script (`<module>_gui.py`)
- Thin wrapper that imports and calls core logic functions
- Handles only UI concerns: layout, events, user feedback
- Calls functions from `<module>.py` for actual work
- Example:
  ```python
  # scripts/converter/converter_gui.py
  import ttkbootstrap as ttk
  from ttkbootstrap.constants import *
  from pathlib import Path
  from . import converter  # Import core logic
  
  def create_gui_panel(parent) -> ttk.Frame:
      frame = ttk.Frame(parent, padding=10)
      
      # UI elements...
      
      def execute_action():
          """GUI event handler - delegates to core logic."""
          input_path = Path(input_entry.get())
          output_path = Path(output_entry.get())
          options = {"format": format_var.get()}
          
          try:
              # Call core logic function
              success = converter.convert_file(input_path, output_path, options)
              if success:
                  Messagebox.show_info("Conversion complete!", parent=frame)
          except Exception as e:
              Messagebox.show_error(f"Error: {e}", parent=frame)
      
      return frame
  ```

#### Benefits of Separation
- **Testability:** Core logic can be unit tested without GUI dependencies
- **CLI Access:** Power users can script operations via command line
- **Debugging:** Logic can be tested independently of GUI issues
- **Reusability:** Core logic can be used in other contexts (APIs, batch scripts)
- **Maintainability:** Changes to UI don't affect business logic and vice versa

### 2. Modular GUI Components
- Each submodule under `scripts/<module>/` should have its own GUI script: `scripts/<module>/<module>_gui.py`
- GUI scripts should be self-contained and testable in isolation
- Common GUI utilities (dialogs, layout helpers, theming) go in `util/gui_utils.py`

### 3. Main GUI as Tab Container
- Create a single main GUI (`gui/main_gui.py` or `scripts/main_gui.py`) that hosts all submodule GUIs as tabs
- Each submodule GUI should expose a factory function or class that returns a frame:
  ```python
  def create_gui_panel(parent) -> ttk.Frame:
      """Creates and returns the GUI panel for this module."""
      frame = ttk.Frame(parent)
      # Build UI in frame
      return frame
  ```

### 3. Integration Pattern
Adding a new submodule GUI to the main GUI should require only a couple lines:
```python
from scripts.my_module import my_module_gui

# In main GUI notebook creation:
tab = my_module_gui.create_gui_panel(notebook)
notebook.add(tab, text="My Module")
```

### 5. Standalone GUIs & Batch Launchers
- Each module GUI should be launchable standalone via: `run_<module>_gui.bat`
- Main GUI launcher: `run_main_gui.bat`
- GUIs can be integrated into the main tabbed interface while remaining standalone-capable

## File Structure & Templates

All template files are located in the `templates/` folder:

### Core Files for Each Module

1. **`<module>.py`** - Core business logic with CLI
   - Template: `templates/module_template.py`
   - Pure functions, no GUI dependencies
   - Includes argparse CLI interface
   - Fully testable via command line

2. **`<module>_gui.py`** - GUI wrapper
   - Template: `templates/module_gui_template.py`
   - Thin wrapper that calls core logic
   - Implements `create_gui_panel(parent)` for integration
   - Includes standalone `main()` function

3. **`run_<module>_gui.bat`** - GUI launcher
   - Template: `templates/run_module_gui.bat`
   - Place at repository root

### Main GUI Files

- **`scripts/main_gui.py`** - Tabbed interface container
  - Template: `templates/main_gui_template.py`
  - Hosts all module GUIs as tabs
  
- **`run_main_gui.bat`** - Main GUI launcher
  - Template: `templates/run_main_gui.bat`

### Configuration Persistence (5+ Properties)

- **Configuration utilities** - For complex GUIs
  - Reference: `templates/gui_config_template.py`
  - Provides auto-save/restore and preset management
  - Storage: `config/<module>_gui_state.json`

## Batch Script Launchers

Use the batch script templates in `templates/`:
- `templates/run_main_gui.bat` - Main GUI launcher
- `templates/run_module_gui.bat` - Module-specific GUI launcher

Copy to repository root and customize as needed.

### CLI Testing (Optional but Recommended)

Core logic in `<module>.py` can be tested directly via command line:
```bat
.venv\Scripts\python.exe scripts\<module>\<module>.py input.txt output.txt --option1 value
```

Benefits:
- Automated testing and scripting
- Debugging without GUI overhead
- Integration into batch processing pipelines
- Power user workflows

## Best Practices

### Layout
- Use grid layout for forms and structured content
- Use pack layout for simple, single-direction layouts
- Always configure column/row weights for responsive behavior:
  ```python
  frame.columnconfigure(0, weight=1)
  frame.rowconfigure(0, weight=1)
  ```

### Theming
- Available themes: `darkly`, `superhero`, `flatly`, `journal`, `lumen`, `minty`, `pulse`, `sandstone`, `united`, `yeti`, `morph`, `simplex`, `cerculean`, `cosmo`, `litera`, `solar`
- Use bootstyles for button variants: `PRIMARY`, `SECONDARY`, `SUCCESS`, `INFO`, `WARNING`, `DANGER`
- Example:
  ```python
  btn = ttk.Button(frame, text="Save", bootstyle=SUCCESS)
  ```

### File Dialogs
- Import dialogs locally to avoid startup overhead:
  ```python
  def browse_file():
      from tkinter import filedialog
      path = filedialog.askopenfilename(...)
  ```

### Progress & Feedback
- Use `ttk.Progressbar` for long operations
- Use `ttk.dialogs.Messagebox` for user feedback:
  ```python
  from ttkbootstrap.dialogs import Messagebox
  Messagebox.show_info("Operation complete!", parent=root)
  Messagebox.show_error("An error occurred!", parent=root)
  ```

### Threading for Long Operations
- Never block the GUI thread with long-running operations
- Use threading for background work:
  ```python
  import threading
  
  def long_operation():
      # Do work
      pass
  
  def start_operation():
      thread = threading.Thread(target=long_operation, daemon=True)
      thread.start()
  
  btn = ttk.Button(frame, text="Start", command=start_operation)
  ```

### Configuration
- Store GUI state (last directory, window size, etc.) in a JSON config file
- Save on close, load on startup
- Use `util/config_utils.py` for config management

### Configuration Persistence & Presets

For GUIs with **5+ configurable properties**, implement persistent configuration to improve user experience.

#### Features to Implement

**Auto-Save GUI State:**
- Automatically save GUI state when window closes or after key events (e.g., "Execute" click)
- Restore saved state when GUI reopens
- Store in `config/<module>_gui_state.json`

**Configuration Presets:**
- Allow users to save named configuration presets
- Provide dropdown to select from saved presets
- Include "Save As...", "Delete" buttons for preset management
- Selecting a preset populates all GUI fields

#### Implementation

See `templates/gui_config_template.py` for complete implementation including:
- `GUIConfig` class for persistence
- Helper functions for preset controls
- Auto-save/restore state management

#### When to Implement

**Always implement for:**
- GUIs with 5+ configurable properties
- Frequently used GUIs with similar inputs
- Complex workflows requiring specific configurations

**Optional for:**
- Simple GUIs (1-4 properties)
- One-time use utilities
- GUIs where fresh state is preferred

#### Storage
- State files: `config/<module>_gui_state.json`
- Add `config/*.json` to `.gitignore` (user-specific)

### Error Handling
- Wrap script logic in try/except blocks
- Display user-friendly errors via message boxes
- Log detailed errors for debugging:
  ```python
  import logging
  
  def execute_action():
      try:
          # Script logic
          pass
      except Exception as e:
          logging.error(f"Action failed: {e}", exc_info=True)
          Messagebox.show_error(
              f"Operation failed:\n{str(e)}", 
              title="Error",
              parent=root
          )
  ```

## Testing Strategy

### Core Logic Testing (Priority)

With proper separation, core logic can be thoroughly tested without GUI:

**Unit Tests:**
- Test pure functions in `<module>.py` using pytest
- Focus on: valid inputs, error handling, edge cases
- Use `tmp_path` fixture for file operations

**CLI Tests:**
- Test command-line interface using subprocess
- Verify help output, argument parsing, exit codes
- Test actual execution with different parameters

### GUI Testing (Secondary)

GUI testing is less critical since logic is tested separately:

**Basic Smoke Tests:**
- Verify GUI panel can be created
- Check widgets are present
- Optional: Use pytest with tkinter mocking

**Manual Testing:**
- Launch via batch scripts: `run_<module>_gui.bat`
- Verify all controls work and errors are handled
- Test configuration persistence (if implemented)
- Test integration in main GUI

### Example Test Structure
```python
# tests/test_<module>.py
def test_process_data_success(tmp_path):
    """Test core logic with valid inputs."""
    result = <module>.process_data(input_file, output_file, option1="value")
    assert result is True

def test_cli_help():
    """Test CLI interface."""
    result = subprocess.run([sys.executable, "scripts/<module>/<module>.py", "--help"])
    assert result.returncode == 0
```

## Examples & References

- Official ttkbootstrap docs: https://ttkbootstrap.readthedocs.io/
- Built-in demos: Run `python -m ttkbootstrap` after installation
- Widget gallery: Check ttkbootstrap documentation for all available widgets and styles

## Module Creation Checklist

When creating a new module with GUI:

### 1. Core Logic (Required)
- [ ] Create `scripts/<module>/<module>.py` with core business logic
- [ ] Implement pure functions with NO GUI dependencies
- [ ] Add CLI interface using `argparse`
- [ ] Include docstrings and type hints
- [ ] Add error handling and logging
- [ ] Test via command line: `.venv\Scripts\python.exe scripts\<module>\<module>.py --help`

### 2. GUI Wrapper (Required)
- [ ] Create `scripts/<module>/<module>_gui.py` with GUI wrapper
- [ ] Import core logic from `<module>.py`
- [ ] Implement `create_gui_panel(parent)` function for tab integration
- [ ] GUI code should only handle UI concerns, delegate logic to core module
- [ ] Add user feedback (status messages, error dialogs)
- [ ] Implement `main()` for standalone execution

### 3. Configuration Persistence (If 5+ Properties)
- [ ] Implement auto-save/restore of GUI state
- [ ] Add preset save/load/delete functionality
- [ ] Create `config/<module>_gui_state.json` storage
- [ ] Add preset dropdown to GUI

### 4. Batch Launchers (Required)
- [ ] Create `run_<module>_gui.bat` at repository root
- [ ] Verify batch script uses virtual environment Python
- [ ] Test batch launcher works from double-click

### 5. Integration & Testing
- [ ] Integrate into main GUI by importing and adding to notebook tabs
- [ ] Test standalone GUI: `run_<module>_gui.bat`
- [ ] Test integrated GUI: `run_main_gui.bat`
- [ ] Test CLI functionality independently
- [ ] Verify configuration persistence (if implemented)

### 6. Documentation
- [ ] Document module in `scripts/<module>/<module>_system.md`
- [ ] Include CLI usage examples
- [ ] Document GUI controls and behavior
- [ ] Add any configuration file formats or requirements

---

**Remember:** When this UI creation guide is present, users should never need to touch the command line. All interactions happen through GUIs launched via batch scripts.
