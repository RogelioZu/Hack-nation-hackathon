"""Deterministic review summary; no inferred mechanisms or agent interpretation."""
import re

from .runner import RANKING_NOT_APPLICABLE

PROTOCOL_HYPOTHESES = ("H1", "H2", "H3", "H4")
INTERACTION_STATUS_TEXT = {
    "INTERVAL_EXCLUDES_ZERO": "El intervalo de la interacción excluye el cero: compatible con una diferencia en la "
                              "asociación entre los grupos del moderador (asociación observacional, no causal).",
    "INCONCLUSIVE_INTERVAL_INCLUDES_ZERO": "El intervalo de la interacción incluye el cero: resultado inconcluso sobre "
                                           "una diferencia entre los grupos del moderador. No es evidencia de que no "
                                           "haya diferencia.",
}


def _spanish_list(items):
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " y " + items[-1]


def _next_experiment_id(experiment_id):
    match = re.fullmatch(r"EXP-(\d+)", experiment_id)
    return f"EXP-{int(match.group(1)) + 1:0{len(match.group(1))}d}" if match else "un experimento siguiente"


def _slope(s):
    return f"{s.estimate:.3f} | {s.standard_error:.3f} | [{s.interval.lower:.3f}, {s.interval.upper:.3f}]"


def _interaction_section(result):
    lines = ["", "## Interacción (exposición × moderador)", ""]
    for r in result.interactions:
        if r.variant != "adjusted":
            continue
        groups = {g.role: g for g in r.groups}
        ref, cmp = groups["reference"], groups["comparison"]
        lines += [f"Modelo `{r.model_id}`. Moderador: **{r.moderator}**. Grupo de referencia: **{r.reference_level!s}** "
                  f"(n={ref.n}; suma FAC_PER={ref.weighted_population:,.0f}). Grupo de comparación: "
                  f"**{r.comparison_level!s}** (n={cmp.n}; suma FAC_PER={cmp.weighted_population:,.0f}).",
                  f"Codificación: {r.coding}. Personas analizadas: {r.analysis_n} de {r.input_n}; "
                  f"sin dato del moderador: {r.missing_moderator_n}.", "",
                  "| Estimando | Estimación | EE | IC 95% |", "|---|---:|---:|---:|",
                  f"| Pendiente de {r.exposure} en el grupo de referencia ({r.moderator} = {r.reference_level!s}) | {_slope(r.reference_group_slope)} |",
                  f"| Pendiente de {r.exposure} en el grupo de comparación ({r.moderator} = {r.comparison_level!s}) | {_slope(r.comparison_group_slope)} |",
                  f"| Interacción: diferencia de pendientes ({r.comparison_level!s} − {r.reference_level!s}) | {_slope(r.interaction)} |",
                  f"| Efecto principal del moderador ({r.moderator_term}) | {_slope(r.moderator_main_effect)} |", "",
                  f"Estado de la interacción: **{r.interpretation_status}**. {INTERACTION_STATUS_TEXT[r.interpretation_status]}"
                  f"{'' if r.equivalence_assessed else ' No se evaluó equivalencia.'}",
                  f"Pendiente del grupo de comparación: {r.comparison_slope_method}.", ""]
    return lines[:-1]


