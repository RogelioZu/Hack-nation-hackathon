# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primarios (desde 2026-10-04): investigadores** que leen la corrida a su ritmo: necesitan ver de un vistazo en qué estado está cada hipótesis y experimento, saltar a cualquier etapa, entender cada código de estado sin glosario y llegar al archivo fuente de cada cifra. Por eso la portada abre con el resumen "Where the investigation stands" y una barra de secciones; el replay cronometrado es secundario (botón "Walkthrough").
- **Jueces del Hack-Nation 7th Global AI Hackathon (Challenge 03, Databricks · Agentic Scientific Discovery)** viendo el demo de 2 minutos, proyectado o grabado. Lo ven de lejos, una sola vez y con narración; la pantalla tiene que avanzar por etapas y leerse sin acercarse.
- Secundarios: quien abre la URL pública (`https://commute-time-lab.vercel.app`) después del demo, sin narrador, y el equipo que sigue una sesión de Omnigent mientras corre.

## Product Purpose

tiemPO (antes Time Poverty Lab; repo: Commute & Time Lab) es un laboratorio científico agéntico. Omnigent orquesta agentes especialistas que investigan, con microdatos reales de la ENUT 2024 (INEGI), qué dimensión del tiempo personal muestra la asociación negativa más fuerte con 5 horas adicionales de traslado laboral entre semana, entre trabajadores de 18 a 65 años de CDMX y Edomex.

La interfaz tiene que comunicar una idea: los agentes no se limitan a responder una pregunta. Examinan la evidencia, identifican la incertidumbre, deciden qué vale la pena investigar después, corren un experimento reproducible y actualizan la decisión científica.

Éxito: un juez entiende en 2 minutos el ciclo pregunta → evidencia → crítica → hipótesis → candidatos → experimento elegido → nueva evidencia → decisión actualizada, y ve que cada tarjeta viene de un artefacto real con ID.

## Positioning

Las cifras salen solo de un motor determinista (`src/experiments/`) que corre cada spec dos veces y verifica el hash del dataset; los agentes LLM interpretan y deciden, nunca calculan. Cada paso del ciclo deja un artefacto JSON con ID estable (EXP-001, CRIT-EXP-001-001, HYP-…) y la interfaz los lee, no los vuelve a escribir. La incertidumbre se muestra como resultado, no se esconde.

## Operating Context

- La cadena completa ya existe en el repo y su índice es `reports/discovery/local/research_state.json` (IDs, relaciones y hashes, sin cifras):
  - EXP-001 y CRIT-EXP-001-001;
  - hipótesis HYP-005/007/008, aprobadas en REV-001;
  - propuestas PROP-003/005/008/009;
  - decisiones DEC-001 (esperando capacidad del motor) a DEC-005 (`READY_TO_EXECUTE`);
  - aprobación humana REV-DEC-005-001;
  - EXP-002 (interacción traslado × sexo) y CRIT-EXP-002-002.
- La UI lee todo a través de un adaptador (`web/lib/discovery/model.ts` → `DiscoveryRunViewModel`). Ningún componente lleva cifras, estados ni IDs escritos.
- Dos modos de la misma interfaz, con el mismo view model:
  - **REPLAY**: bundle `web/data/discovery-run.json`, generado en cada build a partir de los artefactos commiteados. Funciona sin agentes ni Databricks, y en Vercel.
  - **LIVE**: el servidor local lee los archivos del repo mientras Omnigent escribe. En Vercel no hay LIVE.
- La portada es la línea de tiempo de descubrimiento. El panel de Supabase (`/research/[id]`) se conserva como vista de auditoría enlazada.
- Next.js 16 App Router + Tailwind 4 en `web/`, desplegado en Vercel subiendo solo `web/`.

## Capabilities and Constraints

- Sin resultados inventados. EXP-002 no se codifica: lo elige el sistema. Etapas sin artefacto se muestran como pendientes, nunca con contenido de relleno.
- No modificar artefactos científicos ni el motor de experimentos.
- Lenguaje científico seguro: asociación observacional, nunca causal; ranking `INCONCLUSIVE` se dice tal cual. Unidades: minutos totales de lunes a viernes por +300 min de traslado entre semana.
- La varianza CR1 por UPM es una aproximación, no la varianza completa de encuesta compleja de ENUT; esa limitación acompaña a toda cifra.
- Distinción visual obligatoria entre EVIDENCE, HYPOTHESIS, EXPERIMENT, UNCERTAINTY y DECISION. No es un chat.
- UI, demo y textos guardados en inglés; documentación en español.

## Brand Commitments

- Nombre del producto en la web y en el demo: **tiemPO**, con esa capitalización exacta (decisión del usuario, 2026-10-03). Wordmark en Montserrat Black (900), elegido en live mode; el resto de la interfaz sigue en Inter. Los prompts de los agentes en `omnigent.yaml` siguen diciendo "Time Poverty Lab".
- Sistema visual vinculante: `web/education2025-design-system.md` (azul eléctrico `#0055FF` sólido, sin degradados; canvas gris, tarjetas blancas planas, Inter, radios jerárquicos, sidebar azul). Lo eligió el usuario para este rediseño.
- El usuario pidió un aspecto menos saturado y con menos "AI slop" en botones y espacios: el azul sólido queda en la barra lateral, el botón Play y la evidencia; el resto es superficie blanca, texto y líneas finas.

## Evidence on Hand

- EXP-001 (n = 2,563): sueño −48.711 min [−63.481, −33.940]; ocio −20.396; conversación en el hogar −3.816; higiene +3.094 (min de lunes a viernes por +300 min de traslado, modelo ajustado). Ranking `INCONCLUSIVE_RANKING`. Revisión `REQUIRES_HUMAN_REVIEW`.
- CRIT-EXP-001-001: veredicto `UNCERTAIN`, generado por `databricks-gpt-oss-120b` vía Omnigent.
- EXP-002 (sueño, interacción traslado × sexo, n = 2,563):
  - pendiente de hombres −41.596 [−59.099, −24.094];
  - pendiente de mujeres −59.312 [−83.836, −34.788];
  - **interacción −17.715 [−47.532, 12.101]**, `INCONCLUSIVE_INTERVAL_INCLUDES_ZERO`;
  - ranking `NOT_APPLICABLE_SINGLE_OUTCOME`.
- CRIT-EXP-002-002 (`UNCERTAIN`): **H3 pasa de `UNTESTED` a `INCONCLUSIVE`**. Es el momento estrella del demo: el laboratorio actualiza su estado sin inventar certeza.
- Cifras de referencia para revisar; la UI las lee de los artefactos.
- Aún no existe la medición de aceleración (el 10× es una meta).

## Product Principles

1. **El artefacto manda.** Toda tarjeta se rastrea a un archivo con ID; la UI nunca reescribe valores.
2. **La incertidumbre es un resultado.** Se muestra con el mismo peso que la evidencia.
3. **El vacío es honesto.** Lo que no existe aparece como pendiente, con el nombre del artefacto que lo llenará.
4. **Flujo científico, no conversación.** Etapas, traspasos y decisiones; nada de burbujas de chat.
5. **Legible a distancia.** Pensado para proyectarse y narrarse en 2 minutos.
