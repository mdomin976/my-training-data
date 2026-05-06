"""READINESS_VISUALS_IMPL.py
Executable implementation — ImReady4 v4.42
Call render_readiness_visuals(latest, history) from any pre-workout or readiness report.
Returns: (png_path, markdown_table_string)

RHR SOURCE: always uses current_metrics.resting_hr (not resting_hr_snapshot)
for both today's value and the 30-day baseline history.

Dependencies: matplotlib, numpy (standard in Jupyter/Colab)
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import math
import os

# ─────────────────────────────────────────────
# §2.8  getScore — exact translation of MATLAB v4.42
# ─────────────────────────────────────────────
def getScore(scoreHRV, scoreRHR):
    nan = float('nan')
    def _is_nan(v):
        try: return math.isnan(v)
        except: return v is None
    if _is_nan(scoreHRV) or _is_nan(scoreRHR) or scoreHRV is None or scoreRHR is None:
        return "...?", ["No HRV data Today", "Take a measurement."], 7
    elif scoreRHR <= 1 and scoreRHR > -1 and scoreHRV > 1:
        return "HIT",    ["Ready for", "Intensive Training"], 1
    elif scoreRHR <= -2 and scoreHRV >= -1 and scoreHRV < 0:
        return "LIT",    ["Low intensity training", " "], 2
    elif scoreRHR <= -2 and scoreHRV >= 0:
        return "LIT!",   ["Keep calm!", "Acute fatigue signs"], 3
    elif scoreRHR < 1.7 and scoreHRV >= -1:
        return "Normal", ["Go on!", "Train as planned."], 4
    elif scoreHRV >= -1:
        return "LIT",    ["Low intensity training", " "], 2
    elif scoreRHR <= -2:
        return "Rest",   ["Time to recover", "Avoid overtraining"], 5
    elif scoreRHR <= 1.7:
        return "LIT",    ["Low intensity training", "Recovery is not complete"], 3
    else:
        return "REST!",  ["Be careful!", "Illness or stress detected"], 6

# ─────────────────────────────────────────────
# §2.9  Zone colours by code
# ─────────────────────────────────────────────
ZONE_COLORS = {
    1: (120/255, 240/255, 120/255),
    2: (230/255, 230/255, 230/255),
    3: (255/255, 165/255,   0/255),
    4: (180/255, 240/255, 180/255),
    5: (220/255, 220/255, 220/255),
    6: (255/255, 120/255, 120/255),
    7: (255/255, 255/255, 255/255),
}

# ─────────────────────────────────────────────
# §2.3  Coordinate transform
# ─────────────────────────────────────────────
ANG_LIMIT = 1.5 * math.pi / 2

def to_xy(scoreHRV, scoreRHR):
    r     = -scoreHRV + 6
    theta = scoreRHR / 3 * ANG_LIMIT
    return r * math.sin(theta), r * math.cos(theta)

# ─────────────────────────────────────────────
# §2.4  drawZone — curved arcs, >=100 points
# ─────────────────────────────────────────────
def drawZone(ax, xL, xR, yB, yU, color, n_arc=150, zorder=1):
    sRHR_arc = np.linspace(xL, xR, n_arc)
    bot = [to_xy(yB, s) for s in sRHR_arc]
    top = [to_xy(yU, s) for s in reversed(sRHR_arc)]
    verts = bot + top + [bot[0]]
    ax.fill([p[0] for p in verts], [p[1] for p in verts],
            color=color, zorder=zorder, linewidth=0)

# ─────────────────────────────────────────────
# §2.5  drawGrid — concentric arcs, >=300 points
# ─────────────────────────────────────────────
def drawGrid(ax):
    gc = (100/255, 100/255, 100/255)
    for i in range(-3, 4):
        lw = 1.0 if i in (-3, 0, 3) else 0.75
        ls = '-'  if i in (-3, 0, 3) else '--'
        theta_i = i / 3 * ANG_LIMIT
        ax.plot([2.8 * math.sin(theta_i), 9.2 * math.sin(theta_i)],
                [2.8 * math.cos(theta_i), 9.2 * math.cos(theta_i)],
                color=gc, lw=lw, ls=ls, zorder=3)
        sRHR_arr = np.linspace(-3, 3, 300)
        xs = [to_xy(i, s)[0] for s in sRHR_arr]
        ys = [to_xy(i, s)[1] for s in sRHR_arr]
        ax.plot(xs, ys, color=gc, lw=lw, ls=ls, zorder=3)
    for i in range(-3, 4):
        theta_i = i / 3 * ANG_LIMIT
        ax.text(9.6*math.sin(theta_i), 9.6*math.cos(theta_i), str(i),
                ha='center', va='center', fontsize=8, color=gc, zorder=4)
        ax.text(2.4*math.sin(theta_i), 2.4*math.cos(theta_i), str(i),
                ha='center', va='center', fontsize=7, color=gc, zorder=4)

# ─────────────────────────────────────────────
# §2.6  Trail + today point
# ─────────────────────────────────────────────
def drawTrailAndToday(ax, trail_scores, today_scores):
    """trail_scores: list of (sHRV, sRHR) from oldest to newest (up to 5)
    today_scores: (sHRV, sRHR)"""
    n = len(trail_scores)
    if n > 0:
        pts = [to_xy(s[0], s[1]) for s in trail_scores]
        ax.plot([p[0] for p in pts], [p[1] for p in pts],
                'k--', lw=0.8, zorder=5)
        for idx, (sh, sr) in enumerate(trail_scores):
            i_rank = idx + 2
            ms = 4 + (n + 1) / i_rank / 2
            ic = min(0.5 + (i_rank / (n + 1)) / 2, 1.0)
            x, y = to_xy(sh, sr)
            ax.plot(x, y, 'o', markersize=ms,
                    color=(ic, ic, ic), markeredgecolor='k',
                    markeredgewidth=0.5, zorder=6)
    xx, yy = to_xy(*today_scores)
    ax.plot([0, xx], [0, yy], color='k', lw=0.5, zorder=7)
    ax.plot(xx, yy, 'o', markersize=14, color='blue',
            markeredgecolor='white', markeredgewidth=1.5, zorder=8)
    ax.plot(xx, yy, 'o', markersize=10, color='white',
            markeredgecolor='white', zorder=9)
    ax.plot(xx, yy, '*', markersize=16, color='blue', zorder=10)

# ─────────────────────────────────────────────
# §2.7  Central circle with label
# ─────────────────────────────────────────────
def drawReady4(ax, label, code, detail, scoreHRV, scoreRHR, rmssd, rhr):
    theta_c = np.linspace(0, 2*math.pi, 100)
    cx = 2 * np.cos(theta_c)
    cy = 2 * np.sin(theta_c)
    color = ZONE_COLORS[code]
    ax.fill(cx, cy, color=color, zorder=11)
    ax.plot(cx, cy, color='gray', lw=0.6, zorder=12)
    ax.text(0, 0.3, label, ha='center', va='center',
            fontsize=15, fontweight='bold', zorder=13)
    detail_str = detail[0] + '\n' + detail[1]
    ax.text(0, -4.5, detail_str, ha='center', va='center',
            fontsize=11, linespacing=1.5, zorder=13)
    sHRV_str = f"{scoreHRV:+.2f}" if scoreHRV is not None else "n/a"
    sRHR_str = f"{scoreRHR:+.2f}" if scoreRHR is not None else "n/a"
    ax.text(0, -6.4,
            f"scoreHRV  {sHRV_str}   |   scoreRHR  {sRHR_str}",
            ha='center', fontsize=9, family='monospace', zorder=13)
    rmssd_str = f"{rmssd:.0f}" if rmssd is not None else "n/a"
    rhr_str   = f"{rhr}"       if rhr   is not None else "n/a"
    ax.text(0, -7.2,
            f"rMSSD: {rmssd_str} ms   |   RHR: {rhr_str} bpm",
            ha='center', fontsize=8.5, family='monospace', zorder=13)

# ─────────────────────────────────────────────
# §2.2  Compute scores from history
# ─────────────────────────────────────────────
def compute_scores(rmssd_today, rhr_today, history_daily):
    """history_daily: list of dicts with keys 'rmssd' and 'rhr' (resting_hr),
    sorted oldest->newest, covering the last ~30 days (today NOT included).
    RHR always uses resting_hr — no snapshot field.
    Returns (scoreHRV, scoreRHR)"""
    try:
        rmssd_log_today = 20 * math.log(rmssd_today) if rmssd_today and rmssd_today > 0 else None
        rhr_today_val   = rhr_today

        hrv_log_hist = [20 * math.log(d['rmssd']) for d in history_daily
                        if d.get('rmssd') and d['rmssd'] > 0]
        rhr_hist     = [d['rhr'] for d in history_daily
                        if d.get('rhr') and d['rhr'] > 0]

        window_hrv = hrv_log_hist[-30:]
        window_rhr = rhr_hist[-30:]

        if len(window_hrv) < 5 or rmssd_log_today is None:
            scoreHRV = None
        else:
            m, s = np.mean(window_hrv), np.std(window_hrv)
            scoreHRV = float((rmssd_log_today - m) / s) if s > 0 else 0.0

        if len(window_rhr) < 5 or rhr_today_val is None:
            scoreRHR = None
        else:
            m, s = np.mean(window_rhr), np.std(window_rhr)
            scoreRHR = float((rhr_today_val - m) / s) if s > 0 else 0.0

        return scoreHRV, scoreRHR
    except Exception as e:
        print(f"[READINESS_VISUALS] score compute error: {e}")
        return None, None

# ─────────────────────────────────────────────
# §3  Semaphore table logic
# ─────────────────────────────────────────────
def _emoji(status):
    return {'green': '🟢', 'amber': '🟡', 'red': '🔴'}.get(status, '⚪')

def build_semaphore_table(signals_dict, date_str, p_section11, imready4_label, imready4_code):
    """
    signals_dict: from readiness_decision.signals in latest.json
    Returns markdown string for the full semaphore table.
    """
    imready4_to_p = {1: 3, 4: 3, 2: 2, 3: 1, 5: 1, 6: 0, 7: None}
    p_imready4 = imready4_to_p.get(imready4_code)
    final_p = min(p_section11, p_imready4) if p_imready4 is not None else p_section11
    p_labels = {0: 'STOP 🛑', 1: 'REDUCE ⚠️', 2: 'MODIFY 🟡', 3: 'GO 🟢'}

    rows = []
    s = signals_dict
    if s.get('hrv') and s['hrv'].get('status'):
        h = s['hrv']
        delta = h.get('delta_pct', 0)
        rows.append(f"| HRV | {h.get('value','?')} | {_emoji(h['status'])} | vs base {h.get('baseline_7d','?')} ({delta:+.1f}%) |")
    if s.get('rhr') and s['rhr'].get('status'):
        h = s['rhr']
        delta = h.get('delta_bpm', 0)
        rows.append(f"| RHR | {h.get('value','?')} bpm | {_emoji(h['status'])} | vs base {h.get('baseline_7d','?')} ({delta:+.1f} bpm) |")
    if s.get('sleep') and s['sleep'].get('status'):
        h = s['sleep']
        quality_map = {1:'GREAT', 2:'OK', 3:'POOR', 4:'WORST'}
        quality_str = quality_map.get(h.get('quality'), '?')
        rows.append(f"| Sleep | {h.get('hours','?')}h | {_emoji(h['status'])} | calidad {quality_str} |")
    if s.get('acwr') and s['acwr'].get('status'):
        h = s['acwr']
        rows.append(f"| ACWR | {h.get('value','?')} | {_emoji(h['status'])} | — |")
    if s.get('ri') and s['ri'].get('status'):
        h = s['ri']
        rows.append(f"| RI | {h.get('value','?')} | {_emoji(h['status'])} | ayer {h.get('value_yesterday','?')} |")
    if s.get('tsb') and s['tsb'].get('status'):
        h = s['tsb']
        rows.append(f"| TSB | {h.get('value','?')} | {_emoji(h['status'])} | — |")

    table = f"""**SEMAFORO READINESS · {date_str}**

