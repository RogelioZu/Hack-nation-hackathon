"""Omnigent policies for the research agents (declared in /omnigent.yaml)."""

# Actions that need a human sign-off (AGENTS.md §7.4).
APPROVAL_TOOLS = {"run_experiment", "record_decision"}


def ask_before_run(event: dict) -> dict | None:
    """ASK before running an experiment or recording a decision; abstain otherwise."""
    if event.get("type") != "tool_call":
        return None
    tool = event.get("target") or (event.get("data") or {}).get("name")
    if tool in APPROVAL_TOOLS:
        return {"result": "ASK", "reason": f"Human approval required before {tool}."}
    return None
