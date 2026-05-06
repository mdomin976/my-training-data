# COACH_HOOKS.md
**Version:** 1.1  
**Last updated:** 2026-05-06  
**Priority:** HIGHEST — these rules override all other documents including SECTION_11 and DOSSIER for execution order.

This file defines **mandatory execution hooks** that the AI coach must run automatically, without being asked, in the scenarios listed below. The hooks are self-contained steps — they do not replace SECTION_11 logic, they run *before* the coaching text is written.

---

## HOOK-01: Readiness Visuals (DOSSIER §6.5 Enforcement)

### Trigger
This hook fires on **ANY** of the following query types:
- Pre-workout report
- Morning report / readiness check
- "cómo estoy hoy" / "how am I today"
- "puedo entrenar" / "can I train"
- Any query asking about current readiness, state, or go/modify/skip decision
- Any report that includes HRV, RHR, Sleep, ACWR, RI, or TSB metrics

### What to execute — mandatory, no exceptions

**Step A — Fetch and run READINESS_VISUALS_IMPL.py**
1. Fetch the file content from:
   `https://raw.githubusercontent.com/mdomin976/my-training-data/main/READINESS_VISUALS_IMPL.py`
2. Copy the **full source code** into an `execute_code` tool call.
3. Append at the end of the code block:
   ```python
   render_readiness_visuals(latest, history)
   ```
   where `latest` and `history` are the parsed JSON objects from `latest.json` and `history.json`.
4. The function returns `(png_path, table_md)`. Display the PNG inline.

**Step B — Semaphore table**
Use the `table_md` string returned by `render_readiness_visuals()` verbatim as the semaphore table.

### Output order
```
1. [Radar PNG image]          ← from Step A
2. [Semaphore table markdown] ← from Step B (table_md)
3. [Coach readiness text / recommendation]
```
Do NOT reorder. Do NOT skip either visual even if the user did not explicitly request them.

### Fallback — when execute_code or fetch fails
If `READINESS_VISUALS_IMPL.py` cannot be fetched or `execute_code` throws an error:

1. **Radar:** Generate the radar manually using `execute_code` with inline Matplotlib code.
   Read all signal values from `readiness_decision.signals` in `latest.json` (fields: `hrv`, `rhr`, `sleep`, `acwr`, `ri`, `tsb` — each has `status`, `value`, and baseline fields).
   Map status to score: `green = 1.0`, `amber = 0.5`, `red = 0.1`, `unavailable = 0`.

2. **Semaphore table:** Build manually from `readiness_decision.signals` using 🟢🟡🔴⚪ for `green/amber/red/unavailable`.
   This table is **never** optional — it must always be rendered.

### Signal field reference (latest.json)
| Signal | Path | Key sub-fields |
|--------|------|----------------|
| HRV | `readiness_decision.signals.hrv` | value, baseline_7d, delta_pct, status |
| RHR | `readiness_decision.signals.rhr` | value, baseline_7d, delta_bpm, status |
| Sleep | `readiness_decision.signals.sleep` | hours, quality, status |
| ACWR | `readiness_decision.signals.acwr` | value, status |
| RI | `readiness_decision.signals.ri` | value, value_yesterday, status |
| TSB | `readiness_decision.signals.tsb` | value, status |

---

## HOOK-02: (reserved for future hooks)

---

## Maintenance
When adding a new hook:
1. Increment version in header
2. Add HOOK-NN section with Trigger + What to execute + Output order + Fallback
3. Visual implementation lives in `READINESS_VISUALS_IMPL.py` — update that file if chart logic changes, not this one