def render_summary(result):
    moderated = bool(result.interactions)
    reference = next((r for r in result.interactions or [] if r.variant == "adjusted"), None)
    lines = [f"# {result.experiment_id} — revisión científica", "",
             f"Estado: **{result.status}**. Revisión: **{result.review_status}**.", "",
             f"Población primaria: **{result.sample_size:,} personas**; suma FAC_PER: **{result.weighted_population:,.0f} personas**.",
             "Minutos totales de lunes a viernes; coeficientes por 300 minutos adicionales de traslado.", "",
             "## Asociaciones", "",
             "Ajuste primario: trabajo entre semana, edad, sexo y estado. Referencias: hombre y CDMX (09).", ""]
    if moderated:
        lines += [f"Modelo con interacción: la columna de pendiente es la del **grupo de referencia** "
                  f"({reference.moderator} = {reference.reference_level!s}), no un coeficiente agrupado de toda la "
                  "población. Las pendientes de ambos grupos y su diferencia están en la sección de interacción.", "",
                  f"| Outcome | Modelo | n | Pendiente del grupo de referencia ({reference.moderator} = {reference.reference_level!s}) | IC 95% puntual |"]
    else:
        lines += ["| Outcome | Modelo | n | Coeficiente | IC 95% puntual |"]
    lines += ["|---|---|---:|---:|---:|"]
    for e in result.estimates:
        lines.append(f"| {e.outcome} | {e.variant} | {e.n} | {e.coefficient:.3f} | [{e.interval.lower:.3f}, {e.interval.upper:.3f}] |")
    if moderated:
        lines += _interaction_section(result)
    if result.ranking["status"] == RANKING_NOT_APPLICABLE:
        lines += ["", "## Orden e incertidumbre", "", f"**{result.ranking['status']}**.", "",
                  "Hay un solo outcome primario, así que no se evalúa un orden entre outcomes.", "", "## Sensibilidad", ""]
    else:
        lines += ["", "## Orden e incertidumbre", "", f"**{result.ranking['status']}**.", "",
                  "Orden descriptivo de los coeficientes ajustados (más negativo primero):"]
        lines += [f"{r['rank']}. {r['outcome']}: {r['coefficient']:.3f}" for r in result.ranking["point_estimate_order"]]
        lines += ["", "Las diferencias usan la covarianza entre outcomes estimados en las mismas personas. Bonferroni sobre todos los pares, con cobertura familiar nominal de 95%.", "",
                  "| A − B | Diferencia | Intervalo simultáneo |", "|---|---:|---:|"]
        for c in result.ranking["paired_comparisons"]:
            lines.append(f"| {c['outcome_a']} − {c['outcome_b']} | {c['difference_a_minus_b']:.3f} | [{c['interval']['lower']:.3f}, {c['interval']['upper']:.3f}] |")
        lines += ["", "El orden puntual no implica una jerarquía definitiva. No resolver una diferencia tampoco demuestra equivalencia.", "", "## Sensibilidad", ""]
    if not result.sensitivity_results:
        lines += ["La especificación aprobada no incluye análisis de sensibilidad."]
    for s in result.sensitivity_results:
        lines += [f"Regla: {s['rule']}. Excluye **{s['n_excluded']}** personas; n={s['n_after']}; suma de pesos={s['weighted_population']:,.0f}.",
                  f"Estado de orden: **{s['ranking']['status']}**. La población primaria permanece intacta.", "",
                  "| Outcome | Cambio coeficiente | Dirección primaria → sensibilidad | Rango primario → sensibilidad |",
                  "|---|---:|---|---|"]
        for c in s["comparison"]:
            lines.append(f"| {c['outcome']} | {c['coefficient_difference']:.3f} | {c['primary_direction']} → {c['sensitivity_direction']} | {c['primary_rank']} → {c['sensitivity_rank']} |")
    lines += ["", "## Población y faltantes", "", "| Paso | n | Suma de pesos |", "|---|---:|---:|"]
    for c in result.population_counts:
        lines.append(f"| {c['step']} | {c['n']} | {c['weighted_population']:,.0f} |")
    lines += ["", "| Variable canónica | Faltantes primarios |", "|---|---:|"]
    lines += [f"| {v} | {n} |" for v,n in result.missingness.items()]
    lines += ["", "## Diagnósticos", "", "| Modelo | Excluidos por faltantes | UPM | Estratos | gl | R² ponderado | Predicciones negativas | Leverage >2p/n |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for key, d in result.model_diagnostics.items():
        r2 = "NA" if d["weighted_r_squared"] is None else f"{d['weighted_r_squared']:.4f}"
        lines.append(f"| {key} | {d['n_missing_excluded']} | {d['clusters']} | {d['strata']} | {d['inference_df']} | {r2} | {d['negative_fitted_count']} | {d['high_leverage_count_above_2p_over_n']} |")
    lines += ["", "Todos los extremos permanecen; las advertencias de leverage y predicciones negativas son diagnósticos, no exclusiones.",
              "", "## Hipótesis", ""]
    for label, rows in [("Evidencia compatible", result.supported_hypotheses), ("No respaldadas en este modelo", result.unsupported_hypotheses), ("Inconclusas", result.inconclusive_hypotheses)]:
        for row in rows:
            lines.append(f"- {label}: {row['id']} — {row['assessment']}. {row['evidence']}")
    # "Not evaluated" is derived from the hypotheses the engine actually assessed in this result.
    assessed = {row["id"] for row in result.supported_hypotheses + result.unsupported_hypotheses + result.inconclusive_hypotheses}
    pending = [h for h in PROTOCOL_HYPOTHESES if h not in assessed]
    not_evaluated = (f"{_spanish_list(pending)} no se evaluaron. " if len(pending) > 1 else
                     f"{pending[0]} no se evaluó. " if pending else "")
    lines += ["", f"{not_evaluated}Las categorías conservan evidencia y límites, no valores booleanos.",
              "", "## Método y límites", "",
              "Estimación FAC_PER por mínimos cuadrados ponderados, errores agrupados por (EST_DIS, UPM_DIS), corrección CR1 y cuantiles t con G−1 grados de libertad. Los pesos se escalan por una constante para estabilidad numérica; los totales usan FAC_PER original.", "",
              "**No es una estimación completa de varianza de encuesta.** EST_DIS identifica los conglomerados; no se aplica centrado dentro de estrato, FPC ni reconstrucción del diseño fuera del dominio.", "",
              "Referencias de implementación: [statsmodels sandwich](https://www.statsmodels.org/stable/_modules/statsmodels/stats/sandwich_covariance.html) y [survey: subpoblaciones](https://r-survey.r-forge.r-project.org/survey/html/subset.survey.design.html). Ecuaciones y decisiones completas: `docs/EXPERIMENT_ENGINE.md`.", ""]
    lines += [f"- {x}" for x in result.limitations]
    lines += ["", "## Alternativas para revisión, sin selección", ""]
    lines += [f"- {c['question']} {c['expected_information']}. {c['feasibility']}." for c in result.candidate_next_experiments]
    lines += ["", f"No se asigna {_next_experiment_id(result.experiment_id)}. La siguiente decisión queda pendiente de revisión humana.", "", "## Reproducción y procedencia", "",
              f"Dataset SHA256: `{result.provenance['dataset_sha256']}`.",
              f"Spec SHA256: `{result.provenance['spec_sha256']}`.",
              f"Código SHA256: `{result.provenance['code_sha256']}`.",
              f"Hash de analytic_v1 sin cambios: {result.provenance['dataset_hash_unchanged']}.", "",
              f"`python scripts/run_experiment.py experiments/{result.experiment_id}/spec.json` ejecuta dos veces y exige resultados idénticos antes de publicar. `validation.json` registra la verificación de ejecución; `result.json` conserva matrices, diagnósticos, transformaciones y procedencia de cada estimación.", "",
              "EXPERIMENT_COMPLETED", ""]
    return "\n".join(lines)
