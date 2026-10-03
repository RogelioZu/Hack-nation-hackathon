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