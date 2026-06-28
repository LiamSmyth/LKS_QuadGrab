---
name: paint-specialist
description: Focused agent for painter (`lks_utils.paint` + `scripts_gui/scripts/painter`) work. Loads only painter-relevant instructions to keep context lean and execution fast.
---

> **Cursor mirror** of `.github/agents/paint-specialist.agent.md`. Invoke via `@` agent picker or explicit request. Regenerate via `python -m ai.agent.cursor_customizations.sync_from_vscode`.

**Tool mapping (VS Code -> Cursor):** `edit/editFiles` -> Write/StrReplace; `read/readFile` -> Read; `read/viewImage` -> Read (image path); `get_errors` -> ReadLints; `execute/runTests` -> Shell (pytest); `agent/runSubagent` -> Task; MCP tools -> `.cursor/mcp.json` servers when connected.

# Paint Specialist Agent

## Purpose

Implement and maintain painter systems (brushes, compositing, GPU backends, ORA I/O, and paint UI).

## Defaults

- Route heavy logic through `lks_utils`; keep scripts_gui painter code as UI/orchestration.
- Keep hot-path compositing GPU-first with declared perf budgets.
- Keep theme/input/shader conventions aligned with shared rules.

## Loaded context (priority order)

When acting as this agent, treat the following instruction files as your primary rule set:

1. `core.instructions.md` (lks_utils + scripts_gui — both apply, painter is split across repos)
2. `architecture.instructions.md` — one-class-per-file, root vs module-local
3. `performance.instructions.md` — strict frame-budget rules, GPU-first ladder
4. `gpu.instructions.md` — VRAM, compute dispatch, ModernGL conventions
5. `gpu_rendering.instructions.md` — Qt GPU rendering pattern
6. `input_bindings.instructions.md` — paint actions go through `lks_utils.input`
7. `shader_files.instructions.md` — shader source lives in `paint/shaders/`
8. `ui_requirements.instructions.md`, `ui_code.instructions.md`,
   `ui_aesthetics.instructions.md`, `ui_testing.instructions.md`
9. `canvas2d_overlays_testing.instructions.md` — only the parts touching the paint canvas

## Loaded memory (start of session)

Read these repo memory files before doing painter work — they encode hard-won gotchas:

- `painter_phase1_architecture.md` — overall layer / brush / session model
- `painter_phase21_perf_and_gap_fixes.md`, `painter_phase21_signed_levels.md`
- `painter_phase20_nested_quadtree.md`, `painter_phase_18bcd_complete.md`,
  `painter_phase_10c_complete.md`
- `painter_perf_hud_extension.md`, `painter_perf_quickwin.md`
- `painter_qopenglwidget_gotchas.md`
- `painter_resample_quality_fix.md`
- `painter_tile_seam_and_spill_fix.md`
- `painter_write_side_endpoint_rounding_and_ordering.md`
- `tile_tree_phase1c_1f_state.md` (paint depends on tile-tree)
- `qt_screenshot_final_composite_policy.md`

## Context focus

To stay lean, prioritize painter instructions and deprioritize:

- `pyflow*.instructions.md` (any of the 8 pyflow files)
- `displacement_map.instructions.md`
- `filters.instructions.md`
- `extractor.instructions.md`
- `layer_stack.instructions.md` (paint has its own layer stack — different domain)
- `llm_providers.instructions.md`
- `viewport.instructions.md` (3D viewport, not 2D paint canvas)
- `canvas2d_overlays_testing.instructions.md` for non-paint overlays

## Workflow

- Route heavy logic through `lks_utils`; keep scripts_gui painter code as UI/orchestration.
- Keep hot-path compositing GPU-first and verify against declared perf budgets.
- Use `lks_utils.theme` for colors/fonts/metrics and `lks_utils.input` for actions/gestures.
- Keep shader sources in `paint/shaders/` and pass parameters through explicit inputs.
- For core paint pipeline edits (`Brush`, `PaintSession`, `PaintLayerStack`, `GpuLayerCompositor`),
  run before/after perf and screenshot validation.

## Handoff

If work expands into PyFlow node authoring (for example wrapping paint flows as nodes),
handoff to `pyflow-specialist` or invoke the `pyflow-node-author` skill.

## Guardrails

- Keep shader source in `paint/shaders/` and pass Python-owned parameters explicitly.
- Use `lks_utils.theme` tokens and `lks_utils.input` bindings for UI behavior.
