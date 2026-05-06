# COACH_HOOKS.md
**Version:** 1.0  
**Last updated:** 2026-05-06  
**Priority:** HIGHEST — these rules override all other documents including SECTION_11 and DOSSIER for execution order.

This file defines **mandatory execution hooks** that the AI coach must run automatically, without being asked, in the scenarios listed below. The hooks are self-contained steps — they do not replace SECTION_11 logic, they run *before* the coaching text is written.

---

## HOOK-01: Readiness Visuals (DOSSIER §6.5 Enforcement)

### Trigger
This hook fires on **ANY** of the following query types:
- Pre-workout report
- Morning report / readiness check
- “cómo estoy hoy” / “how am I today”
- “puedo entrenar” / “can I train”
- Any query asking about current readiness, state, or go/modify/skip decision
- Any report that includes HRV, RHR, Sleep, ACWR, RI, or TSB metrics

### What to execute — mandatory, no exceptions

**Step A — Radar ImReady4**  
Execute `READINESS_VISUALS_IMPL.py::render_readiness_visuals(latest, history)` using the `execute_code` tool.  
The function returns `(png_path, table_md)`.  
Display the PNG inline before any coaching text using the image output from the code execution.

If code execution is unavailable in the current environment, generate the radar using the fallback procedure below.

**Step B — Semaphore table**  
Use the `table_md` string returned by `render_readiness_visuals()` verbatim.  
If code execution failed, build the semaphore table manually from `readiness_decision.signals` in `latest.json` following MORNING_REPORT_VISUALS.md §3.

### Output order
```
1. [Radar PNG image]
2. [Semaphore table markdown]
3. [Coach readiness text / recommendation]
```
Do NOT reorder. Do NOT skip either visual even if the user did not explicitly request them.

### Fallback — when execute_code is unavailable
If the `execute_code` tool is not available or throws an error:
1. **Radar:** Render a text-art approximation using the zone label from `getScore(scoreHRV, scoreRHR)` and display the zone code prominently (e.g. `⭐ ZONE: Normal — Go on! Train as planned.`)
2. **Semaphore table:** Build manually from `readiness_decision.signals` using the 🟢🟡🔴 logic in MORNING_REPORT_VISUALS.md §3. This table is **never** optional — it must always be rendered.

### How to compute scoreHRV and scoreRHR
Use the 30-day rolling window from `history.json > daily_90d[]`:
```
scoreHRV = (ln(rMSSD_today) × 20 - mean_30d) / std_30d
scoreRHR = (RHR_today - mean_30d_rhr) / std_30d_rhr
```
Source fields in `latest.json`:
- `rMSSD_today` → `current_metrics.hrv_snapshot_rmssd`
- `RHR_today`   → `current_metrics.resting_hr_snapshot`

If < 5 days of history exist, scoreHRV = scoreRHR = null → zone = `"...?"` per `getScore()` spec.

### Zone → Colour mapping
| Code | Zone label | Colour       |
|------|------------|--------------|
| 1    | HIT        | 🟢 Green       |
| 2    | LIT        | ⚪ Light grey  |
| 3    | LIT!       | 🟡 Amber       |
| 4    | Normal     | 🟢 Light green |
| 5    | Rest       | ⚪ Grey        |
| 6    | REST!      | 🔴 Red         |
| 7    | ...?       | ⚪ White       |

---

## HOOK-02: (reserved for future hooks)

---

## Maintenance
When adding a new hook:
1. Increment version in header
2. Add HOOK-NN section with Trigger + What to execute + Output order + Fallback
3. If a new `.py` implementation file is needed, commit it to this repo alongside this file
