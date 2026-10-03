# Hack-Nation: Agentic Scientific Discovery Lab

## Overview
This project is part of the **Hack-Nation 7th Global AI Hackathon (Challenge 03)**. Our goal is to build an agentic AI lab aimed at achieving 10x faster scientific discovery. 

We are applying this architecture to analyze **ENUT (National Survey on Time Use) data**, demonstrating how coordinated AI agents can generate insights, formulate hypotheses, design experiments, and interpret results autonomously.

## Architecture
Our solution is powered by **Omnigent** (Databricks/Open Source) as the core orchestration layer. To ensure scientific rigor, reproducibility, and a visual demonstration of the discovery loop, we enforce a **Shared Research State** pattern.

Instead of ambiguous text-based conversations, our agents communicate strictly by reading and updating a centralized JSON object.

### The 7-Agent Squad
1. **Literature Agent**: Finds prior evidence and gaps.
2. **Hypothesis Agent**: Proposes falsifiable explanations.
3. **Data Steward**: Validates if available ENUT data can test the hypothesis.
4. **Experiment Planner**: Designs the test to maximize learning.
5. **Experiment Runner**: Executes pre-defined, reproducible statistical protocols on ENUT data (no arbitrary code).
6. **Scientific Critic**: Evaluates results and checks for interpretation errors.
7. **Discovery Director**: Decides the next action based on the full state.

## Current Status (2026-10-03)

**Research question.** Among workers aged 18–65 living in Mexico City and the State of Mexico, which dimension of personal time shows the strongest negative association with five additional hours of weekday commuting? All findings are observational associations, not causal effects.

**Scientific data layer (done).** ENUT 2024 microdata were processed into the canonical dataset `analytic_v1` (2,563 workers, `APPROVED_FOR_EXPERIMENTS`). Variable definitions are in [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md) and provenance is in [`metadata/analytic_v1_manifest.json`](metadata/analytic_v1_manifest.json).

**Deterministic experiment engine (done).** [`src/experiments/`](src/experiments/) turns a strictly validated `ExperimentSpec` into an `ExperimentResult`. It uses FAC_PER-weighted linear regression with PSU-clustered (CR1) uncertainty. This approximates ENUT's complex-survey variance and does not fully reconstruct it. Agents request experiments through this engine. They never compute or invent numbers. See [`docs/EXPERIMENT_ENGINE.md`](docs/EXPERIMENT_ENGINE.md).

**EXP-001 (completed, awaiting human review).** Longer weekday commuting showed the strongest negative point association with sleep (about −49 weekday minutes per +300 commute minutes). Uncertainty prevented a definitive ranking across all four time-use outcomes (sleep, leisure, household conversation, personal hygiene). See [`reports/experiments/EXP-001/summary.md`](reports/experiments/EXP-001/summary.md).

**Next: the agentic discovery loop.** A Scientific Critic reviews EXP-001. A Hypothesis Agent and an Experiment Planner then propose competing follow-up experiments. The Discovery Director, orchestrated by Omnigent, selects one and explains the choice. The engine runs it, and the new evidence updates the next decision. No experiment sequence is hard-coded.

## 🚀 Getting Started

### Prerequisites
- Python environment (uv or pipx recommended)
- Databricks API keys configured

### Installation
Install Omnigent with Databricks support:
```bash
uv tool install "omnigent[databricks]"
```
or 
```
pip install "omnigent[databricks]"
```

The agent tools also need the Python dependencies in `analysis/` (`cd analysis && uv sync`), a `.env` at the repo root with `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`, and a Databricks CLI profile (`DEFAULT` by default; see `executor.auth` in `omnigent.yaml`).

### Running the Lab
Start a session with the Discovery Director, sending the initial Shared Research State as the first message. Run it from the repo root so the tools in `agents/commute_lab/` and `analysis/` are importable:
```bash
PYTHONPATH=agents:analysis omnigent run omnigent.yaml -p "$(cat initial_state.json)"
```