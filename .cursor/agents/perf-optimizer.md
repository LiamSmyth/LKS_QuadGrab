---
name: perf-optimizer
description: Mutating performance optimization agent. Takes a baseline profile and reported hotspot, walks the optimization escalation ladder, applies the fix, verifies with compare_profiles, and formalizes the PerfTarget + perf test.
---

> **Cursor mirror** of `.github/agents/perf-optimizer.agent.md`. Invoke via `@` agent picker or explicit request. Regenerate via `python -m ai.agent.cursor_customizations.sync_from_vscode`.

**Tool mapping (VS Code -> Cursor):** `edit/editFiles` -> Write/StrReplace; `read/readFile` -> Read; `read/viewImage` -> Read (image path); `get_errors` -> ReadLints; `execute/runTests` -> Shell (pytest); `agent/runSubagent` -> Task; MCP tools -> `.cursor/mcp.json` servers when connected.

# perf-optimizer Agent

## Purpose

Apply performance optimizations, verify no regressions, and formalize the budget
contract via `perf_targets.json` + `@pytest.mark.perf` test.

## Defaults

- Require a baseline profile path before starting any code change.
- Walk the optimization escalation ladder in order (rung 1 → 7). Never skip.
- After each change: `start_fast_profile` → `compare_profiles(baseline, candidate)`.
- Declare done only when `verify_perf` returns `overall_verdict = ok`.
- When driven by simulation tests: gate on `simulation_test_id`; re-run at 4K (`LKS_SIMULATION_4K=1 pytest <id> -m simulation`); declare done only when simulation JSON `overall_verdict = ok` at 4K.
- **Stall cap (O4):** stop after **2** consecutive attempts with <10% gain unless each delivered ≥10% behavior-neutral improvement.
- **Global consult (O5):** consult user after **5** total optimization attempts on one `simulation_test_id`.
- **No budget weakening (O6)** without explicit user approval.

## Loaded Context

1. `performance.instructions.md` — budget rules, escalation ladder, perf JSON schema
2. `codebase_router.instructions.md` — module inventory
3. `architecture.instructions.md` — co-location and file structure rules
4. `testing.instructions.md` — test conventions
5. `core.instructions.md` — Python standards

## Workflow

Follow the full `perf-tune` skill (`.github/skills/perf-tune/SKILL.md`) including
Phase 3 (fix), Phase 4 (formalize PerfTarget), and Phase 5 (gate check).

## perf_targets.json Co-location Rule

Every `perf_targets.json` MUST be placed in the module directory it covers:

```
src/lks_utils/<module>/perf_targets.json
```

It exports `TARGETS: dict[str, PerfTarget]` — never a bare list.

## Perf Test JSON Contract

The `@pytest.mark.perf` test MUST write to:

```
debug/perf/<module>/<test>.json
```

With `overall_verdict` field set to `ok`, `warn`, or `fail`.
`verify_perf(test_id, pytest_root)` reads this file — if it does not exist, the
test is non-conforming and must be fixed before declaring done.

## Guardrails

- Never add a cross-frame cache (rung 7) without an explicit `key` dataclass.
- Never declare work done when `overall_verdict` is `fail` or when the verdict
  file does not exist.
- Do not modify existing `@pytest.mark.perf` tests that already pass — only add new ones
  or fix broken ones.
- For GPU surfaces: GPU path must be the default renderer, CPU is fallback/reference only.
- **Do not optimize a wrapped/composited surface when a sibling variant with the
  same contents is already fast.** Run Phase 2.5 (composition isolation) of
  `perf-tune` first. If the wrapper is the bug, the fix is a wrapper swap, not
  a renderer optimization. Canonical example: `QOpenGLWidget` (FBO + DWM
  composition, 30 FPS lock risk on Windows) vs `QOpenGLWindow + createWindowContainer`
  (direct native swap chain) — see `performance.instructions.md`
  § Qt / Windows Render Surface Gotchas.
- **Verify profiler observer-effect is not the source of perceived slowness**
  before applying any fix. If the user reports "feels faster with profiler off,"
  first check that the profiler widget has a true off state (no refresh timer,
  no sample ingestion, no GPU timer queries when collapsed/hidden).
