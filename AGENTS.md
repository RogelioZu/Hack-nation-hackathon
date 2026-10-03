# AI Development Context: Omnigent Agent Architecture

> **Note to AI Assistants (Claude,Codex,Cursor, Copilot, etc.):** Use this document as the absolute source of truth for the agent architecture and data flow in this project.

## Core Constraint: The Shared Research State
Agents in this system **DO NOT** communicate via free-text chats. They communicate exclusively by receiving, mutating, and returning a single JSON object (the Shared Research State). 

Every agent's system prompt must enforce that their output is strictly this JSON object.

### JSON Schema
```json
{
  "research_question": "String",
  "population": "Object",
  "hypotheses": [
    { "id": "String", "claim": "String", "status": "untested | tested" }
  ],
  "evidence": ["Array of evidence cards"],
  "variables": "Object mapping concepts to data columns",
  "experiments": [
    { "id": "String", "hypothesis_id": "String", "method": "String", "status": "String" }
  ],
  "results": ["Array of metrics and artifacts"],
  "limitations": ["Array of strings"],
  "next_decision": { "experiment": "String", "reason": "String" }
}
```

## Agent Roles & Handoffs
Omnigent handles the routing. Each agent owns a specific scientific decision:

| Agent | Scientific Decision | Input | Output |
| :--- | :--- | :--- | :--- |
| **Discovery Director** | What to investigate next | Complete State | Next Action |
| **Literature Agent** | What prior evidence exists | Question | Evidence Cards + Citations |
| **Data Steward** | If data allows testing it | Hypothesis | Variable Map + Quality Report |
| **Hypothesis Agent** | What falsifiable explanation to test | Evidence | Ranked Hypotheses |
| **Experiment Planner**| What test maximizes learning | Hypotheses + Data | Experiment Spec |
| **Experiment Runner** | Execute test reproducibly | Experiment Spec | Metrics + Artifacts |
| **Scientific Critic** | If interpretation is trustworthy | Results | Critique + Validation Requests |