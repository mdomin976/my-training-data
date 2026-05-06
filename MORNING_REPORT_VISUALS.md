# MORNING REPORT VISUALS — Rendering Spec
> Version: 2.2 (2026-05-06)

El morning report genera **exactamente una imagen**, seguida de una tabla Markdown:

1. **Imagen 1 — Radar ImReady4** (fiel al código MATLAB v4.42)
2. **Tabla — Semáforo P0–P3** (6 señales compuestas, Section 11, en Markdown)

Nada más. No hay paneles auxiliares, no hay HR/Power de ayer, no hay métricas de carga en las imágenes. Esos datos van en el texto del report.

---

## 1. CUÁNDO RENDERIZAR

Renderizar la imagen + tabla siempre que el usuario pida:
- "pre-workout report" / "informe de mañana" / "readiness de hoy"
- "cómo estoy hoy" / "puedo entrenar" / "morning report"
- cualquier consulta de estado antes de una sesión planificada

La imagen y la tabla van **antes** del texto de recomendación.

---

## 2. IMAGEN 1 — RADAR IMREADY4

### 2.1 Fuente de referencia

La implementación replica fielmente el código MATLAB ImReady4 v4.42 (`chartBackground`, `drawZone`, `drawGrid`, `drawReady4`, `getScore`). Python es el lenguaje de ejecución; la lógica es idéntica.

### 2.2 Fuente del rMSSD y cálculo de scores (z-scores sobre ventana 30d)

> **CRÍTICO — fuente del rMSSD:**
> Usar **`hrv_snapshot_rmssd`** de `latest.json` → `current_metrics.hrv_snapshot_rmssd` para el valor de hoy.
> El campo `hrv` de `latest.json` es el HRV4Training score (0–100), **NO** el rMSSD en ms. No usarlo para el cálculo de scoreHRV.
> Para el trail (días previos), usar `history.json` campo `rmssd` (en ms).

```python
# Igual que MATLAB v4.42
HRV_rMSSD = 20 * log(rMSSD)   # log natural; rMSSD en ms

# Para cada día i en los últimos 30 (desde history.json):
window = HRV_rMSSD[i : i+30]
scoreHRV = (HRV_rMSSD[i] - mean(window)) / std(window)

window_rhr = RHR[i : i+30]
scoreRHR   = (RHR[i]      - mean(window_rhr)) / std(window_rhr)
```

Los scores se clampean implícitamente al rango visible del grid (±3 es el límite de representación).

### 2.3 Transformación de coordenadas

```python
angLimit = 1.5 * pi / 2
r     = -scoreHRV + 6
theta = scoreRHR / 3 * angLimit
X = r * sin(theta)
Y = r * cos(theta)

# Función helper reutilizable:
def to_xy(scoreHRV, scoreRHR):
    r     = -scoreHRV + 6
    theta = scoreRHR / 3 * angLimit
    return r * sin(theta), r * cos(theta)
```

### 2.4 Zonas de color (drawZone en MATLAB)

> **CRÍTICO — bordes curvos:**
> Las zonas NO se dibujan interpolando solo las 4 esquinas del rectángulo. Los bordes de arco (yB y yU constantes) deben generarse con **≥100 puntos interpolados** en la dirección de scoreRHR para producir los bordes curvos propios de la proyección polar. Los bordes radiales (xL y xR constantes) sí son líneas rectas en el espacio XY.

```python
def drawZone(ax, xL, xR, yB, yU, color, n_arc=100, zorder=1):
    """
    xL, xR = límites de scoreRHR (→ eje angular)
    yB, yU = límites de scoreHRV  (→ radio)
    Bordes de arco: interpolar n_arc puntos en scoreRHR con sHRV fijo.
    Bordes radiales: dos puntos extremos (recta en XY).
    """
    sRHR_arc = linspace(xL, xR, n_arc)
    # Arco inferior (sHRV = yB, de xL a xR)
    bot = [to_xy(yB, s) for s in sRHR_arc]
    # Arco superior (sHRV = yU, de xR a xL — cierre antihorario)
    top = [to_xy(yU, s) for s in reversed(sRHR_arc)]
    verts = bot + top + [bot[0]]
    ax.fill([p[0] for p in verts], [p[1] for p in verts], color=color, zorder=zorder)
```

