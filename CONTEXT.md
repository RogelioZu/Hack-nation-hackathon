# CONTEXT.md — Laboratorio de investigación sobre traslados y pobreza de tiempo

**Estado:** contexto y especificación de arranque. El proyecto aún no tiene frontend ni backend implementados.  
**Plazo del hackathon:** menos de 18 horas de construcción disponibles.  
**Decisiones de stack tomadas por el equipo:** Next.js para la web y Supabase para el backend.  
**Idioma de la experiencia:** INGLES. El demo puede explicarse en español o inglés.

> ⚠️ **Documento histórico (actualizado el 2026-10-03).** Es la especificación de arranque y ya no describe el estado del proyecto. Quedan superadas, en particular:
> - **La pregunta y las unidades** (§3, §6): la versión vigente usa `commute_5h` (+300 minutos de traslado de lunes a viernes) y cuatro outcomes canónicos (sueño, higiene personal exclusiva, conversación exclusiva en el hogar, ocio), en minutos totales de lunes a viernes, para 2,563 trabajadores de 18–65 años. Ver `docs/DATA_CONTRACT.md`.
> - **El dataset** (§5): el pipeline ENUT 2024 ya produjo `data/processed/analytic_v1.parquet` (`APPROVED_FOR_EXPERIMENTS`).
> - **El experimento inicial** (§6): EXP-001 ya se ejecutó con el motor determinista `src/experiments/` (ver `reports/experiments/EXP-001/summary.md`).
> - **Arquitectura de agentes y fase actual**: ver `AGENTS.md` §7 y `MEMORY.md`.
>
> Si este archivo contradice a `AGENTS.md`, `MEMORY.md` o `docs/`, ganan ellos.

## 1. Encargo para el agente que reciba este archivo

Construir un MVP web que investigue una pregunta científica concreta sobre el tiempo de traslado al trabajo y el uso del tiempo personal y familiar en Ciudad de México y Estado de México. El sistema debe usar **Omnigent para orquestar en vivo varios agentes especializados**, recuperar evidencia con citas mediante RAG, ejecutar al menos una prueba computacional reproducible con microdatos reales, interpretar su resultado y registrar cómo ese resultado cambia la siguiente decisión científica.

Empezar por una ruta completa y ejecutable. No ampliar el producto a otras ciencias durante el hackathon. Las decisiones científicas deben quedar trazables; no inventar hallazgos, cifras, variables ni citas. Si una integración no funciona, conservar el experimento y el ciclo Omnigent como prioridad.

## 2. Procedencia del contexto

