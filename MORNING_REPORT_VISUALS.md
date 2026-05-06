# MORNING REPORT VISUALS — Rendering Spec

Este documento define cómo el AI coach debe renderizar gráficamente el bloque de readiness del morning report. Incluye dos componentes visuales:

1. **Radar ImReady4** — visualización bidimensional del estado HRV+RHR (scoreHRV vs scoreRHR)
2. **Semáforo P0–P3** — agregación de la escalera de readiness de Section 11

---

## 1. CUÁNDO RENDERIZAR

Renderizar ambos componentes siempre que el usuario pida:
- "pre-workout report" / "informe de mañana" / "readiness de hoy"
- "cómo estoy hoy" / "puedo entrenar"
- cualquier consulta de estado antes de una sesión planificada

El bloque visual va **antes** del texto de recomendación, no después.

---

## 2. COMPONENTE A — RADAR IMREADY4

### 2.1 Estructura del gráfico

El radar es una proyección polar 2D donde:
- **Eje angular (X)** = `scoreRHR` — FC de reposo relativa al baseline 30d
  - Izquierda (−3): RHR muy por debajo del baseline (fatiga parasimpática)
  - Centro (0): RHR en baseline
  - Derecha (+3): RHR muy por encima del baseline (estrés/carga)
- **Eje radial (Y)** = `scoreHRV` — HRV relativa al baseline 30d
  - Arriba (+3): HRV muy por encima del baseline (recuperación óptima)
  - Abajo (−3): HRV muy por debajo del baseline (fatiga/supresión)

**Transformación de coordenadas:**
```
angLimit = 1.5 × π/2
r     = −scoreHRV + 6
theta = scoreRHR / 3 × angLimit
X = r × sin(theta)
Y = r × cos(theta)
```

### 2.2 Zonas de color

| Zona | xL | xR | yB | yU | Color (RGB) | Label |
|------|----|----|----|----|-------------|-------|
| Fondo neutro | −3 | +3 | −3 | +3 | 220,220,220 | — |
| REST! | +1.7 | +3 | −3 | −1 | 255,50,50 | REST! |
| LIT (estrés alto) | −2 | +1.7 | −3 | −1 | 255,165,0 | LIT |
| LIT (fatiga) | −3 | −2 | 0 | +3 | 255,165,0 | LIT |
| Normal | −2 | +1.7 | −1 | +3 | 200,240,200 | Normal |
| HIT | −1 | +1 | +1 | +3 | 80,220,80 | HIT |
| Rest (fatiga+estrés) | −3 | −2 | −3 | −1 | 160,160,160 | Rest |

### 2.3 Grid y etiquetas

- Líneas radiales en −3, −2, −1, 0, +1, +2, +3 (scoreRHR)
- Arcos concéntricos en −3, −2, −1, 0, +1, +2, +3 (scoreHRV)
- Líneas principales (0, ±3): `lw=1.2, ls='-'`
- Líneas secundarias (±1, ±2): `lw=0.6, ls='--'`
- Etiquetas numéricas en borde exterior e interior del grid

### 2.4 Elementos dinámicos

```
# Trail histórico (últimos 5 días)
- Línea discontinua gris conectando los puntos
- Puntos grises degradados: más claro = más reciente, más oscuro = más antiguo
- Tamaño de marcador proporcional a la antigüedad (más pequeño = más antiguo)

# Punto de hoy
- Círculo relleno con color de zona (según code_today)
- Borde blanco/gris, tamaño 16–18pt
- Estrella (*) superpuesta en negro

# Círculo central (label)
- Radio = 2.1 unidades
- Color de fondo = color de zona del día
- Texto grande: label corto (HIT / LIT / Normal / REST! / Rest / LIT!)
- Texto pequeño: descripción de 1 línea ("Low intensity training", etc.)
```

### 2.5 Paneles auxiliares (optativos en modo texto)

