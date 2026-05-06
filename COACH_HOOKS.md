# COACH_HOOKS.md
**Version:** 1.2  
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
4. The function returns `png_path`. Display the PNG inline.

### Output order
```
1. [Radar PNG image]          ← from Step A
2. [Coach readiness text / recommendation]
```
Do NOT reorder. Do NOT skip the visual even if the user did not explicitly request it.

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
2. Add HOOK-NN section with Trigger + What to execute + Output order
3. Visual implementation lives in `READINESS_VISUALS_IMPL.py` — update that file if chart logic changes, not this one