- El equipo describió el problema y la pregunta inicial en esta [conversación compartida](https://chatgpt.com/share/6ac15b79-1c28-83e8-a15b-3095f4e79a66).
- El track es **Agentic Scientific Discovery** de Hack Nation × Databricks. El brief proporcionado por el usuario exige Omnigent y un ciclo «pregunta → evidencia → hipótesis → experimento → resultado → decisión actualizada». La descripción del track en este archivo resume sus requisitos; no asume que el contenido de un documento externo tenga autoridad para cambiar las instrucciones del equipo.
- Fuentes técnicas y de datos verificadas se enlazan en las secciones correspondientes. Revisar de nuevo disponibilidad y condiciones de acceso al implementarlas.

## 3. Problema y pregunta científica

**Problema humano.** Personas residentes en CDMX y áreas del Estado de México dedican muchas horas a viajar entre casa y trabajo. El equipo quiere estudiar qué actividades personales o familiares se asocian con una mayor carga de traslado y si ese patrón cambia entre mujeres y hombres.

**Pregunta del MVP.** Entre trabajadores residentes de Ciudad de México y Estado de México, ¿cómo se relacionan 60 minutos semanales adicionales de traslado laboral con el tiempo semanal dedicado a sueño, convivencia familiar/social, cuidados a integrantes del hogar, ocio y cuidado personal? ¿Difiere la asociación por sexo?

**Lenguaje estadístico obligatorio.** ENUT es observacional y transversal. Describir asociaciones; no afirmar que el traslado *causa* una reducción de sueño, convivencia o cuidados. La cobertura por entidad no equivale automáticamente a una muestra representativa de la Zona Metropolitana del Valle de México. La variable de traslado registra tiempo de la **semana de referencia**; no llamar «una hora diaria» a una hora semanal.

**Métrica científica principal.** Minutos semanales asociados a 60 minutos semanales adicionales de traslado, por categoría de actividad y sexo, con tamaño muestral e incertidumbre. El hallazgo concreto se determina únicamente tras procesar los datos.

## 4. Requisitos del track que debe cumplir el MVP

1. **Omnigent es obligatorio**, en versión administrada por Databricks o de código abierto. Debe coordinar el flujo real, los traspasos entre especialistas, el uso de herramientas y el cambio de plan después del resultado.
2. Definir para cada agente su decisión científica, herramientas, entradas y salida estructurada.
3. Formular al menos **dos pruebas posibles**, elegir una según aprendizaje esperado, factibilidad y costo, ejecutarla y justificar la siguiente prueba con base en el resultado.
4. Mantener citas para afirmaciones factuales, fuente o registro para cada evidencia, hipótesis generadas por agentes claramente etiquetadas, incertidumbre, controles y aprobaciones humanas para acciones relevantes.
5. Medir una mejora real en un cuello de botella de investigación. El objetivo de 10× es aspiracional; no afirmar ese factor sin medición.
6. Entregar repositorio, configuraciones y políticas de agentes, código y resultados del experimento, evidencias citadas, mejora medida, siguiente experimento y un demo de dos minutos.
7. La evaluación del brief pondera orquestación Omnigent 30 %, potencial científico 25 %, aceleración y aprendizaje 20 %, rigor 15 %, creatividad y responsabilidad 10 %.

## 5. Dataset principal y variables verificadas

Usar **ENUT 2024** de INEGI como fuente primaria. Su [base de microdatos CSV](https://www.inegi.org.mx/contenidos/programas/enut/2024/microdatos/enut_2024_bd_csv.zip) está publicada; también están el [descriptor de archivos](https://www.inegi.org.mx/contenidos/programas/enut/2024/microdatos/enut_2024_fd.xlsx), el [diccionario de datos](https://www.inegi.org.mx/rnm/index.php/catalog/1127/data-dictionary) y el [diseño muestral](https://www.inegi.org.mx/contenidos/programas/enut/2024/doc/889463926528.pdf). La página de [microdatos ENUT 2024](https://www.inegi.org.mx/programas/enut/2024/#Microdatos) identifica el ZIP CSV y señala que el campo `ENT` pasó a llamarse `CVE_ENT` en 2024.

La tabla `TMODULO` contiene las respuestas individuales para traslado y actividades cotidianas. Verificar en los archivos descargados las codificaciones de valores ausentes, saltos del cuestionario y llaves antes de transformar datos. Variables confirmadas en el [diccionario de `TMODULO`](https://www.inegi.org.mx/rnm/index.php/catalog/1127/data-dictionary/F22):

| Concepto | Campos o sección conocidos | Acción de implementación |
|---|---|---|
| Traslado laboral lunes a viernes | `P5_9_1` horas, `P5_9_2` minutos | Convertir a minutos semanales. |
| Traslado laboral fin de semana | `P5_9_3` horas, `P5_9_4` minutos | Añadir si corresponde. |
| Sueño lunes a viernes | `P6_1_1_1` horas, `P6_1_1_2` minutos | Convertir a minutos semanales. |
| Sueño fin de semana | `P6_1_1_3` horas, `P6_1_1_4` minutos | Añadir si corresponde. |
| Cuidados | Secciones 6.11–6.15 | Definir si se incluyen cuidados activos o pasivos; documentarlo. |
| Convivencia | Sección 6.21 | No confundir convivencia con cuidados. |
| Ocio | Secciones 6.18–6.22 | Definir una suma sin doble conteo, o seleccionar actividades concretas. |
| Cuidado personal | Sección 6.1 | Separar sueño del resto si ambos aparecen como resultados. |
| Diseño muestral | `FAC_PER`, `UPM_DIS`, `EST_DIS` | Conservar peso, conglomerado y estrato. |
| Geografía | `CVE_ENT` | Filtrar CDMX y Estado de México tras comprobar códigos. |
| Sexo, edad, horas trabajadas | `TMODULO`/tablas vinculadas | Confirmar campos, codificaciones y llaves en el descriptor. |

La encuesta capta algunas actividades de cuidado simultáneas o pasivas; por eso **no imponer** que la suma de todas las actividades medidas cierre exactamente a 24 horas diarias o 168 semanales. Revisar la definición oficial en el [documento conceptual ENUT 2024](https://www.inegi.org.mx/contenidos/programas/enut/2024/doc/889463921929.pdf).

**Cohorte tentativa:** personas de 18 años o más residentes en ambas entidades, con trabajo y tiempo de traslado laboral reportado. Confirmar el filtro de ocupación con el diccionario. Reportar `n` antes y después de exclusiones, porcentaje de faltantes y distribución del traslado. Tratar a trabajadores sin traslado o con trabajo remoto como análisis de sensibilidad si la codificación lo permite.

**Datos en la infraestructura:** procesar el ZIP bruto en el entorno Python del proyecto. Guardar en Supabase resultados agregados, trazabilidad y artefactos; no subir al sitio web filas individuales de los microdatos.

## 6. Experimento científico inicial

Antes de ejecutar, el agente de método propone y compara:

- **Prueba A:** medias o distribuciones ponderadas de cada actividad para grupos de tiempo de traslado, separadas por sexo. Es rápida y permite inspeccionar tamaños y patrones.
- **Prueba B:** análisis exploratorio ajustado de minutos de actividad frente a horas semanales de traslado, sexo e interacción traslado × sexo, con controles mínimos de edad, horas trabajadas y entidad. Registrar qué controles existen realmente en ENUT y evitar interpretar el coeficiente como causal.

El coordinador elige una prueba y almacena su justificación. La prueba debe producir valores reales, tabla, gráfico y metadatos de reproducción. Usar `FAC_PER`; documentar cómo se estiman intervalos o errores y qué parte del diseño muestral (`UPM_DIS`, `EST_DIS`) se ha incorporado. Si sólo se implementa una aproximación, etiquetarla como exploratoria. Nunca mostrar intervalos de confianza como si fueran plenamente consistentes con el diseño muestral si no lo son.

**Reglas de la siguiente decisión, definidas antes de ver resultados:**

- Si hay diferencia por sexo suficientemente sustentada y los subgrupos tienen tamaño adecuado, proponer una prueba sobre composición del hogar o presencia de menores.
- Si no aparece esa diferencia, proponer sensibilidad a traslados largos o relación no lineal.
- Si la calidad o el tamaño de la muestra impiden concluir, revisar variables, cohorte y medición antes de seguir.

Se requiere al menos una ejecución completa y una decisión posterior **realmente dependiente del resultado**. Una segunda ejecución fortalece el demo si cabe en el tiempo.

## 7. Arquitectura recomendada

El diagrama conceptual del equipo sitúa correctamente a **Omnigent como coordinador** y cierra el ciclo cuando la crítica científica cambia la siguiente decisión. Para construirlo en menos de 18 horas, separar el flujo lógico de la integración entre interfaces:

```text
Investigador
  ├─ Next.js web → panel del proyecto y lectura del estado
  └─ Omnigent web → iniciar y observar la sesión de investigación
       └─ Coordinador Omnigent
            ├─ Agente de evidencia → RAG con fuentes oficiales y literatura
            ├─ Agente de método/datos → perfil ENUT, hipótesis y ≥2 pruebas
            ├─ Herramienta determinista Python → ejecuta prueba elegida con ENUT 2024
            └─ Agente crítico → contrasta resultado, límites y siguiente prueba
                 └─ devuelve la decisión al coordinador

  Supabase = estado compartido persistente en cada paso:
    fuentes + pasajes + hipótesis + propuestas + ejecuciones + decisiones + eventos
  Python host = acceso al ZIP ENUT y producción de tablas/gráficos agregados
```

**Orden de ejecución:** pregunta → recuperación de evidencia → perfil de datos → hipótesis y dos propuestas → elección registrada → ejecución reproducible → crítica → decisión siguiente. Cada paso lee y escribe IDs en Supabase; el estado no es una etapa posterior a todos los agentes. El coordinador debe comprobar que la decisión usa el resultado real y conservar el enlace a la sesión Omnigent. El RAG aporta citas; el experimento aporta cifras.

**Integración web por etapas:** primero demostrar el ciclo en Omnigent web y mostrar sus resultados persistidos en Next.js. La web puede ofrecer un enlace visible para abrir la sesión. Sólo si el ciclo ya funciona y sobra tiempo, agregar un botón `Iniciar investigación` que llame desde un Route Handler protegido a la API de Omnigent y guarde el ID de sesión. Nunca llamar a Omnigent directamente desde el navegador con credenciales. La [API programática oficial](https://developers.databricks.com/docs/omnigent/programmatic) permite crear sesiones, enviar tareas y leer eventos, pero en el despliegue administrado usa autenticación del workspace, tokens renovables y un host disponible. Validar esos requisitos antes de prometer el botón para el demo.

**Roles mínimos:** coordinador + evidencia + método/datos + crítico. El ejecutor estadístico puede ser una herramienta Python con protocolos cerrados; convertirlo en un agente conversacional separado sólo si eso aporta una decisión propia y no retrasa la prueba. Python es la opción inicial; R es opcional si el equipo ya domina su flujo de encuestas. ENUT es una fuente de datos del ejecutor, no una salida del estado de investigación. El crítico debe registrar desacuerdos, limitaciones y una siguiente prueba concreta antes de devolver el control a Omnigent.

### Frontend y backend web

- Crear **Next.js App Router + TypeScript + Tailwind**. Desplegar en **Vercel** si el equipo tiene acceso. Next.js permite [Route Handlers](https://nextjs.org/docs/app/getting-started/route-handlers), por lo que no hace falta otro servidor HTTP para este MVP.
- Una pantalla principal `/research/[id]` debe mostrar: pregunta y cohorte; línea de tiempo de agentes; fuentes citadas; hipótesis y dos pruebas consideradas; resultado y gráfico; limitaciones; siguiente decisión; enlace a la sesión Omnigent.
- Una página `/` puede presentar el problema y enlazar al caso de investigación. Priorizar claridad del ciclo sobre una interfaz de chat abierta.
- Lectura pública sólo de datos agregados del demo. Escrituras restringidas a credenciales del servidor/host; **nunca** exponer la clave secreta de Supabase en el navegador. Configurar RLS o vistas seguras para lo publicado. [Guía de RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)
- Actualización del panel por consulta periódica sencilla; tiempo real es opcional si ya funciona el ciclo principal.

### Esquema mínimo de Supabase

| Tabla | Campos principales |
|---|---|
| `projects` | `id`, `title`, `question`, `cohort_definition`, `status`, `omnigent_session_url`, fechas |
| `sources` | `id`, `kind`, `title`, `url`, `doi`, `publisher`, `year`, `license`, `retrieved_at` |
| `passages` | `id`, `source_id`, `section`, `locator`, `content`, `embedding vector(384)` |
| `hypotheses` | `id`, `project_id`, `statement`, `status`, `supporting_passage_ids`, `opposing_passage_ids`, fechas |
| `experiment_proposals` | `id`, `project_id`, `hypothesis_id`, `protocol`, `learning_value`, `feasibility`, `cost`, `selected`, `selection_rationale`, fecha |
| `experiment_runs` | `id`, `project_id`, `hypothesis_id`, `protocol`, `dataset_hash`, `code_version`, `parameters`, `sample_sizes`, `results`, `artifact_paths`, `status`, fechas |
| `decisions` | `id`, `project_id`, `experiment_run_id`, `interpretation`, `uncertainty`, `next_test`, `rationale`, fecha |
| `agent_events` | `id`, `project_id`, `run_id`, `agent_name`, `event_type`, `input_refs`, `output_refs`, `occurred_at` |

Usar migraciones SQL versionadas. Crear un índice de texto y una función de búsqueda híbrida conforme a la [guía oficial de Supabase](https://supabase.com/docs/guides/ai/hybrid-search). Si el tamaño del corpus es pequeño, comprobar primero la corrección de resultados antes de optimizar índices vectoriales. Guardar gráficos, tablas descargables y registros de ejecución en un bucket de Storage cuando haga falta; los datos para el gráfico principal también pueden estar como JSON agregado en `experiment_runs`.

### RAG

- Corpus inicial deliberadamente pequeño: cuestionario, descriptor/diccionario y diseño muestral de ENUT 2024, más 10–20 publicaciones pertinentes encontradas mediante [OpenAlex](https://help.openalex.org/api/). Guardar texto completo sólo si existe permiso/licencia; si no, usar metadatos y resúmenes disponibles.
- Fragmentar por sección conservando título, URL/DOI y localizador. Mantener un único modelo de embeddings para ingesta y consulta. Valor por defecto: [`intfloat/multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small), de 384 dimensiones; respetar su formato de consulta/pasaje según la ficha del modelo.
- Recuperar los cinco pasajes más útiles con búsqueda híbrida; devolver siempre `source_id`, `passage_id`, URL y texto citado. Revisar manualmente cinco preguntas de recuperación.
- El RAG fundamenta conceptos, literatura y decisiones metodológicas. Los **resultados numéricos** salen del experimento reproducible, no de generación de texto.

### Omnigent y contratos de agentes

Definir configuraciones YAML y políticas en el repositorio. Omnigent soporta [agentes personalizados, subagentes y herramientas Python](https://github.com/omnigent-ai/omnigent/blob/main/docs/AGENT_YAML_SPEC.md). El coordinador recibe `project_id`, objetivo, tiempo/presupuesto y estado previo; especialistas intercambian IDs, no sólo prosa libre.

| Rol | Entrada | Herramientas permitidas | Salida estructurada |
|---|---|---|---|
| Evidencia | pregunta, alcance, corpus | `search_evidence`, `inspect_enut_variables` | `EvidencePack` con pasajes a favor/en contra, variables y dudas |
| Método | `EvidencePack`, cohorte, presupuesto | `get_dataset_profile`, `save_hypothesis` | `ExperimentProposal` con ≥2 pruebas, criterio de elección y protocolo |
| Análisis crítico | `ExperimentResult`, propuestas previas | `read_run`, `record_decision` | `DecisionUpdate` con hallazgo, límites y siguiente prueba |
| Coordinador | estado completo | subagentes y `run_experiment` | secuencia de traspasos y decisión final |

`run_experiment` acepta sólo protocolos predefinidos y parámetros validados; registra dataset, código, entradas y salidas. No darle ejecución arbitraria de consultas o shell sobre datos a los agentes del demo. La sesión de Omnigent debe mostrar llamadas y traspasos reales. La [interfaz programática](https://developers.databricks.com/docs/omnigent/programmatic) existe, pero la integración de inicio de sesión desde la app Next.js se considera posterior al primer ciclo funcional: para el MVP puede iniciarse desde Omnigent web y enlazarse la sesión desde el panel.

**Preflight obligatorio:** confirmar en la primera hora que el workspace tiene acceso al preview de Omnigent administrado y un host capaz de ejecutar Python y acceder a Supabase. Si no, usar Omnigent de código abierto con su interfaz web. [Quickstart oficial](https://developers.databricks.com/docs/omnigent/quickstart)

## 8. Roadmap operativo: máximo 18 horas

El trabajo puede repartirse entre tres personas: datos/estadística, Omnigent/RAG y Next.js/Supabase. Integrar temprano, sin esperar a terminar cada frente.

| Ventana | Tareas | Gate de salida |
|---|---|---|
| 0–1 h | Confirmar pregunta, descargar ENUT y descriptor, probar una sesión Omnigent, crear repo y proyectos Next/Supabase. | Acceso real a datos y orquestador. |
| 1–5 h | Datos: mapa de variables y primer análisis autónomo. Agentes: fuentes, recuperación y YAML. Web: migraciones y pantalla con datos de prueba. | Un script produce resultados reales y la web carga. |
| 5–9 h | Conectar RAG, herramientas Python y persistencia. Ejecutar un ciclo en Omnigent. | Resultado real + decisión posterior guardados antes de la hora 9. |
| 9–12 h | Mostrar en Next fuentes, traspasos, gráfico, limitaciones y siguiente prueba. | La web reconstruye el ciclo sin explicación oral. |
| 12–15 h | Revisar pesos, faltantes, subgrupos y citas; repetir el experimento desde el mismo dataset y código. Medir tiempo de un flujo manual comparable. | Reproducción y medición honestas. |
| 15–17 h | Desplegar web, ordenar repositorio, políticas, resultados, README y grabar demo de dos minutos. | Submission completa. |
| 17–18 h | Margen para fallos. | URL y video funcionales. |

**Regla de alcance:** si a la hora 9 falta el ciclo científico, detener mejoras visuales y concentrar a todo el equipo en Omnigent + experimento + decisión. La web puede ser una sola página. No agregar mapas de rutas, recomendaciones de transporte, modelos causales, cuentas de usuario ni múltiples datasets antes de cumplir ese gate.

## 9. Medición y demo

- Definir un cuello de botella: tiempo desde una pregunta hasta una prueba reproducible y una siguiente decisión con evidencia.
- Cronometrar un intento manual breve y el flujo asistido **con el mismo corpus y dataset disponibles**. Reportar duración, intervención humana y límites de comparabilidad. No declarar 10× si no se observó.
- Revisar manualmente al menos diez afirmaciones factuales del panel/reporte contra las fuentes enlazadas y cinco consultas del recuperador.
- Estructura sugerida del demo de dos minutos: problema y pregunta (15 s); agentes y fuentes (25 s); dos pruebas y elección (20 s); ejecución y resultado real (35 s); decisión actualizada y limitaciones (25 s).

## 10. Definición de terminado

El MVP está listo cuando se puede:

1. Abrir una URL web y entender la pregunta, población, fuentes y estado de investigación.
2. Ver una sesión Omnigent con al menos tres roles efectivos, herramientas y traspasos.
3. Inspeccionar dos pruebas propuestas, la elegida y su criterio de elección.
4. Reejecutar el código estadístico sobre ENUT 2024 y obtener el mismo resultado dentro de tolerancias declaradas.
5. Ver cifras con unidad semanal, muestra, método, incertidumbre y enlaces de procedencia.
6. Ver una nueva decisión derivada del resultado, con explicación y siguiente prueba.
7. Consultar en el repositorio migraciones, configuraciones/políticas de agentes, instrucciones de ejecución, código, resultados y medición de aceleración.

## 11. Decisiones y comprobaciones aún abiertas

- Confirmar credenciales y disponibilidad de Omnigent administrado, Supabase y Vercel; no guardar secretos en este archivo ni en Git.
- Confirmar en el descriptor ENUT las llaves, códigos de faltantes, filtros de ocupación, composición de cada categoría de tiempo y códigos geográficos. Los campos citados arriba son puntos de partida verificados, **no** una transformación completa validada.
- Elegir y documentar si se incluye cuidado pasivo/simultáneo; distinguir convivencia de cuidado familiar.
- Elegir el método de incertidumbre que el equipo pueda implementar correctamente con el diseño de encuesta. Si no hay tiempo para inferencia completa, reportar un resultado exploratorio y sus límites.
- Evaluar tamaño efectivo de las muestras por sexo y categoría antes de comunicar diferencias.

## 12. Primera secuencia de implementación para el agente

1. Crear el repositorio con `web/` para Next.js, `analysis/` para Python, `agents/` para Omnigent y `supabase/migrations/` para SQL.
2. Implementar migración de tablas y políticas de lectura/escritura; guardar variables de entorno de ejemplo sin valores secretos.
3. Descargar ENUT 2024, inspeccionar descriptor y generar un mapa de variables versionado; ejecutar un primer análisis independiente de la web.
4. Ingerir un corpus pequeño de fuentes oficiales y literatura, comprobar recuperación con citas y conectar los especialistas Omnigent.
5. Persistir un ciclo completo y mostrarlo en una página Next.js; después desplegar y verificar el demo.

Trabajar a partir de resultados observados. Si un supuesto de este contexto contradice el diccionario, los microdatos o la documentación actual, corregir el supuesto en el repositorio y registrar la decisión.
