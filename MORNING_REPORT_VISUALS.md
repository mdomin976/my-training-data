# MORNING REPORT VISUALS — Rendering Spec
> Version: 2.0 (2026-05-06)

El morning report genera **exactamente dos imágenes**, en este orden:

1. **Imagen 1 — Radar ImReady4** (fiel al código MATLAB v4.42)
2. **Imagen 2 — Semáforo P0–P3** (6 señales compuestas, Section 11)

Nada más. No hay paneles auxiliares, no hay HR/Power de ayer, no hay métricas de carga en las imágenes. Esos datos van en el texto del report.

---

## 1. CUÁNDO RENDERIZAR

Renderizar ambas imágenes siempre que el usuario pida:
- "pre-workout report" / "informe de mañana" / "readiness de hoy"
- "cómo estoy hoy" / "puedo entrenar" / "morning report"
- cualquier consulta de estado antes de una sesión planificada

Las imágenes van **antes** del texto de recomendación.

---

## 2. IMAGEN 1 — RADAR IMREADY4

### 2.1 Fuente de referencia

La implementación replica fielmente el código MATLAB ImReady4 v4.42 (`chartBackground`, `drawZone`, `drawGrid`, `drawReady4`, `getScore`). Python es el lenguaje de ejecución; la lógica es idéntica.

### 2.2 Cálculo de scores (z-scores sobre ventana 30d)

```python
# Igual que MATLAB v4.42
HRV_rMSSD = 20 * log(rMSSD)   # log natural

# Para cada día i en los últimos 30:
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
```

### 2.4 Zonas de color (drawZone en MATLAB)

Las zonas se dibujan aplicando la misma transformación polar a los vértices rectangulares:

| Zona     | xL   | xR   | yB   | yU   | Color RGB        |
|----------|------|------|------|------|-----------------|
| Fondo    | −3   | +3   | −3   | +3   | 220, 220, 220   |
| REST!    | +1.7 | +3   | −3   | −1   | 255, 0, 0       |
| LIT      | −2   | +1.7 | −3   | −1   | 255, 165, 0     |
| LIT      | −3   | −2   | 0    | +3   | 255, 165, 0     |
| Normal   | −2   | +1.7 | −1   | +3   | 200, 255, 200   |
| HIT      | −1   | +1   | +1   | +3   | 0, 255, 0       |
| Rest     | −3   | −2   | −3   | −1   | 160, 160, 160   |

> IMPORTANTE: en `drawZone`, el parámetro `yB` es el límite inferior y `yU` el superior. La zona se dibuja como polígono cerrado con los 4 lados transformados a coordenadas polares. Ver MATLAB para el orden exacto de vértices.

### 2.5 Grid (drawGrid en MATLAB)

- **Líneas radiales**: para cada entero i de −3 a +3, dibujar línea desde r=2.8 hasta r=9.2 en ángulo `theta = i/3 * angLimit`
- **Arcos concéntricos**: para cada entero r de −3 a +3, dibujar arco de radio `r+6` desde −angLimit a +angLimit
- Líneas en 0 y ±3: `lw=1.0, ls='-'`
- Líneas en ±1, ±2: `lw=0.75, ls='--'`
- Color de grid: `[100, 100, 100] / 255`
- Etiquetas numéricas en borde exterior (`r=9.2`) e interior (`r=2.8`)

### 2.6 Elementos dinámicos

```
TRAIL (últimos 5 días, excluyendo hoy):
- Línea discontinua negra conectando los puntos (k--)
- Para cada punto i (i=2 es ayer, i=5 es hace 4 días):
    ms   = 4 + (n/i) / 2          # tamaño marcador
    ic   = 0.5 + (i/n) / 2        # intensidad gris
    color = [ic, ic, ic]
    marker: 'o', facecolor=color, edgecolor='k'

PUNTO DE HOY (i=1):
- plot3([xx xx],[yy yy],[0 0], 'k-')   # línea vertical al centro
- Círculo azul grande: 'o', facecolor='b', edgecolor='w', size=14
- Círculo blanco encima: 'o', facecolor='w', edgecolor='w', size=10
- Estrella encima: '*', facecolor='b', edgecolor='b', size=16
```

### 2.7 Círculo central con label (drawReady4)

```python
# Polígono de 100 lados centrado en (0,0), radio=2
circle = nsidedpoly(100, center=(0,0), radius=2)
fill(circle, color=zone_color)

# Texto grande: label (HIT / LIT / Normal / REST! / Rest / LIT!)
text(0, 0, label, ha='center', va='middle', fontsize=14, fontweight='bold')

# Texto pequeño debajo: descripción de 2 líneas
text(0, -4.5, detail_line1 + '\n' + detail_line2, ha='center', va='middle', fontsize=12)
```

### 2.8 Lógica getScore (MATLAB v4.42 — traducción exacta)

```python
def getScore(scoreHRV, scoreRHR):
    if isnan(scoreRHR) or isnan(scoreHRV):
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

### 2.10 Dimensiones y fondo

- Figura cuadrada o ligeramente apaisada. Fondo: blanco o claro (fiel al MATLAB original)
- El radar ocupa toda la figura — sin paneles auxiliares
- Título: `"{nombre atleta}: advice"` (como en MATLAB `h.Name`)

---

## 3. IMAGEN 2 — SEMÁFORO P0–P3

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

### 3.5 Layout de la imagen

Figura apaisada (~10×5 pulgadas), fondo oscuro `#1a1a2e`:

```
┌────────────────────────────────────────────────────┐
│  SEMÁFORO READINESS  ·  {fecha}                    │
├──────────┬─────────────────────┬───────────────────┤
│  ● HRV   │  {valor} ms         │  {nota vs base}   │
│  ● RHR   │  {valor} bpm        │  {nota}           │
│  ● Sueño │  Score {valor}      │  {horas}          │
│  ● ACWR  │  {valor}            │  {interpretación} │
│  ● RI    │  {valor}            │  {interpretación} │
│  ● TSB   │  {valor}            │  {interpretación} │
├──────────┴─────────────────────┴───────────────────┤
│  SECTION 11: P{n}  ·  ImReady4: {label} (P{n})    │
│  ┌─────────────────────────────────────────────┐   │
│  │  P{final}  →  {ACCIÓN}                      │   │
│  └─────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

- Cada fila de señal: círculo coloreado (verde/ámbar/rojo) a la izquierda, nombre, valor y nota
- Banner final: fondo del color del nivel P, texto grande `P{n} → {ACCIÓN}`
- Fuente monoespaciada para valores

---

## 4. FORMATO DE TEXTO COMPLEMENTARIO

Después de las dos imágenes, el coach añade el bloque de texto:

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

- **scoreHRV / scoreRHR**: calcular desde `history.json` (rMSSD + RHR de los últimos 30 días) usando la fórmula §2.2
- **Trail 5 días**: los 5 registros más recientes de `history.json`
- **Semáforo signals**: desde `latest.json` (campos `hrv`, `resting_hr`, `sleep_score`, `acwr`, `recovery_index`, `tsb`, baselines)
- Si `history.json` no está disponible, usar los scores pre-computados de `latest.json` (`derived_metrics`)

---

## 6. NOTAS DE MANTENIMIENTO

- Umbrales del semáforo (§3.1) se revisan al final de cada bloque de 4 semanas.
- La lógica `getScore` de ImReady4 (§2.8) NO se modifica sin actualizar también la versión MATLAB.
- La combinación ImReady4 ↔ Section 11 (§3.4) toma siempre el nivel más conservador.
- Versión: `2.0 (2026-05-06)`
