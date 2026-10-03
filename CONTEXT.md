# CONTEXT.md — Time Poverty Lab: traslado laboral y uso del tiempo (ENUT 2024)

**Estado al 2026-10-03.** Verificado contra el repo (commit `04df096`), la base de Supabase y el despliegue de Vercel.
**Fase actual:** capa agéntica de descubrimiento. Los datos, el motor de experimentos y EXP-001 ya existen. Falta el ciclo en el que la evidencia cambia la siguiente decisión.
**Presupuesto:** 10 horas en total.
**Idiomas:** documentación y conversación en español. Interfaz web, demo, `README.md`, prompts de los agentes y textos guardados en Supabase en inglés. Identificadores de código en inglés.

> **Jerarquía de documentos.** Este archivo da el contexto completo: qué se construye, por qué, qué se decidió y en qué estado está. Las reglas operativas y los contratos están en [`AGENTS.md`](AGENTS.md). El estado detallado y las trampas técnicas están en [`MEMORY.md`](MEMORY.md). El significado de variables, población y métodos está en `docs/`. Si hay contradicción, gana primero lo que digan los datos y la documentación oficial de INEGI, luego `docs/` y luego `AGENTS.md`. El §13 lista los puntos donde `AGENTS.md` y `MEMORY.md` estaban desfasados el 2026-10-03.

---

## 1. Qué hay que construir

Un MVP web en el que **Omnigent orquesta en vivo agentes especialistas** para investigar una pregunta científica con microdatos reales de la **ENUT 2024** (Encuesta Nacional sobre Uso del Tiempo, INEGI). El sistema debe:

1. recuperar evidencia con citas (RAG sobre documentos oficiales y literatura);
2. formular hipótesis falsables y al menos dos pruebas candidatas;
3. elegir una prueba por aprendizaje esperado y ejecutarla con un motor determinista y reproducible;
4. someter el resultado a una crítica científica;
5. registrar cómo ese resultado cambia la siguiente decisión.

Nombre del proyecto en prompts y demo: **Time Poverty Lab**. Nombre del repo y del despliegue: **Commute & Time Lab** (`commute-time-lab`).

No ampliar a otras ciencias, mapas de rutas, recomendaciones de transporte, modelos causales, cuentas de usuario ni múltiples datasets. No pulir la UI antes de que funcione el ciclo.

## 2. Procedencia del contexto

