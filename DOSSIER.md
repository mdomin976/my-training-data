# ATHLETE DOSSIER: Section 11

## 1. PHYSIOLOGY & ZONES
- **FTP:** 325W
- **Max HR:** 187 bpm
- **Resting HR:** 45 bpm
- **LTHR:** 172 bpm
- **Zone Preference:** Power-first for cycling/MTB. 
- **Notes:** Athlete has a high threshold (LTHR 172) relative to Max HR (187).

## 2. TRAINING BACKGROUND
- **Primary Sports:** Road Cycling, MTB.
- **Weekly Volume:** 10–12 hours.
- **Experience Level:** Advanced / Consistent.

## 3. GOALS & EVENTS
- **Primary Goal:** 200km Road Race preparation.
- **Focus:** Endurance durability and steady-state power for long-distance performance.

## 4. AVAILABILITY & PREFERENCES
- **Monday:** Rest Day (Preferred).
- **Tuesday/Wednesday:** Available for High-Intensity / Hard Sessions.
- **Thursday:** Recovery or Aerobic Base.
- **Friday/Saturday/Sunday:** Long Rides / Endurance volume.

## 5. COACHING PREFERENCES
- **Style:** Evidence-based, data-driven.
- **Focus:** Monitor decoupling on the long Friday-Sunday blocks to track aerobic durability for the 200km target.

---

## 6. HRV READINESS — SNAPSHOT METHODOLOGY (ImReady4 v4.42)

### 6.1 Data Source Priority
When calculating the daily HRV readiness score, use the following priority order:

1. **PRIMARY — Morning Snapshot rMSSD**: use `hrv_snapshot_rmssd` from `current_metrics` in `latest.json` when non-null.
2. **FALLBACK — Overnight/Passive HRV**: use `hrv` (RMSSD) from `current_metrics` when snapshot rMSSD is unavailable.
3. **RHR — always**: use `resting_hr` from `current_metrics` in **both** paths (snapshot and fallback). Never use `resting_hr_snapshot`.

Always surface which HRV source was used in the pre-workout report (e.g. `"HRV source: snapshot rMSSD"` or `"HRV source: overnight"`).

### 6.2 Score Computation (ImReady4 Algorithm)

The readiness score is derived from two standardised z-scores computed against a **30-day rolling window**.

**Step 1 — Transform raw values:**
```
HRV_rMSSD_log = 20 × ln(rMSSD)    [snapshot or overnight, see §6.1 priority]
RHR_raw       = resting_hr         [always — both snapshot and fallback paths]
```

> ⚠️ **Baseline consistency rule**: the RHR z-score baseline (mean_30d, std_30d) **must always be computed from `resting_hr`** history — the same field used as today's value in both paths.
> Mixing `resting_hr_snapshot` into any part of the RHR calculation is not permitted.

**Step 2 — Compute z-scores against 30-day rolling window:**
```
# SNAPSHOT PATH (hrv_snapshot_rmssd available)
scoreHRV = (20·ln(hrv_snapshot_rmssd_today) − mean_30d[hrv_snapshot_rmssd_log]) / std_30d[hrv_snapshot_rmssd_log]
scoreRHR = (resting_hr_today               − mean_30d[resting_hr])              / std_30d[resting_hr]

# FALLBACK PATH (hrv_snapshot_rmssd not available)
scoreHRV = (20·ln(hrv_today)  − mean_30d[hrv_log])  / std_30d[hrv_log]
scoreRHR = (resting_hr_today  − mean_30d[resting_hr]) / std_30d[resting_hr]
```
Note: scoreRHR formula is **identical** in both paths — `resting_hr` throughout.
Sign convention: a *higher* RHR than baseline yields a *positive* scoreRHR (stress signal).

**Step 3 — Classify readiness state:**

| scoreRHR | scoreHRV | Label | Code | Action |
|---|---|---|---|---|
| (−1, +1] | > +1 | **HIT** | 1 | Ready for intensive training |
| ≤ −2 | [−1, 0) | **LIT** | 2 | Low intensity — fatigue signs |
| ≤ −2 | ≥ 0 | **LIT!** | 3 | Keep calm — acute fatigue |
| < +1.7 | ≥ −1 | **Normal** | 4 | Train as planned |
| ≥ +1 (else) | ≥ −1 | **LIT** | 2 | Low intensity |
| ≤ −2 (else) | any | **Rest** | 5 | Time to recover |
| ≤ +1.7 (else) | < −1 | **LIT** | 3 | Recovery not complete |
| > +1.7 | < −1 | **REST!** | 6 | Illness or high stress |
| NaN | NaN | **…?** | 7 | No data — take measurement |

### 6.3 Integration with Section 11 Readiness Ladder

- The ImReady4 snapshot score is a **Tier-2 signal** — it supplements but does not replace the Section 11 P0–P3 readiness ladder (overnight HRV + RHR + Sleep + ACWR + RI + TSB).
- When snapshot rMSSD differs from overnight HRV by >15%, surface both and note the divergence in the coach note.
- Code-to-action mapping:
  - **Code 1 (HIT)** → reinforces P3 green — proceed with planned intensity
  - **Code 2/3 (LIT/LIT!)** → consider P2 modification — reduce intensity, add Z1 buffer
  - **Code 4 (Normal)** → consistent with P3 green
  - **Code 5/6 (Rest/REST!)** → escalate to P1/P0 — investigate, recommend rest or skip
  - **Code 7 (no data)** → fall back to overnight metrics only

### 6.4 Display in Pre-Workout Report
When snapshot data is available, include this line in the readiness block:
```
HRV Snapshot (ImReady4): <label> | rMSSD <val> ms | RHR <val> bpm (resting_hr) | Source: snapshot/overnight
```

### 6.5 Readiness Visuals — Obligatorio

> **REGLA OBLIGATORIA**: Cualquier informe que incluya métricas de readiness — pre-workout report, morning report, "cómo estoy hoy", "puedo entrenar", consulta de estado o similar — **debe renderizar siempre**:
>
> 1. **Imagen — Radar ImReady4**: ejecutar `READINESS_VISUALS_IMPL.py` vía `execute_code` y llamar `render_readiness_visuals(latest, history)`.
> 2. **Tabla Markdown — Semáforo P0–P3**: usar el `table_md` devuelto por la función.
>
> Ambos elementos van **antes** del texto de recomendación del coach.
> No omitir ninguno de los dos aunque el usuario no los pida explícitamente.

---

<!--
## PREVIOUS VERSION (pre-2026-05-06) — kept for rollback reference

v1 (2026-05-06 morning): RHR in snapshot path used resting_hr_snapshot. Fixed same day.
v2 (2026-05-06 afternoon): RHR unified to resting_hr in both snapshot and fallback paths.
resting_hr_snapshot removed from all RHR calculations and baselines.
-->
