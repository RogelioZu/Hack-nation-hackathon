# Hipótesis retiradas (primera corrida, 2026-10-04)

HYP-001 a HYP-003 las generó el Hypothesis Agent real (`databricks-gpt-oss-120b`, sesión
`2faee997389744c9a168a9bc22a0cb80`) y pasaron el validador de ese momento. Al revisarlas aparecieron tres
huecos en el validador, y las tres incumplen el validador endurecido:

- **Las tres:** el criterio de apoyo y de refutación compara solo estimaciones puntuales. En HYP-001 ese
  orden ya se cumple en EXP-001 (sueño −48.711 frente a ocio −20.396), aunque la diferencia no excluye el
  cero, así que la afirmación no se puede refutar tal como está escrita.
- **HYP-002:** `known_executable: true` para comparar coeficientes entre mujeres y hombres. Según el
  contrato, las corridas separadas por subgrupo son descriptivas, no una prueba formal de la diferencia.
- **HYP-003:** lenguaje causal ("a possible stronger effect").

Se conservan sin cambios como registro. Sus IDs no se reutilizan.

## Segunda corrida (sesión `afc927adf6fd4af0883afa7219e1b10c`)

HYP-004 (ocio < 0) y HYP-006 (higiene > 0) pasaron el validador de ese momento, pero no son hipótesis nuevas.
EXP-001 ya estimó esos mismos coeficientes con los mismos datos, la misma población y el mismo modelo, y
sus intervalos incluyen el cero: ocio [-43.436, 2.644], higiene [-0.76, 6.948]. La observación que las
refutaría ya está observada, y repetir el motor daría el mismo resultado. Se agregó la regla de novedad:
una hipótesis debe añadir un subgrupo, una comparación entre grupos, una variable aprobada no usada o una
forma funcional distinta. HYP-005 sigue activa.