- El equipo describió el problema y la pregunta inicial en esta [conversación compartida](https://chatgpt.com/share/6ac15b79-1c28-83e8-a15b-3095f4e79a66).
- El track es **Challenge 03 — Agentic Scientific Discovery** del Hack-Nation 7th Global AI Hackathon (con Databricks). El brief exige Omnigent y el ciclo «pregunta → evidencia → hipótesis → experimento → resultado → decisión actualizada».
- La capa de datos se construyó **fuera de este repo**, en fases con aprobación humana explícita: 1 auditoría → 2A staging semántico → 2B dataset canónico → 3 motor de experimentos y autorización de EXP-001. Sus artefactos se trajeron al repo en los commits `805b7c2` y `04df096`.
- La especificación original de este archivo (pregunta de 60 minutos semanales, cinco categorías de actividad, 18 horas de plazo) quedó superada. El §3 resume qué cambió.

## 3. Problema y pregunta científica

**Problema humano.** Muchas personas de CDMX y del Estado de México pasan horas viajando entre casa y trabajo. Queremos saber qué dimensiones del tiempo personal se asocian con una mayor carga de traslado y si el patrón cambia por sexo o por la presencia de menores en el hogar.

**Pregunta vigente.**

> Entre trabajadores de 18 a 65 años que residen en Ciudad de México (CDMX) y Estado de México (Edomex), ¿qué dimensión del tiempo personal muestra la asociación negativa más fuerte con **5 horas adicionales de traslado laboral entre semana** (`commute_5h`: 1 unidad = 300 minutos más de lunes a viernes)? ¿Difiere la asociación por sexo o por la presencia de menores en el hogar?

**Cuatro dimensiones canónicas** (outcomes primarios): sueño, higiene personal exclusiva, conversación exclusiva con integrantes del hogar y ocio. Definiciones exactas en [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md) y en el §5.

**Unidades.** Todos los tiempos son **minutos totales de lunes a viernes** de la semana de referencia. No son promedios diarios ni minutos de una semana de 7 días. `commute_5h = commute_weekday_min / 300`. Nunca llamar "una hora diaria" a 300 minutos de la semana laboral.

**Lenguaje obligatorio.** ENUT es observacional y transversal: se dice "se asocia con", nunca "causa", "reduce", "sacrifica" ni "provoca". La cobertura CDMX + Edomex no es una muestra representativa de la Zona Metropolitana del Valle de México.

**Métrica principal.** Minutos de lunes a viernes asociados a +300 minutos de traslado entre semana, por outcome, con `n`, método, incertidumbre (y su limitación de diseño) y procedencia.

### Qué cambió respecto a la especificación original

| Aspecto | Especificación original | Vigente (aprobada) |
|---|---|---|
| Exposición | +60 minutos **semanales** de traslado | `commute_5h`: +300 minutos de traslado **de lunes a viernes** |
| Unidades | minutos semanales | minutos totales de lunes a viernes; fin de semana excluido |
| Outcomes | sueño, convivencia, cuidados, ocio, cuidado personal | sueño, higiene personal exclusiva, conversación exclusiva en el hogar, ocio (11 componentes). **Cuidados fuera** |
| Población | 18+ con trabajo y traslado reportado | 18–65, trabajador activo (regla aprobada), sin ausentes en la semana, traslado resuelto; n = 2,563 |
| Heterogeneidad | sexo | sexo y presencia de menores |
| Método inicial | prueba A (medias por grupo) o prueba B (WLS con traslado × sexo) | motor determinista: regresión lineal ponderada por FAC_PER con CR1 por UPM, sin interacciones por ahora |
| Agentes | 4 roles (coordinador, evidencia, método/datos, crítico) | 7 agentes + Shared Research State (§9) |
| Plazo | 18 horas | 10 horas |

## 4. Requisitos del track y cómo se cubren

Ponderación: orquestación Omnigent 30 % · potencial científico 25 % · aceleración y aprendizaje 20 % · rigor 15 % · creatividad y responsabilidad 10 %.

| Requisito | Cómo se cubre | Estado |
|---|---|---|
| Omnigent (administrado o de código abierto) coordina el flujo real, traspasos, herramientas y cambio de plan | `omnigent.yaml`: Discovery Director raíz + 6 sub-agentes, 11 tools Python, políticas ASK | 🟡 Spec válido; falta la primera sesión real |
| Cada agente con decisión científica, herramientas, entradas y salida estructurada | Tabla de agentes (§9.2) y Shared Research State JSON | 🟡 Prompts desfasados |
| ≥2 pruebas, elección por aprendizaje/factibilidad/costo, ejecución y siguiente prueba justificada | `save_proposals` + motor + `record_decision` con reglas R1–R3 | ⏳ EXP-001 corrido a mano; EXP-002 aún sin elegir |
| Citas para afirmaciones factuales, hipótesis etiquetadas, incertidumbre, aprobaciones humanas | RAG con `source_id`/`passage_id`/locator; `hypotheses.generated_by`; ASK antes de ejecutar o decidir | ✅ Infraestructura lista |
| Mejora medida en un cuello de botella | Cronometrar flujo manual vs asistido (§15). El 10× del README es una **meta** | ⏳ Sin medir |
| Entregables: repo, configs y políticas, código y resultados, evidencia citada, mejora medida, siguiente experimento, demo de 2 min | Este repo + web desplegada + video | 🟡 Parcial |

## 5. Datos: de ENUT 2024 a `analytic_v1`

### Fuentes oficiales

[Microdatos CSV](https://www.inegi.org.mx/contenidos/programas/enut/2024/microdatos/enut_2024_bd_csv.zip) · [descriptor de archivos](https://www.inegi.org.mx/contenidos/programas/enut/2024/microdatos/enut_2024_fd.xlsx) · [diccionario de datos (catálogo RNM 1127)](https://www.inegi.org.mx/rnm/index.php/catalog/1127/data-dictionary) · [diseño conceptual](https://www.inegi.org.mx/contenidos/programas/enut/2024/doc/889463921929.pdf) · [diseño muestral](https://www.inegi.org.mx/contenidos/programas/enut/2024/doc/889463926528.pdf) · [página de microdatos](https://www.inegi.org.mx/programas/enut/2024/#Microdatos). En 2024 el campo `ENT` pasó a llamarse `CVE_ENT`.

Copias archivadas en el repo: `metadata/official/enut_2024_ddi.xml` (y `.json`) y `metadata/official/enut_2024_cuestionario.pdf`. El ZIP bruto **no** se versiona (`data/raw/` está en `.gitignore`).

### Pipeline (cerrado)

| Fase | Producto | Evidencia en el repo |
|---|---|---|
| 1 · Auditoría | inventario de tablas, llaves, códigos y faltantes | `reports/audit/enut_2024_audit.{md,json}` |
| 2A · Staging semántico | `staging_v1.parquet` (todas las personas de TMODULO, columnas crudas) | `reports/audit/phase2a_semantic_validation.{md,json}`, `metadata/mappings/staging_v1_features.json`. El parquet de staging **ya no está en el repo** |
| 2B · Dataset canónico | `data/processed/analytic_v1.parquet` | `reports/audit/phase2b_analytic_validation.{md,json}`, `phase2b_prebuild_checks.json`, `metadata/analytic_v1_manifest.json`, `metadata/mappings/analytic_v1_leisure.json` |
| 3 · Motor y EXP-001 | autorización `APPROVED_FOR_EXPERIMENTS` | `metadata/analytic_v1_experiment_approval.json`, `docs/EXPERIMENT_ENGINE.md` |

- SHA256 de `analytic_v1.parquet`: `973f2c010940da06048eb12ade53fa271525d82f68d3a157ad78e429d687dd94`. **Verificado el 2026-10-03:** coincide con el manifiesto y con el registro de aprobación.
- El manifiesto dice `final_human_approval = pending` porque refleja el momento de la fase 2B. La aprobación posterior vive en el registro de aprobación. No "corregir" el manifiesto.
- **No reconstruir el pipeline, no reinterpretar los datos crudos, no volver a limpiar y no modificar `analytic_v1.parquet`.** Una versión nueva es un archivo nuevo (`analytic_v2…`) con aprobación humana.

### Población analítica primaria

2,563 personas; suma de FAC_PER = 12,737,236.

- `state` ∈ {`09` CDMX, `15` Edomex}; edad 18–65 inclusive.
- `active_worker = P5_1 = 1 o P5_2 ∈ 1–6`. Se excluyen los ausentes en la semana de referencia (`P5_2 = 7`); `P5_2 = 8` queda fuera de la población. No se usa la clasificación oficial `COND_AEE`.
- Traslado resuelto. Sin filtros de caso completo, de trabajo positivo, de traslado positivo ni de extremos. Los ceros se marcan, no se eliminan.

### Variables canónicas

Fuente TMODULO salvo indicación. Linaje exacto por columna en el manifiesto.

| Variable | Fuente ENUT | Definición |
|---|---|---|
| `commute_weekday_min` | `P5_9_1`/`P5_9_2` (+ `P5_7` y flujo laboral) | 60 × horas + minutos. Con trabajo solo virtual (`P5_7 = 2`, que se salta la 5.9) es un **cero estructural marcado** |
| `commute_5h` | `commute_weekday_min` | ÷ 300 (exposición) |
| `commute_structural_zero` | `P5_7`, `P5_9_*` | verdadero solo para el salto aprobado de trabajo virtual |
| `sleep_weekday_min` | `P6_1_1_1`/`P6_1_1_2` | sueño exclusivo, incluye siestas; `99` = No sabe → nulo |
| `personal_hygiene_weekday_min` | `P6_1_3_1`/`P6_1_3_2` | higiene y arreglo exclusivo; **no** todo el autocuidado |
| `household_conversation_weekday_min` | `P6_21_1`, `P6_21A_1_1`/`P6_21A_1_2` | conversación exclusiva con integrantes del hogar; **no** todo el tiempo familiar |
| `leisure_weekday_min` | 11 pares de `P6_18`, `P6_19_1–2`, `P6_20_1–2`, `P6_22_1–6` | deporte, artes, juegos, espectáculos, sitios culturales, pantallas, audio, lectura, publicar en redes, navegar en redes y otro Internet recreativo. Excluye `P6_21`, `P6_23` y fin de semana |
| `work_weekday_min` | `P5_8_*` según `P5_5`/`P5_7` | ramas de trabajo según modalidad; control aprobado |
| `age`, `sex`, `state` | `EDAD_V`, `SEXO` (1 hombre, 2 mujer), `CVE_ENT` | controles aprobados |
| `work_modality` | `P5_7`, `P5_5` | presencial / virtual / mixta; nulo si no se preguntó |
| `has_child_u15`, `has_minor_u18`, `household_size` | TSDEM agregado por `LLAVEHOG` | composición del hogar; edad desconocida → nulo |
| `weight`, `stratum`, `cluster` | `FAC_PER`, `EST_DIS`, `UPM_DIS` | diseño muestral |
| `person_id`, `household_id` | `LLAVEMOD`, `LLAVEHOG` | llaves |

- **Faltantes en la población primaria:** 0 en exposición, outcomes, controles y diseño; `work_modality` 957 (no preguntada); `has_child_u15` y `has_minor_u18` 3 cada una.
- Solo `work_weekday_min`, `age`, `sex` y `state` están aprobadas como controles. Las demás variables canónicas no son controles automáticos.
- No forzar que las actividades sumen 24 h (ENUT capta actividades simultáneas). No recortar ni winsorizar extremos.
- ⚠️ Los nombres de variables cambian entre años: en ENUT 2019, `P5_4_*` era el traslado y `P5_9_*` la búsqueda de trabajo. En ENUT 2024, la pregunta 5.9 (`P5_9_*`) es el traslado.

## 6. Motor determinista de experimentos

```
ExperimentSpec  →  src.experiments.runner.run_experiment(spec)  →  ExperimentResult
```

Es **el único camino computacional aprobado** sobre `analytic_v1`. Ningún agente calcula, estima ni inventa cifras. Contrato completo en [`docs/EXPERIMENT_ENGINE.md`](docs/EXPERIMENT_ENGINE.md) y JSON Schema en `metadata/experiment_contract.schema.json`.

### Qué acepta hoy el `ExperimentSpec` (`src/experiments/schemas.py`, Pydantic estricto)

| Campo | Valores permitidos |
|---|---|
| `schema_version` / `experiment_id` | `1.0` / `EXP-NNN` |
| `dataset_version` | `analytic_v1` |
| `population` | `source = approved_analytic_v1`; `states` ⊆ {`09`, `15`}; `age_min`/`age_max` dentro de 18–65; `sexes` ⊆ {`male`, `female`}; `expected_n` opcional |
| `exposure` | `commute_5h` |
| `outcomes` | los 4 canónicos |
| `covariates` | `work_weekday_min`, `age`, `sex`, `state` |
| `method` | `weighted_linear_regression` (registro cerrado) |
| `hypothesis_ids` | `H1`, `H2` (H2 exige ≥2 outcomes) |
| `sensitivity_analyses` | `exclude_zero_weekday_work` |
| `missingness_policy` / `uncertainty` / `confidence_level` | `model_specific_complete_case` / `psu_cluster_CR1_t` / `0.95` |
| `survey_weight` / `cluster` / `stratum` | `weight` / `cluster` / `stratum` |
| `include_unadjusted` | booleano |

Campos, variables, métodos o valores desconocidos se rechazan. Ejemplo válido: `experiments/EXP-001/spec.json`.

### Método

- Mínimos cuadrados ponderados por FAC_PER (solver SVD), con intercepto, `commute_5h` y los controles pedidos. Referencias: hombre y estado `09`. Sin interacciones.
- Varianza sándwich agrupada por pares exactos (`EST_DIS`, `UPM_DIS`) con corrección CR1 e intervalos t con G − 1 grados de libertad. Validado contra statsmodels WLS + cluster CR1.
- **Limitación que toda salida conserva:** no es la varianza completa de encuesta compleja de ENUT. No hay centrado por estrato, FPC, réplicas ni reconstrucción del dominio fuera de `analytic_v1`. No llamarlo `svyglm` ni "varianza ajustada por diseño".
- **Ranking:** intervalos de Bonferroni para los 4 coeficientes (98.75 % individual) y para las 6 diferencias pareadas (99.1667 %), usando la covarianza entre outcomes de las mismas personas. El orden es `DISTINGUISHABLE_RANKING` solo si todas las diferencias ordenadas excluyen el cero. Si no, `INCONCLUSIVE_RANKING`.
- **Reproducibilidad:** verifica el SHA256 del parquet antes y después, corre cada spec dos veces y exige resultados idénticos. Escribe `result.json`, `summary.md`, `spec.json` y `validation.json` en `reports/experiments/<id>/`. Los resultados no llevan marcas de tiempo, así que mismo código + datos + spec + runtime = mismos bytes.
- **Fallos:** `ExperimentError` con código y mensaje (dataset incorrecto, pesos inválidos, rango incompleto, n ≤ p, menos de 2 UPM…). Nunca devuelve un resultado exitoso parcial.
- `review_status` siempre es `REQUIRES_HUMAN_REVIEW`. `EXPERIMENT_COMPLETED` es un estado técnico, no una aprobación científica.

### Qué cabe y qué no en el contrato actual

- **Cabe:** el mismo modelo en subpoblaciones (por sexo, estado o rango de edad) cambiando `population`. El motor exige rango completo: si se filtra un solo sexo (o un solo estado), hay que quitar `sex` (o `state`) de `covariates`, porque la columna queda constante y el modelo falla.
- **No cabe sin revisar el contrato:** interacciones (traslado × sexo, traslado × menores), términos no lineales, splines, categorías de traslado, modelos de dos partes (participación vs duración), `has_child_u15`/`has_minor_u18` como covariables, nuevos outcomes y las hipótesis H3/H4 en `hypothesis_ids`. Comparar formalmente pendientes entre sexos es H3, aunque estimarlas por separado sí cabe.
- Revisar el contrato exige cambiar a la vez `schemas.py`, el JSON Schema, `docs/EXPERIMENT_ENGINE.md` y los tests, con aprobación humana. El Planner debe declarar la factibilidad de cada candidato. Un candidato que exija revisión no se ejecuta sin ella.

## 7. EXP-001: el resultado de partida

Spec: `experiments/EXP-001/spec.json` (H1, H2; 4 outcomes; controles trabajo, edad, sexo y estado; versiones ajustada y sin ajustar; sensibilidad `exclude_zero_weekday_work` → 16 modelos). Detalle completo en [`reports/experiments/EXP-001/summary.md`](reports/experiments/EXP-001/summary.md).

**Estado:** `EXPERIMENT_COMPLETED` · revisión `REQUIRES_HUMAN_REVIEW` · ranking **`INCONCLUSIVE_RANKING`**.

Coeficientes por +300 min de traslado entre semana, en minutos de lunes a viernes (n = 2,563):

| Outcome | Ajustado | IC 95 % puntual | Sin ajustar | IC 95 % puntual |
|---|---:|---|---:|---|
| `sleep_weekday_min` | −48.711 | [−63.481, −33.940] | −56.414 | [−71.438, −41.389] |
| `leisure_weekday_min` | −20.396 | [−43.436, 2.644] | −27.223 | [−50.791, −3.656] |
| `household_conversation_weekday_min` | −3.816 | [−10.344, 2.712] | −4.395 | [−11.142, 2.351] |
| `personal_hygiene_weekday_min` | +3.094 | [−0.760, 6.948] | +2.041 | [−1.950, 6.031] |

- **Diferencias pareadas (Bonferroni):** solo sueño − conversación (−44.894 [−66.887, −22.902]) y sueño − higiene (−51.804 [−72.055, −31.554]) excluyen el cero. Sueño − ocio (−28.314 [−66.170, 9.541]) no se resuelve, igual que las otras tres.
- **Hipótesis:** H1 con evidencia compatible (sueño). H2 con evidencia de al menos una diferencia, sin orden completo. H3 y H4 no se evaluaron.
- **Sensibilidad:** excluir a las 34 personas con `work_weekday_min = 0` (n = 2,529) no cambia direcciones ni orden.
- **Diagnósticos:** 351 UPM, 19 estratos, 350 gl, R² ponderado ≤ 0.07, sin predicciones negativas, 168 puntos con leverage > 2p/n en los modelos ajustados (se conservan).
- **Reproducción:** dataset `973f2c01…dd94`, spec `b7fa540b…4d71`, código `7867362c…edd`, `result.json` `5e4084a3…6b28`. `validation.json`: misma spec → mismo resultado. `engine_validation.json`: 41 tests y 16 modelos validados contra statsmodels en el entorno del pipeline. `experiments/EXP-001/result.json` es una copia idéntica.

**Redacción aceptable:** "Longer weekday commuting showed the strongest negative point association with sleep in EXP-001, but uncertainty prevented a definitive ranking across all four time-use outcomes."
**Redacción prohibida:** "commuting definitely sacrifices sleep the most" o cualquier variante causal o de ranking definitivo.

**Direcciones abiertas que dejó EXP-001** (candidatas, **no** EXP-002 predeterminado): ¿la relación es no lineal? ¿difiere por sexo? El sistema debe evaluarlas junto con cualquier otro candidato justificado, como un experimento de validación o la separación de participación y duración en ocio, y elegir el de mayor aprendizaje esperado.

## 8. Ciclo de descubrimiento, hipótesis y reglas

```
pregunta → evidencia (RAG, con citas) → hipótesis → pruebas candidatas (≥2) → Experiment Planner
        → orquestación Omnigent → ExperimentSpec → motor determinista → ExperimentResult
        → Scientific Critic → estado científico actualizado → siguiente experimento (vuelve al ciclo)
```

**No hay secuencia fija** EXP-001 → EXP-002 → EXP-003. El motor produce evidencia; los agentes la interpretan y deciden. Protocolo completo en [`docs/EXPERIMENT_PROTOCOL.md`](docs/EXPERIMENT_PROTOCOL.md).

### Hipótesis iniciales

| ID | Hipótesis | ¿Cabe en el motor? |
|---|---|---|
| H1 — Desplazamiento de tiempo | Más traslado se asocia con menos tiempo en al menos una dimensión personal | Sí (evaluada en EXP-001) |
| H2 — Desplazamiento desigual | La magnitud difiere entre las 4 dimensiones; el sistema determina cuál es la más negativa | Sí (evaluada en EXP-001) |
| H3 — Heterogeneidad por sexo | La relación difiere entre hombres y mujeres (interacción u otra comparación justificada) | Solo por estimación separada; la comparación formal requiere revisar el contrato |
| H4 — Restricción del hogar | La relación difiere según haya menores en el hogar | Requiere revisar el contrato |

Las hipótesis generadas por agentes se etiquetan (`hypotheses.generated_by`) y separan tres cosas: evidencia existente, inferencia e hipótesis nueva.

### Reglas de decisión pre-registradas

Se guardan en `projects.decision_rules` al crear el proyecto, **antes** de ver resultados. Son guías del crítico y del Director, no una secuencia fija:

- **R1:** hay diferencia por sexo suficientemente sustentada y los subgrupos tienen tamaño adecuado → probar composición del hogar o presencia de menores.
- **R2:** no aparece diferencia por sexo → sensibilidad a traslados largos o relación no lineal.
- **R3:** la calidad o el tamaño de muestra impiden concluir, o el run falló → revisar variables, cohorte y medición.

`docs/EXPERIMENT_PROTOCOL.md` ("Branching Rules") detalla otras ramas: la interacción por sexo que se debilita con controles del hogar lleva a traslado × hogar con menores; la evidencia de no linealidad lleva a categorías, splines o cuantiles; la caída de una actividad lleva a un análisis de dos partes (participación vs duración); y un resultado nulo no termina la investigación, sino que lleva a revisar potencia, medición y especificación.

### Crítica y selección

- **Scientific Critic:** evalúa tamaño de muestra y subgrupos, faltantes, supuestos, diseño muestral, robustez, incertidumbre, explicaciones alternativas, lenguaje causal, comparaciones múltiples y afirmaciones no sustentadas. Veredicto: `VALID` · `UNCERTAIN` · `REQUIRES_REVISION` · `REQUIRES_HUMAN_REVIEW`. Un resultado `REQUIRES_REVISION` no cuenta como evidencia establecida.
- **Experiment Planner:** ≥2 candidatos cuando sea factible, cada uno con pregunta, hipótesis, ganancia de información esperada, variables, factibilidad dentro del contrato, costo, limitaciones y por qué podría cambiar la interpretación.
- **Discovery Director:** elige por **aprendizaje esperado, nunca por probabilidad de significancia**, y deja la decisión registrada y trazable a la evidencia. Si la evidencia es insuficiente, la acción correcta puede ser un experimento de validación, no una conclusión más fuerte.
- **Aprobación humana** obligatoria cuando cambia la población o la definición de un outcome, cuando la interpretación de datos crudos es ambigua, cuando se propone una afirmación causal, cuando se excluyen observaciones con una regla nueva, cuando cambia la metodología de encuesta, cuando un experimento contradice un contrato o cuando el crítico la pide. En Omnigent, la política ASK la exige antes de `run_experiment` y de `record_decision`.

## 9. Arquitectura de agentes (Omnigent)

### 9.1 Ejecución

- **Omnigent 0.16 de código abierto**, spec en `omnigent.yaml`, validado con `omnigent.spec.load`.
- **Executor actual** (commit `84207bb`): `harness: codex`, `model: gpt-5.4-mini`, con la llave `OPENAI_API_KEY` de una service account del equipo. Reemplaza a `databricks-claude-sonnet-4-6` con auth Databricks. Omnigent no lee `.env`: hay que cargarla antes (`set -a; source .env; set +a`). El ancla `&executor` aplica a los 7 agentes.
- Comando: `PYTHONPATH=agents:analysis omnigent run omnigent.yaml -p "$(cat initial_state.json)"`. Las tools necesitan `agents/` y `analysis/` en el path.
- Políticas: `approve_runs_and_decisions` (ASK antes de `run_experiment` y `record_decision`) y un tope de 150 llamadas a tools por sesión.

### 9.2 Los 7 agentes

El Discovery Director es la raíz. Los otros 6 son sub-agentes (`type: agent`) que heredan solo sus tools. Cada uno es dueño de **una decisión científica**:

| Agente | Decisión | Tools (`agents/commute_lab/tools.py`) | Persiste en |
|---|---|---|---|
| Literature Agent | qué evidencia previa existe | `search_evidence`, `search_openalex` | `sources`, `passages` |
| Hypothesis Agent | qué explicación falsable probar | `save_hypothesis` | `hypotheses` |
| Data Steward | si los datos permiten probarla | `describe_dataset`, `search_evidence` | estado JSON (`variables`, `population`, `limitations`) |
| Experiment Planner | qué prueba maximiza el aprendizaje | `save_proposals` (≥2) | `experiment_proposals` |
| Experiment Runner | ejecutar de forma reproducible | `run_experiment` (ASK), `read_run` | `experiment_runs` |
| Scientific Critic | si la interpretación es confiable | `read_run`, `record_decision` (ASK) | `decisions`, estado de `hypotheses` |
| Discovery Director | qué investigar después | `create_project`, `set_project_status`, `log_event` + los 6 sub-agentes | `projects`, `agent_events` |

Todas las tools escriben una fila en `agent_events`, que la web muestra como línea de tiempo. Flujo, con una sola vuelta extra (máximo 2 experimentos por sesión):

```
Director → literature_agent → hypothesis_agent → data_steward → experiment_planner
        → experiment_runner → scientific_critic → Director (next_decision)
        └─(si aplica, una vez)→ experiment_planner → experiment_runner → scientific_critic → Director
```

### 9.3 Shared Research State

Los agentes **no** conversan en texto libre. Reciben, modifican y devuelven **un único objeto JSON**. La regla vive en los prompts, porque Omnigent no tiene una política que fuerce JSON. El JSON es el contrato de mensajes durante la sesión; Supabase es el registro persistente que lee la web.

- **Esquema actual** (`initial_state.json`): `project_id`, `research_question`, `population`, `hypotheses`, `evidence`, `variables`, `experiments`, `results`, `limitations`, `next_decision`.
- **Esquema objetivo** (fase actual, con IDs estables para hipótesis, experimentos, críticas, candidatos y decisiones): `project_id`, `research_question`, `dataset_version`, `population`, `evidence`, `hypotheses`, `experiments`, `experiment_results`, `scientific_critiques`, `limitations`, `candidate_experiments`, `decisions`, `next_action`.
- Cada tarjeta de evidencia lleva `claim`, `stance`, `source_id`, `passage_id` o `doi`, `url`, `locator` y `quote`. `next_decision` lleva `rule_applied` y el `run_id` real.

### 9.4 Brecha entre lo implementado y el objetivo

Los prompts, `initial_state.json` y tres tools son anteriores al motor:

- `run_experiment` todavía busca `analysis/enut/protocols.py` (`weighted_means_by_group`, `wls_commute_by_sex`), que **nunca se implementó y queda reemplazado por el motor**. Hoy siempre termina en `failed`. Hay que reescribirla para que reciba un `ExperimentSpec`, llame a `src.experiments.runner.run_experiment` y persista el resultado y su procedencia en `experiment_runs`.
- `save_proposals` valida contra esa misma lista vieja de protocolos (también en el `enum` de `omnigent.yaml`).
- `describe_dataset` debe exponer `docs/DATA_CONTRACT.md`, el manifiesto y los valores que acepta el esquema. **Nunca devuelve filas.**
- Los prompts siguen describiendo la pregunta vieja (60 minutos semanales, cuidados, protocolos cerrados).
- El entorno de Omnigent necesita pandas, pyarrow, numpy, scipy y pydantic para llamar al motor.

## 10. Persistencia: Supabase

Proyecto `xnbruiprrxradfidoleu` (us-east-1, Postgres 17, pgvector). La cuenta tiene otro proyecto, "Finding out" (`fnveucrdccqwzovptxqa`), que **no** es del hackathon.

| Tabla | Propósito |
|---|---|
| `projects` | caso de investigación: `question`, `cohort_definition`, `decision_rules`, `status`, `omnigent_session_url`, `is_demo` |
| `sources` / `passages` | documentos citables y fragmentos RAG (`embedding vector(384)`, `fts` en español) |
| `hypotheses` | `statement`, `generated_by`, `status`, pasajes a favor y en contra |
| `experiment_proposals` | candidatos A/B con `protocol`, `learning_value`, `feasibility`, `cost`, `selected`, `selection_rationale` |
| `experiment_runs` | `dataset_hash`, `code_version`, `parameters`, `sample_sizes`, `results`, `artifact_paths`, `status` |
| `decisions` | `interpretation`, `uncertainty`, `limitations`, `rule_applied`, `next_test`, `rationale` |
| `agent_events` | línea de tiempo y auditoría |

- **RLS** activo en todas las tablas: `anon`/`authenticated` solo SELECT; solo `service_role` escribe. **Nunca filas individuales de microdatos en Supabase**, solo agregados y procedencia.
- Migraciones aplicadas: `20261003210503_extensions`, `20261003210519_core`, `20261003210530_rag`, `20261003210538_rls`, `20261003221539_rag_spanish_fts`. Nunca editar una ya aplicada.
- **Contenido real al 2026-10-03:** solo el seed demo (1 proyecto `is_demo`, 1 hipótesis, 2 propuestas, 1 run `pending`, 0 decisiones, 4 eventos) más el corpus RAG (5 fuentes: 3 INEGI + 2 demo; 535 pasajes con embedding; 0 papers de OpenAlex). **Todavía no hay ningún resultado real persistido.**
- El contrato de `experiment_runs.results` que dibuja la web (`web/lib/types.ts`) es anterior al `ExperimentResult` del motor. Falta decidir cómo se guarda (§17).

## 11. RAG

- Embeddings `intfloat/multilingual-e5-small` (384 dims, CPU), prefijos `passage: ` / `query: `, el mismo modelo en ingesta y consulta.
- `public.hybrid_search`: texto completo (`public.es_unaccent`, coincidencias parciales ordenadas por nº de términos) + coseno HNSW, combinados con Reciprocal Rank Fusion. Entrada en Python: `rag.search.search_evidence(query, k=5)`. Consultar en español; los términos en inglés se expanden con un glosario fijo.
- Corpus: cuestionario ENUT 2024 (88 pasajes, uno por pregunta), diseño conceptual (402) y diseño muestral (45), sin portadas, índices, anexos duplicados ni referencias. La limpieza conserva "PASE A" y "FILTRO" porque explican faltantes estructurales. Los papers de OpenAlex se registran como `sources` (`kind = 'paper'`, metadatos y resumen, sin pasajes).
- QA (`uv run python -m rag.eval`, 15 consultas): hit@1 0.80, hit@5 0.93, MRR 0.86, 0 % de ruido de formulario en el top 5.
- El RAG fundamenta conceptos, literatura y decisiones de método. **Nunca produce cifras de resultados.**

## 12. Web

- Next.js 16 App Router + TypeScript + Tailwind 4 en `web/`. Desplegada en Vercel: **https://commute-time-lab.vercel.app** (pública).
- `/`: portada y lista de casos. `/research/[id]`: panel del ciclo (pregunta, cohorte, línea de tiempo, fuentes, hipótesis, propuestas, resultados con gráfico, decisión), refrescado cada 5 s.
- Solo lectura con la clave publishable bajo RLS. La clave `service_role` nunca llega al navegador. Omnigent nunca se llama desde el navegador con credenciales. Un botón "Start research" (Route Handler → API de Omnigent) se agrega **solo después** de que el ciclo funcione.
- Hoy muestra el proyecto demo (`/research/00000000-0000-0000-0000-000000000001`).

## 13. Estado actual verificado (2026-10-03)

| Frente | Estado |
|---|---|
| Supabase (migraciones, RLS, seed demo) | ✅ |
| RAG (535 pasajes, FTS en español, eval medido) | ✅ |
| Web leyendo Supabase y desplegada | ✅ (contrato de resultados viejo) |
| `analytic_v1` en el repo, SHA256 verificado, aprobación registrada | ✅ |
| Motor `src/experiments/` + scripts + `report.py` | ✅ **16 tests pasan** en este repo (Python 3.12, versiones fijadas + pandas/pyarrow) con `python -m unittest discover -s tests` |
| EXP-001 | ✅ completado; pendiente de revisión humana |
| `omnigent.yaml` (formato válido, executor codex) | 🟡 prompts, `enum` de protocolos e `initial_state.json` desfasados |
| Tools `run_experiment`, `save_proposals`, `describe_dataset` | 🟡 desfasadas (§9.4) |
| Capa agéntica (crítico, candidatos, decisión, EXP-002) | ⏳ nada implementado |
| Primera sesión real de Omnigent | ⏳ |
| Medición manual vs asistido | ⏳ |
| Demo de 2 minutos | ⏳ |

**Fricciones encontradas al verificar:**

1. El comando de tests de `AGENTS.md` §10 (`python -m unittest discover -s tests -t .`) **falla** con `Start directory is not importable`, porque `tests/` no tiene `__init__.py`. Funciona sin `-t .`.
2. `requirements-experiments.txt` empieza con `-r requirements.txt`, y ese archivo **no está en el repo**. `pip install -r requirements-experiments.txt` falla. Mientras tanto, instalar a mano pandas, pyarrow y las versiones fijadas (numpy 2.3.5, pydantic 2.13.5, scipy 1.16.3, statsmodels 0.14.6, patsy 1.0.2).
3. `scripts/validate_experiment_engine.py` hashea `data/interim/staging_v1.parquet` y `data/raw/enut_2024/*.csv`, que no están en el repo. Solo corre en el entorno del pipeline. `engine_validation.json` registra esa ejecución (PASS).
4. `metadata/provenance.json` está vacío (0 bytes) y `audit/` es una copia idéntica de `reports/audit/`.

**Desfases en otros documentos** (ningún cambio aplicado; conviene alinearlos):

- `AGENTS.md` y `MEMORY.md` todavía dicen que faltan `analytic_v1.parquet`, el registro de aprobación, `report.py`, los scripts y `requirements-experiments.txt`. Ya están (commit `04df096`).
- Ambos siguen describiendo el modelo `databricks-claude-sonnet-4-6` con perfil Databricks. El executor es `codex` / `gpt-5.4-mini`.
- Ambos y `analysis/enut/README.md` ubican `staging_v1.parquet` en `data/processed/`. Se quitó del repo en `04df096`.
- `agents/README.md` dice 10 tools; son 11 (falta `describe_dataset`).

## 14. Roadmap y próximos pasos

| Horas | Trabajo | Condición de salida | Estado |
|---|---|---|---|
| 0–1 | `AGENTS.md`, esqueleto, Supabase, preflight de Omnigent | acceso real a BD + orquestador | ✅ BD · 🟡 orquestador sin sesión real |
| 1–3 | migraciones, RLS, seed, ingesta + búsqueda RAG | `hybrid_search` devuelve pasajes con cita | ✅ |
| 3–4.5 | panel Next.js | la web muestra estado real de la BD | ✅ |
| 4.5–6.5 | pipeline → `analytic_v1` → motor → EXP-001; conectar motor a `run_experiment` | resultado real persistido | ✅ motor y EXP-001 · ⏳ persistencia |
| 6.5–8 | **capa agéntica**: crítico sobre EXP-001 → hipótesis → candidatos → elección → nuevo `ExperimentSpec` → motor → crítica → decisión | decisión dependiente del resultado guardada | ⏳ **fase actual** |
| 8–9 | panel con el ciclo completo; reejecutar; cronometrar | reproducción y medición honestas | ⏳ |
| 9–10 | Vercel, README, demo de 2 min | entrega completa | ⏳ |

**Siguientes pasos, en orden:**

1. Reescribir `run_experiment`, `save_proposals` y `describe_dataset` contra el motor (§9.4) y persistir un resultado real de EXP-001 en `experiment_runs`.
2. Decidir cómo se guardan `ExperimentResult`, `ScientificCritique` y los candidatos en Supabase, y adaptar `web/lib/types.ts`.
3. Implementar la capa agéntica: Shared Research State objetivo, prompts de crítico, Hypothesis Agent, Planner y Director con la pregunta, unidades y outcomes vigentes. Validar `omnigent.yaml` con `omnigent.spec.load` y comprobar que ningún `FunctionTool.callable` sea `None`.
4. Primera sesión real de Omnigent con la llave cargada, arrancando desde `reports/experiments/EXP-001/result.json`. Comprobar que el ASK salta cuando un sub-agente llama a `run_experiment` o `record_decision`.
5. Que el sistema elija y ejecute EXP-002, lo critique y registre la siguiente decisión.
6. Panel con el ciclo completo; reproducir; cronometrar manual vs asistido.
7. Arreglar las fricciones del §13 y alinear `AGENTS.md`, `MEMORY.md` y los READMEs.
8. Redesplegar la web, README final y grabar el demo.

**Regla de alcance:** si el ciclo científico (ejecución real + decisión dependiente) no funciona a la hora 6, se detiene todo el trabajo de UI y el equipo entero pasa a Omnigent + experimento + decisión. La web puede ser una sola página.

## 15. Medición y demo

- **Cuello de botella medido:** el tiempo desde una pregunta hasta una prueba reproducible y una siguiente decisión con evidencia.
- Cronometrar un intento manual breve y el flujo asistido **con el mismo corpus y dataset**. Reportar duración, intervención humana y límites de comparabilidad. No declarar 10× ni ningún factor sin medirlo.
- Revisar a mano al menos 10 afirmaciones factuales del panel contra sus fuentes, y correr `rag.eval` antes y después de cambiar la ingesta o la búsqueda.
- **Demo (2 min, en inglés):** problema y pregunta (15 s) → agentes y fuentes (25 s) → dos pruebas y la elección (20 s) → ejecución y resultado real (35 s) → decisión actualizada y limitaciones (25 s).

## 16. Definición de terminado

1. Una URL pública explica la pregunta, la población, las fuentes y el estado de la investigación.
2. Una sesión de Omnigent muestra ≥3 roles efectivos, llamadas a herramientas y traspasos.
3. Se ven las dos pruebas propuestas, la elegida y por qué se eligió.
4. El código estadístico se reejecuta sobre `analytic_v1` y reproduce el resultado (el motor exige resultados idénticos).
5. Las cifras muestran unidades (minutos de lunes a viernes por +300 min de traslado), `n`, método, incertidumbre con su limitación de diseño y enlaces de procedencia.
6. Se ve una decisión nueva derivada del resultado, con la regla aplicada y la siguiente prueba.
7. El repo contiene migraciones, configuraciones y políticas de agentes, instrucciones de ejecución, código, resultados y la medición de aceleración.

## 17. Decisiones

### Tomadas (resumen; registro completo en [`AGENTS.md`](AGENTS.md#registro-de-decisiones))

| Fecha | Decisión |
|---|---|
| 2026-10-03 | Stack: Next.js 16 + Supabase (pgvector, RLS) + Python; web de solo lectura que consulta cada 5 s |
| 2026-10-03 | Arquitectura de 7 agentes + Shared Research State (JSON entre agentes, Supabase como persistencia) |
| 2026-10-03 | Aprobación humana (ASK) antes de `run_experiment` y `record_decision`; máximo 2 experimentos por sesión |
| 2026-10-03 | Embeddings e5-small en Python; FTS en español (`es_unaccent`) con coincidencias parciales; cuestionario como fuente propia, un pasaje por pregunta |
| 2026-10-03 | Año ENUT 2024; pregunta con `commute_5h` y 4 outcomes en minutos de lunes a viernes; población 18–65; cuidados fuera |
| 2026-10-03 | `analytic_v1` versionado en git (deriva de microdatos públicos); el ZIP bruto fuera de git; Supabase sin filas individuales |
| 2026-10-03 | El motor determinista es el único camino computacional; reemplaza los protocolos cerrados `weighted_means_by_group` y `wls_commute_by_sex` |
| 2026-10-03 | EXP-001 completado con `INCONCLUSIVE_RANKING`; EXP-002 lo elige el sistema por aprendizaje esperado, sin secuencia fija |
| 2026-10-03 | Executor de Omnigent: `codex` + `gpt-5.4-mini` con `OPENAI_API_KEY` (commit `84207bb`), en lugar de Claude en Databricks |

### Abiertas

1. **Modelo.** Confirmar que la llave tiene acceso a `gpt-5.4-mini` y que el harness `codex` de Omnigent maneja bien las function tools y las políticas ASK.
2. **Políticas en sub-agentes.** Comprobar en la primera sesión que el ASK salta cuando el runner o el crítico llaman a la tool. Si no, mover esas llamadas al Director.
3. **`ExperimentResult` en Supabase.** ¿Resultado completo en `experiment_runs.results`, o resumen + `artifact_paths` hacia `reports/experiments/<id>/`? ¿Bastan `decisions` y `experiment_proposals` para la crítica y los candidatos, o hace falta una migración?
4. **Revisión humana de EXP-001.** ¿El ciclo puede usarlo como evidencia provisional antes de esa revisión, o la revisión es un paso del ciclo?
5. **Ampliación del contrato.** Si el sistema elige interacciones, no linealidad, dos partes o H3/H4, hay que revisar el contrato del motor con aprobación humana.
6. **Entorno reproducible.** Agregar o quitar `requirements.txt`, decidir el comando de tests y qué hacer con `provenance.json` vacío y el duplicado `audit/`.
7. **Seguridad.** Decidir si se quita `EXECUTE` a `anon`/`authenticated` sobre `public.rls_auto_enable()`, que ya existía en el proyecto.
8. **Datos demo.** Crear un proyecto real nuevo o limpiar el seed demo cuando exista el ciclo real; nunca mezclar resultados reales con filas demo.