Tabla de zonas (orden de dibujado: primero el fondo, luego en orden):

| Zona     | xL   | xR   | yB   | yU   | Color RGB        |
|----------|------|------|------|------|-----------------|
| Fondo    | −3   | +3   | −3   | +3   | 220, 220, 220   |
| REST!    | +1.7 | +3   | −3   | −1   | 255, 0, 0       |
| LIT      | −2   | +1.7 | −3   | −1   | 255, 165, 0     |
| LIT      | −3   | −2   | 0    | +3   | 255, 165, 0     |
| Normal   | −2   | +1.7 | −1   | +3   | 200, 255, 200   |
| HIT      | −1   | +1   | +1   | +3   | 0, 255, 0       |
| Rest     | −3   | −2   | −3   | −1   | 160, 160, 160   |

### 2.5 Grid (drawGrid en MATLAB)

> **CRÍTICO — arcos del grid:**
> Los arcos concéntricos se generan pasando `sHRV = i` (constante) con `sRHR` variando de −3 a +3 a través de `to_xy`. **NO** son círculos simples de radio `r+6` centrados en el origen; eso produce arcos incorrectos. Usar ≥300 puntos.

```python
for i in range(-3, 4):
    lw = 1.0 if i in (-3, 0, 3) else 0.75
    ls = '-'  if i in (-3, 0, 3) else '--'

    # Líneas radiales (sRHR = i, r varía de 2.8 a 9.2)
    theta_i = i / 3 * angLimit
    x0, y0 = 2.8 * sin(theta_i), 2.8 * cos(theta_i)
    x1, y1 = 9.2 * sin(theta_i), 9.2 * cos(theta_i)
    ax.plot([x0, x1], [y0, y1], color=grid_color, lw=lw, ls=ls)

    # Arcos concéntricos: sHRV = i constante, sRHR varía de -3 a +3
    sRHR_arr = linspace(-3, 3, 300)
    xs = [to_xy(i, s)[0] for s in sRHR_arr]
    ys = [to_xy(i, s)[1] for s in sRHR_arr]
    ax.plot(xs, ys, color=grid_color, lw=lw, ls=ls)
```

- Color de grid: `[100, 100, 100] / 255`
- Etiquetas numéricas en borde exterior (`r=9.2`, usar theta de cada i) e interior (`r=2.8`)

### 2.6 Elementos dinámicos

```
TRAIL (últimos 5 días, excluyendo hoy — desde history.json):
- Línea discontinua negra conectando los puntos (k--)
- Para cada punto idx (0=más antiguo, n-1=ayer):
    i_rank = idx + 2        # i=2 es ayer, i=n+1 es más antiguo
    n      = n_trail + 1
    ms     = 4 + (n / i_rank) / 2     # tamaño marcador
    ic     = min(0.5 + (i_rank / n) / 2, 1.0)   # intensidad gris
    color  = (ic, ic, ic)
    marker: 'o', facecolor=color, edgecolor='k', edgewidth=0.5

PUNTO DE HOY:
- Línea desde (0,0) hasta (xx, yy): color='k', lw=0.5
- Círculo azul grande:  'o', facecolor='b', edgecolor='w', size=14, ew=1.5
- Círculo blanco encima: 'o', facecolor='w', edgecolor='w', size=10
- Estrella encima:       '*', color='b', size=16
```

### 2.7 Círculo central con label (drawReady4)