Cuando se renderiza en modo completo (imagen), añadir bajo el radar:
- **Panel izquierdo**: HR + Power de la actividad de ayer (dual axis: potencia azul, FC roja)
- **Panel derecho**: tabla de métricas — Type, Time, Duration, Load, IF, RPE, FEEL + tabla rMSSD/SDNN/RHR hoy vs ayer

---

## 3. COMPONENTE B — SEMÁFORO P0–P3

### 3.1 Lógica de señales

El semáforo agrega **6 señales** en una puntuación compuesta. Cada señal emite un color:

| Señal | Campo en latest.json | Verde ✅ | Ámbar 🟡 | Rojo 🔴 |
|-------|---------------------|----------|----------|--------|
| **HRV** | `hrv` (overnight rMSSD) | ≥ baseline_7d × 0.95 | 0.85–0.95× | < 0.85× |
| **RHR** | `resting_hr` | ≤ baseline_7d + 2 bpm | +2 a +5 bpm | > +5 bpm |
| **Sleep** | `sleep_score` | ≥ 70 | 55–69 | < 55 |
| **ACWR** | `acwr` | 0.80–1.30 | 0.70–0.79 ó 1.31–1.49 | < 0.70 ó ≥ 1.50 |
| **RI** | `readiness_index` (Section 11) | ≥ 70 | 50–69 | < 50 |
| **TSB** | `tsb` | −30 a +5 | −40 a −31 ó +6 a +15 | < −40 ó > +15 |

> Nota: si un campo es `null` o no está disponible, la señal se omite del cómputo (no penaliza).

### 3.2 Cálculo del nivel P

```
rojos   = count(señales == rojo)
ámbaros = count(señales == ámbar)
verdes  = count(señales == verde)

if rojos >= 2:                       → P0  (STOP — no entrenar)
elif rojos == 1 or ámbaros >= 3:     → P1  (Modificar fuertemente — Z1 solo)
elif ámbaros == 2:                   → P2  (Modificar — reducir intensidad)
elif ámbaros <= 1 and rojos == 0:    → P3  (GO — entrenar según plan)
```

### 3.3 Acción recomendada por nivel

| Nivel | Color | Etiqueta | Acción |
|-------|-------|----------|--------|
| **P3** | 🟢 Verde | GO | Entrenar según plan. Sin modificaciones. |
| **P2** | 🟡 Ámbar | MODIFY | Reducir intensidad. Sustituir Z4+ por Z2. Acortar si TSS > 80. |
| **P1** | 🟠 Naranja | REDUCE | Solo Z1. Duración máxima 60 min. Sin intervalos. |
| **P0** | 🔴 Rojo | STOP | Descanso obligatorio. Investigar causa (enfermedad, sobreentrenamiento). |

### 3.4 Integración con ImReady4

El nivel P de Section 11 y el code de ImReady4 se combinan tomando el **más conservador**:

```
# Mapeo ImReady4 code → nivel P equivalente
code 1 (HIT)    → P3
code 4 (Normal) → P3
code 2 (LIT)    → P2
code 3 (LIT!)   → P1
code 5 (Rest)   → P1
code 6 (REST!)  → P0
code 7 (no data)→ sin modificación (usar solo Section 11)

# Nivel final = más restrictivo entre P_section11 y P_imready4
final_level = min(P_section11, P_imready4)   # P0 < P1 < P2 < P3
```

---

## 4. FORMATO DE SALIDA — MORNING REPORT

### 4.1 Bloque de texto (modo sin imagen)

```
═══════════════════════════════════════════
READINESS  ·  {fecha}
═══════════════════════════════════════════

SEMÁFORO P0–P3
  HRV    {val} ms   {emoji}
  RHR    {val} bpm  {emoji}
  Sleep  {val}      {emoji}
  ACWR   {val}      {emoji}
  RI     {val}      {emoji}
  TSB    {val}      {emoji}
  ─────────────────────────
  NIVEL SECTION 11:  P{n}  {emoji_nivel}

IMREADY4 SNAPSHOT
  rMSSD  {val} ms  │  scoreHRV {val:+.2f}
  RHR    {val} bpm │  scoreRHR {val:+.2f}
  ─────────────────────────
  ImReady4: {label}  (code {n})
  Source: snapshot / overnight

NIVEL FINAL: P{n}  →  {acción}
═══════════════════════════════════════════
```