| Señal | Valor | Estado | Nota |
|-------|-------|--------|------|
""" + "\n".join(rows) + "\n"
    table += f"\n**Section 11: P{p_section11} · ImReady4: {imready4_label} (P{p_imready4 if p_imready4 is not None else '?'}) → Nivel final: P{final_p} {p_labels[final_p]}**\n"
    return table

# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
def render_readiness_visuals(latest: dict, history: dict, out_dir: str = 'output') -> tuple:
    """
    Generates:
      1. Radar ImReady4 PNG  → saved to out_dir/imready4_radar.png
      2. Semaphore markdown table string

    RHR SOURCE: always resting_hr (current_metrics.resting_hr).
    Baseline history also uses resting_hr field — no snapshot mixing.

    Returns: (png_path: str, table_md: str)
    """
    os.makedirs(out_dir, exist_ok=True)

    # ── Extract today's values ────────────────
    cm   = latest.get('current_metrics', latest.get('current_status', {}).get('current_metrics', {}))
    rd   = latest.get('readiness_decision', {})
    sigs = rd.get('signals', {})

    rmssd_today = cm.get('hrv_snapshot_rmssd') or cm.get('hrv')
    # RHR: always use resting_hr — never resting_hr_snapshot
    rhr_today   = cm.get('resting_hr')

    # ── Build 30-day history for z-score ──────
    # RHR history: always resting_hr field — consistent with today's value
    daily_90d = history.get('daily_90d', []) if history else []
    hist_entries = []
    for d in daily_90d:
        r  = d.get('rmssd') or d.get('hrv')
        rh = d.get('resting_hr') or d.get('rhr')
        if r and rh:
            hist_entries.append({'rmssd': float(r), 'rhr': float(rh)})
    hist_entries = hist_entries[:30]

    scoreHRV, scoreRHR = compute_scores(rmssd_today, rhr_today, hist_entries)

    # ── Trail (last 5 days, excl. today) ─────
    trail_entries = hist_entries[-5:] if hist_entries else []
    trail_scores  = []
    for e in trail_entries:
        sh, sr = compute_scores(e['rmssd'], e['rhr'], hist_entries[:hist_entries.index(e)])
        if sh is not None and sr is not None:
            trail_scores.append((sh, sr))

    label, detail, code = getScore(scoreHRV, scoreRHR)

    # ── FIGURE ───────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 7.5))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    ax.set_xlim(-10.8, 10.8)
    ax.set_ylim(-8.5, 10.8)
    ax.axis('off')

    athlete_loc  = latest.get('athlete_profile', {}).get('location', 'Athlete')
    athlete_name = athlete_loc.split(',')[0] if athlete_loc else 'Athlete'
    fig.suptitle(f"{athlete_name}: advice", fontsize=12, y=0.98)

    zone_table = [
        (-3, 3,  -3,  3,   (220/255, 220/255, 220/255)),
        (1.7, 3, -3, -1,   (255/255,   0/255,   0/255)),
        (-2, 1.7,-3, -1,   (255/255, 165/255,   0/255)),
        (-3, -2,  0,  3,   (255/255, 165/255,   0/255)),
        (-2, 1.7,-1,  3,   (200/255, 255/255, 200/255)),
        (-1,  1,  1,  3,   (  0/255, 255/255,   0/255)),
        (-3, -2, -3, -1,   (160/255, 160/255, 160/255)),
    ]
    for (xL, xR, yB, yU, col) in zone_table:
        drawZone(ax, xL, xR, yB, yU, col)

    drawGrid(ax)

    sh_today = scoreHRV if scoreHRV is not None else 0.0
    sr_today = scoreRHR if scoreRHR is not None else 0.0
    drawTrailAndToday(ax, trail_scores, (sh_today, sr_today))
    drawReady4(ax, label, code, detail, scoreHRV, scoreRHR, rmssd_today, rhr_today)

    png_path = os.path.join(out_dir, 'imready4_radar.png')
    plt.tight_layout()
    plt.savefig(png_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)

    # ── §3 Semaphore table ───────────────────
    p_ladder_map = {'go': 3, 'modify': 2, 'reduce': 1, 'skip': 0}
    rec = rd.get('recommendation', 'go')
    p_section11 = p_ladder_map.get(rec, 3)

    from datetime import date
    date_str = date.today().isoformat()
    table_md = build_semaphore_table(sigs, date_str, p_section11, label, code)

    return png_path, table_md


# ─────────────────────────────────────────────
# Quick CLI test
# ─────────────────────────────────────────────
if __name__ == '__main__':
    import json, sys
    latest_path  = sys.argv[1] if len(sys.argv) > 1 else 'latest.json'
    history_path = sys.argv[2] if len(sys.argv) > 2 else 'history.json'
    with open(latest_path)  as f: latest  = json.load(f)
    with open(history_path) as f: history = json.load(f)
    png, md = render_readiness_visuals(latest, history)
    print(f"Radar saved → {png}")
    print(md)