```python
# Polígono de 100 lados centrado en (0,0), radio=2
theta_c = linspace(0, 2*pi, 100)
cx = 2 * cos(theta_c)
cy = 2 * sin(theta_c)
ax.fill(cx, cy, color=zone_colors[code])
ax.plot(cx, cy, color='gray', lw=0.6)

# Texto grande: label (HIT / LIT / Normal / REST! / Rest / LIT!)
ax.text(0, 0.3, label, ha='center', va='center', fontsize=15, fontweight='bold')

# Texto pequeño con detalle: FUERA del radar, en y = -4.5
ax.text(0, -4.5, detail_line1 + '\n' + detail_line2,
        ha='center', va='center', fontsize=11, linespacing=1.5)

# Scores en y = -6.4 y -7.2 (fuente monoespaciada)
ax.text(0, -6.4, f"scoreHRV  {sHRV:+.2f}   │   scoreRHR  {sRHR:+.2f}",
        ha='center', fontsize=9, fontfamily='monospace')
ax.text(0, -7.2, f"rMSSD: {rmssd} ms   │   RHR: {rhr} bpm",
        ha='center', fontsize=8.5, fontfamily='monospace')
```

### 2.8 Lógica getScore (MATLAB v4.42 — traducción exacta)

```python
def getScore(scoreHRV, scoreRHR):
    if scoreRHR is None or scoreHRV is None or isnan(scoreRHR) or isnan(scoreHRV):
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
```

### 2.9 Colores por code (MATLAB `colors` cell array)

| Code | Label  | RGB                  |
|------|--------|----------------------|
| 1    | HIT    | 120, 240, 120        |
| 2    | LIT    | 230, 230, 230        |
| 3    | LIT!   | 255, 165, 0          |
| 4    | Normal | 180, 240, 180        |
| 5    | Rest   | 220, 220, 220        |
| 6    | REST!  | 255, 120, 120        |
| 7    | —      | 255, 255, 255        |

### 2.10 Dimensiones, ejes y fondo

- Figura cuadrada (~7×7.5 pulgadas). Fondo: blanco (fiel al MATLAB original).
- El radar ocupa toda la figura — sin paneles auxiliares.
- `ax.set_xlim(-10.8, 10.8)` · `ax.set_ylim(-8.5, 10.8)` — dejar espacio inferior para textos de score.
- `ax.axis('off')` — sin ejes cartesianos visibles.
- Título: `"{nombre atleta}: advice"` (como en MATLAB `h.Name`).

---

## 3. TABLA — SEMÁFORO P0–P3 (Markdown)

En lugar de una imagen, el semáforo se renderiza como una tabla Markdown inmediatamente después del radar.

### 3.1 Lógica de señales (6 señales)

| Señal  | Campo en latest.json          | Verde ✅                    | Ámbar 🟡                        | Rojo 🔴               |
|--------|-------------------------------|-----------------------------|---------------------------------|-----------------------|
| HRV    | `hrv` (overnight rMSSD)       | ≥ baseline_7d × 0.95        | 0.85–0.95×                      | < 0.85×               |
| RHR    | `resting_hr`                  | ≤ baseline_7d + 2 bpm       | +2 a +5 bpm                     | > +5 bpm              |
| Sleep  | `sleep_score`                 | ≥ 70                        | 55–69                           | < 55                  |
| ACWR   | `acwr`                        | 0.80–1.30                   | 0.70–0.79 ó 1.31–1.49           | < 0.70 ó ≥ 1.50       |
| RI     | `recovery_index` (latest.json)| ≥ 0.70                      | 0.50–0.69                       | < 0.50                |
| TSB    | `tsb`                         | −30 a +5                    | −40 a −31 ó +6 a +15            | < −40 ó > +15         |

> Si un campo es `null`, la señal se omite del cómputo y no penaliza.

### 3.2 Cálculo del nivel P

```python
rojos   = count(señales == rojo)
ambaros = count(señales == ambar)

if rojos >= 2:                        → P0  STOP
elif rojos == 1 or ambaros >= 3:      → P1  REDUCE
elif ambaros == 2:                    → P2  MODIFY
elif ambaros <= 1 and rojos == 0:     → P3  GO
```

### 3.3 Acción por nivel

