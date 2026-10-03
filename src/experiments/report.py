"""Deterministic review summary; no inferred mechanisms or agent interpretation."""


def render_summary(result):
    lines = [f"# {result.experiment_id} — revisión científica", "",
             f"Estado: **{result.status}**. Revisión: **{result.review_status}**.", "",
             f"Población primaria: **{result.sample_size:,} personas**; suma FAC_PER: **{result.weighted_population:,.0f} personas**.",
             "Minutos totales de lunes a viernes; coeficientes por 300 minutos adicionales de traslado.", "",
             "## Asociaciones", "",
             "Ajuste primario: trabajo entre semana, edad, sexo y estado. Referencias: hombre y CDMX (09).", "",
             "| Outcome | Modelo | n | Coeficiente | IC 95% puntual |", "|---|---|---:|---:|---:|"]
    for e in result.estimates:
        lines.append(f"| {e.outcome} | {e.variant} | {e.n} | {e.coefficient:.3f} | [{e.interval.lower:.3f}, {e.interval.upper:.3f}] |")
    lines += ["", "## Orden e incertidumbre", "", f"**{result.ranking['status']}**.", "",
              "Orden descriptivo de los coeficientes ajustados (más negativo primero):"]
    lines += [f"{r['rank']}. {r['outcome']}: {r['coefficient']:.3f}" for r in result.ranking["point_estimate_order"]]
    lines += ["", "Las diferencias usan la covarianza entre outcomes estimados en las mismas personas. Bonferroni sobre todos los pares, con cobertura familiar nominal de 95%.", "",
              "| A − B | Diferencia | Intervalo simultáneo |", "|---|---:|---:|"]
    for c in result.ranking["paired_comparisons"]:
        lines.append(f"| {c['outcome_a']} − {c['outcome_b']} | {c['difference_a_minus_b']:.3f} | [{c['interval']['lower']:.3f}, {c['interval']['upper']:.3f}] |")
    lines += ["", "El orden puntual no implica una jerarquía definitiva. No resolver una diferencia tampoco demuestra equivalencia.", "", "## Sensibilidad", ""]
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
    lines += ["", "H3 y H4 no se evaluaron. Las categorías conservan evidencia y límites, no valores booleanos.",
              "", "## Método y límites", "",
              "Estimación FAC_PER por mínimos cuadrados ponderados, errores agrupados por (EST_DIS, UPM_DIS), corrección CR1 y cuantiles t con G−1 grados de libertad. Los pesos se escalan por una constante para estabilidad numérica; los totales usan FAC_PER original.", "",
              "**No es una estimación completa de varianza de encuesta.** EST_DIS identifica los conglomerados; no se aplica centrado dentro de estrato, FPC ni reconstrucción del diseño fuera del dominio.", "",
              "Referencias de implementación: [statsmodels sandwich](https://www.statsmodels.org/stable/_modules/statsmodels/stats/sandwich_covariance.html) y [survey: subpoblaciones](https://r-survey.r-forge.r-project.org/survey/html/subset.survey.design.html). Ecuaciones y decisiones completas: `docs/EXPERIMENT_ENGINE.md`.", ""]
    lines += [f"- {x}" for x in result.limitations]
    lines += ["", "## Alternativas para revisión, sin selección", ""]
    lines += [f"- {c['question']} {c['expected_information']}. {c['feasibility']}." for c in result.candidate_next_experiments]
    lines += ["", "No se asigna EXP-002. La siguiente decisión queda pendiente de revisión humana.", "", "## Reproducción y procedencia", "",
              f"Dataset SHA256: `{result.provenance['dataset_sha256']}`.",
              f"Spec SHA256: `{result.provenance['spec_sha256']}`.",
              f"Código SHA256: `{result.provenance['code_sha256']}`.",
              f"Hash de analytic_v1 sin cambios: {result.provenance['dataset_hash_unchanged']}.", "",
              "`python scripts/run_experiment.py experiments/EXP-001/spec.json` ejecuta dos veces y exige resultados idénticos antes de publicar. `validation.json` registra la verificación de ejecución; `result.json` conserva matrices, diagnósticos, transformaciones y procedencia de cada estimación.", "",
              "EXPERIMENT_COMPLETED", ""]
    return "\n".join(lines)
