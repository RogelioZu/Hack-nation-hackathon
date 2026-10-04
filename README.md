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

## Current Status (2026-10-04)

**Research question.** Among workers aged 18–65 living in Mexico City and the State of Mexico, which dimension of personal time shows the strongest negative association with five additional hours of weekday commuting? All findings are observational associations, not causal effects.

**Scientific data layer (done).** ENUT 2024 microdata were processed into the canonical dataset `analytic_v1` (2,563 workers, `APPROVED_FOR_EXPERIMENTS`). Variable definitions are in [`docs/DATA_CONTRACT.md`](docs/DATA_CONTRACT.md) and provenance is in [`metadata/analytic_v1_manifest.json`](metadata/analytic_v1_manifest.json).

**Deterministic experiment engine (done).** [`src/experiments/`](src/experiments/) turns a strictly validated `ExperimentSpec` into an `ExperimentResult`. It uses FAC_PER-weighted linear regression with PSU-clustered (CR1) uncertainty. This approximates ENUT's complex-survey variance and does not fully reconstruct it. Agents request experiments through this engine. They never compute or invent numbers. See [`docs/EXPERIMENT_ENGINE.md`](docs/EXPERIMENT_ENGINE.md).

**EXP-001 (completed, awaiting human review).** Longer weekday commuting showed the strongest negative point association with sleep (about −49 weekday minutes per +300 commute minutes). Uncertainty prevented a definitive ranking across all four time-use outcomes (sleep, leisure, household conversation, personal hygiene). See [`reports/experiments/EXP-001/summary.md`](reports/experiments/EXP-001/summary.md).

**The agentic discovery loop ran once, end to end.** No experiment sequence was hard-coded. Each step left a committed artifact:
1. The Scientific Critic reviewed EXP-001 and flagged sex differences (H3) as untested.
2. The Hypothesis Agent proposed falsifiable hypotheses, which a human approved for planning (REV-001).
3. The Experiment Planner proposed competing experiments: formal interaction tests and an exploratory subgroup model.
4. The Discovery Director preferred the formal test, but first recorded that it was waiting for an engine capability.
5. The engine gained binary-moderator interactions, the Director reassessed, and a human approved the experiment (REV-DEC-005-001).

**EXP-002 (completed, awaiting human review).** A formal commute × sex interaction for weekday sleep. The female slope point estimate is more negative than the male one, but the interaction interval includes zero (−17.7 weekday minutes, 95% interval [−47.5, 12.1]). The critic therefore moved **H3 from UNTESTED to INCONCLUSIVE**: the lab tested the question and recorded that it remains unresolved, instead of claiming a difference or its absence. See [`reports/experiments/EXP-002/summary.md`](reports/experiments/EXP-002/summary.md) and [`reports/discovery/local/research_state.json`](reports/discovery/local/research_state.json).

## Discovery UI

**Live:** https://commute-time-lab.vercel.app

The web app in [`web/`](web/) replays the whole run as seven stages, read from the committed artifacts:
1. Research question
2. EXP-001 evidence
3. Scientific critic
4. Hypotheses and experiment planning
5. Discovery decision, with the engine capability change and human approval
6. EXP-002
7. Updated scientific state

A build-time adapter normalizes the artifacts into one view model, using `research_state.json` as the index. Components never hard-code a number, status or id. Replay needs no agents, model provider or database. Run it with:

```bash
cd web
npm install
npm run dev              # http://localhost:3000/
npm run test:discovery   # acceptance checks
```

## 🚀 Getting Started

### Prerequisites
- Python environment (uv recommended); the experiment engine runs in its own Python 3.12 venv (`requirements-experiments.txt`)
- A Databricks workspace token in `DATABRICKS_TOKEN` for the agents (`openai-agents` harness with `databricks-gpt-oss-120b`; see `executor` in `omnigent.yaml` and [`AGENTS.md`](AGENTS.md) §10)
- Node.js for the web app

### Installation
Install Omnigent with Databricks support:
```bash
uv tool install "omnigent[databricks]"
```
or 
```
pip install "omnigent[databricks]"
```

The agent tools also need the Python dependencies in `analysis/` (`cd analysis && uv sync`) and a `.env` at the repo root with `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` and `DATABRICKS_TOKEN`. The agents run on open-source Omnigent; see `executor` in `omnigent.yaml`. Omnigent does not read `.env`, so load it first with `set -a; source .env; set +a`. The full command list is in [`AGENTS.md`](AGENTS.md) §10.

### Running the Lab
Start a session with the Discovery Director, sending the initial Shared Research State as the first message. Run it from the repo root so the tools in `agents/commute_lab/` and `analysis/` are importable:
```bash
PYTHONPATH=agents:analysis omnigent server --background
PYTHONPATH=agents:analysis omnigent run omnigent.yaml --server http://127.0.0.1:6767 -p "$(cat initial_state.json)"
omnigent stop
```

After agents write new artifacts, rebuild the state index and the UI bundle, then commit both:

```bash
python scripts/build_research_state.py
cd web && npm run snapshot
```