| Nivel | Color hex | Etiqueta | Acción                                              |
|-------|-----------|----------|-----------------------------------------------------|
| P3    | #34D399   | GO       | Entrenar según plan. Sin modificaciones.            |
| P2    | #FFD700   | MODIFY   | Reducir intensidad. Sustituir Z4+ por Z2.           |
| P1    | #FF8C00   | REDUCE   | Solo Z1. Máx 60 min. Sin intervalos.                |
| P0    | #FF3232   | STOP     | Descanso obligatorio. Investigar causa.             |

### 3.4 Integración ImReady4 → nivel P

```python
imready4_to_p = {1: 3, 4: 3, 2: 2, 3: 1, 5: 1, 6: 0, 7: None}
p_imready4 = imready4_to_p[code_today]

# Nivel final = el más restrictivo
if p_imready4 is not None:
    final_level = min(p_section11, p_imready4)
else:
    final_level = p_section11
```

### 3.5 Formato de la tabla Markdown

Generar la tabla con emojis de color y el bloque de resultado al final:

```markdown
**SEMÁFORO READINESS · {fecha}**

| Señal | Valor | Estado | Nota |
|-------|-------|--------|------|
| HRV   | {val} ms | 🟢/🟡/🔴 | vs base {base} ms ({delta:+.0f}%) |
| RHR   | {val} bpm | 🟢/🟡/🔴 | vs base {base} (+{delta} bpm) |
| Sleep | Score {val} | 🟢/🟡/🔴 | {horas} |
| ACWR  | {val} | 🟢/🟡/🔴 | {interpretación} |
| RI    | {val} | 🟢/🟡/🔴 | {interpretación} |
| TSB   | {val} | 🟢/🟡/🔴 | {interpretación} |

**Section 11: P{n} · ImReady4: {label} (P{n}) → Nivel final: P{final} {ACCIÓN}**
```

- Usar emoji `🟢` `🟡` `🔴` para el estado de cada señal.
- La fila de resultado final va en negrita fuera de la tabla.
- Si una señal es `null`, omitir la fila.

---

## 4. FORMATO DE TEXTO COMPLEMENTARIO

Después de la imagen y la tabla, el coach añade el bloque de texto:

```
═══════════════════════════════════════════
READINESS  ·  {fecha}
═══════════════════════════════════════════

ImReady4: {label}  (code {n})
  rMSSD overnight: {val} ms  │  scoreHRV {val:+.2f}
  RHR overnight:  {val} bpm  │  scoreRHR {val:+.2f}

NIVEL FINAL: P{n}  →  {acción}

Nota del coach: {2–3 frases sobre compliance, carga, contexto}
═══════════════════════════════════════════
```

---

## 5. FUENTES DE DATOS

- **rMSSD de hoy**: `latest.json` → `current_metrics.hrv_snapshot_rmssd` (valor en ms)
- **rMSSD trail + RHR trail**: `history.json` campos `rmssd` y `rhr` de los últimos 30 días
- **scoreHRV / scoreRHR**: calcular con la fórmula §2.2 usando la ventana de history.json
- **Trail 5 días**: los 5 registros con datos válidos más recientes de `history.json` (excluyendo hoy)
- **Semáforo signals**: desde `latest.json` (campos `hrv`, `resting_hr`, `sleep_score`, `acwr`, `recovery_index`, `tsb`, baselines)
- Si `history.json` no está disponible, usar los scores pre-computados de `latest.json` (`derived_metrics`)

---

## 6. NOTAS DE MANTENIMIENTO

- Umbrales del semáforo (§3.1) se revisan al final de cada bloque de 4 semanas.
- La lógica `getScore` de ImReady4 (§2.8) NO se modifica sin actualizar también la versión MATLAB.
- La combinación ImReady4 ↔ Section 11 (§3.4) toma siempre el nivel más conservador.
- Versión: `2.2 (2026-05-06)` — cambio: Imagen 2 semáforo eliminada; sustituida por tabla Markdown (§3.5).
