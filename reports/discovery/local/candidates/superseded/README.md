# Propuestas retiradas (primera corrida del Experiment Planner, 2026-10-04)

Las generó el Experiment Planner real (`databricks-gpt-oss-120b`, sesión `224bcdee13c74ddd9a9b87f90044cc46`)
y pasaron el validador de ese momento. Al revisarlas aparecieron estos problemas, y las dos incumplen el
validador corregido:

- **PROP-001** (HYP-005, interacción traslado × sexo): el diseño es correcto, pero `contradicting_result`
  clasifica "el intervalo incluye el cero" como refutación. Eso es inconcluso, y además el mismo caso
  aparece en `inconclusive_result`.
- **PROP-002** (HYP-007, exploratoria): el criterio compara el coeficiente del subgrupo con el estimado
  global, que no es un contraste entre grupos.
- **Corrida:** el chequeo de duplicados marcaba como duplicado de PROP-001 una prueba formal sobre otro
  outcome (ocio) o con otra hipótesis, y eso bloqueó las pruebas formales de HYP-007 y HYP-008. Además, el
  agente reportó "PROP-003 saved" sin haber llamado a `save_proposal` para ella.

Se conservan sin cambios como registro. Sus IDs no se reutilizan.

## Segunda corrida (sesión `17efb538793b420ead3faa1bbab8845c`)

PROP-003 y PROP-005 siguen activas. Se retiraron estas dos:

- **PROP-004** (HYP-007, interacción traslado × `has_child_u15`): el modelo no incluye el efecto principal de
  `has_child_u15`, lo que deja mal especificada la interacción. Además, `has_child_u15` no es una covariable
  del schema y la propuesta no declara `covariates_outside_schema`.
- **PROP-006** (HYP-008, ocio por sexo): HYP-008 predice una diferencia en cualquier sentido, pero la
  propuesta solo cuenta como apoyo una interacción negativa y trata una positiva como refutación.

Reglas nuevas del validador: las interacciones deben incluir el efecto principal del moderador, y en una
hipótesis bidireccional el apoyo debe aceptar ambos sentidos, sin tratar un "excluye cero" como refutación.

## Cuarta corrida (sesión `7976f509cc7d4db899b99c40ef9fa8e9`)

- **PROP-007** (HYP-007, interacción traslado × `has_child_u15`): el diseño es correcto (incluye el término
  principal y declara las capacidades faltantes), pero `scientific_value` afirma que la prueba "provides
  definitive evidence". Es una sobreafirmación: una prueba observacional da una estimación con
  incertidumbre.
- En esa corrida el agente se atascó en HYP-008 por dos fallas del validador, ya corregidas. Rechazaba
  "main effect", que es terminología estadística y no causal. Y en una hipótesis bidireccional no explicaba
  qué refutación es válida: la equivalencia dentro de un margen fijado por revisión humana. Además, el
  CLI de Omnigent terminó con "Turn did not complete within 120s" (subscribe-after-post race).