### 4.2 Bloque gráfico (modo imagen — ejecutar código Python)

Layoutar en una figura de **14×9.5 pulgadas** con fondo oscuro `#1a1a2e`:

```
┌──────────────────────────────────────────────────────┐
│  HEADER: nombre atleta · fecha · versión              │
├──────────────────────────────────┬───────────────────┤
│                                  │  SEMÁFORO P0–P3   │
│     RADAR IMREADY4               │  ● HRV   ✅/🟡/🔴 │
│     (zona superior ~55% alto)    │  ● RHR   ✅/🟡/🔴 │
│                                  │  ● Sleep ✅/🟡/🔴 │
│                                  │  ● ACWR  ✅/🟡/🔴 │
│                                  │  ● RI    ✅/🟡/🔴 │
│                                  │  ● TSB   ✅/🟡/🔴 │
│                                  │  ──────────────── │
│                                  │  P{n} · {acción}  │
├──────────────────────┬───────────┴───────────────────┤
│  Ayer: HR + Power    │  Métricas: rMSSD/SDNN/RHR     │
│  (dual axis)         │  + actividad ayer              │
└──────────────────────┴───────────────────────────────┘
```

**Código Python de referencia:** ver `DOSSIER.md` §6.2 para lógica de z-scores. La función `get_label(scoreHRV, scoreRHR)` y `draw_zone()` ya están implementadas en las sesiones del coach. El semáforo se renderiza como una columna de `matplotlib.patches.Circle` con color verde/naranja/rojo según umbral.

---

## 5. IMPLEMENTACIÓN SUGERIDA

### Opción A — Python inline (recomendada para el AI coach)

El AI coach ejecuta el bloque Python directamente en cada morning report:

```
1. Fetch latest.json → extraer métricas
2. Calcular ImReady4 z-scores (DOSSIER §6.2)
3. Evaluar semáforo P0–P3 (este doc §3.1–3.2)
4. Combinar niveles → nivel final (§3.4)
5. Renderizar figura Matplotlib (layout §4.2)
6. Mostrar imagen + bloque de texto resumen
```

**Ventajas:** cero dependencias externas, funciona dentro del contexto del AI. El código ya existe y funciona (sesión 2026-05-06).

### Opción B — Script standalone `morning_report.py` en el repo

Para uso fuera del AI (terminal, cron job):

```python
# Estructura propuesta
morning_report.py
  ├── fetch_latest()           # lee latest.json desde GitHub raw
  ├── compute_imready4()       # z-scores según DOSSIER §6.2
  ├── compute_semaphore()      # lógica P0–P3 según este doc §3
  ├── render_figure()          # Matplotlib, layout §4.2
  └── main()                   # orquesta todo, guarda PNG + imprime texto
```

Puede ejecutarse con: `python morning_report.py --date 2026-05-06`
Guarda: `reports/morning_2026-05-06.png`

**Ventajas:** reutilizable, automatizable, independiente del AI.

### Opción C — Widget Intervals.icu (futuro)

Intervals.icu permite añadir custom fields a la página de wellness. Se puede enviar el nivel P calculado como `TrainingAdvice` (ya implementado en ImReady4 v4.42 para el code). Extensión natural: enviar también el nivel P0–P3 como nota de wellness diaria vía API `PUT /api/v1/athlete/{id}/wellness/{date}`.

**Ventajas:** visible directamente en la app sin salir de Intervals.icu.

---

## 6. NOTAS DE MANTENIMIENTO

- Los umbrales del semáforo (§3.1) se revisarán con el atleta al final de cada bloque de 4 semanas.
- Si Section 11 actualiza la escalera P0–P3, este documento se actualiza en paralelo.
- La lógica de combinación ImReady4 ↔ Section 11 (§3.4) es el corazón del sistema: **siempre tomar el nivel más conservador**.
- Versión actual de este documento: `1.0 (2026-05-06)`
