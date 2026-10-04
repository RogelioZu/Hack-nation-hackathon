"""Build the Shared Research State from committed artifacts (docs/RESEARCH_STATE.md).

    python scripts/build_research_state.py                 # validate, write the snapshot, print a summary
    python scripts/build_research_state.py --check         # validate only, write nothing
    python scripts/build_research_state.py --print         # also print the full state JSON
    python scripts/build_research_state.py --trace CRIT-EXP-001-001

The snapshot reports/discovery/<workspace>/research_state.json is generated output, never a source.
It is written only when the state is valid. Exit code 1 on validation errors.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agents"))

from commute_lab.research_state import build_state, dumps, snapshot_path, trace  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", default="local", help="reports/discovery/<workspace> (default: local)")
    parser.add_argument("--check", action="store_true", help="validate only; do not write the snapshot")
    parser.add_argument("--print", dest="print_state", action="store_true", help="print the full state JSON")
    parser.add_argument("--trace", metavar="ID", help="print what an object relies on and what uses it")
    parser.add_argument("--allow-changed", action="append", default=[], metavar="PATH",
                        help="accept that this already-indexed artifact changed (repeatable)")
    args = parser.parse_args()

    out = snapshot_path(ROOT, args.workspace)
    previous = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
    state, issues = build_state(ROOT, args.workspace, previous, frozenset(args.allow_changed))
    valid = state["validation"]["valid"]

    if args.trace:
        known = {link["from"] for link in state["links"]} | {link["to"] for link in state["links"]} | \
            {e["evidence_id"] for e in state["evidence"]}
        if args.trace not in known:
            print(f"unknown or unlinked id: {args.trace}", file=sys.stderr)
            return 1
        print(json.dumps(trace(state, args.trace), indent=2, ensure_ascii=False))
        return 0 if valid else 1
    if args.print_state:
        print(dumps(state), end="")

    written = False
    if valid and not args.check:
        text = dumps(state)
        if not out.exists() or out.read_text(encoding="utf-8") != text:
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp = out.with_suffix(".json.tmp")
            tmp.write_text(text, encoding="utf-8", newline="\n")
            os.replace(tmp, out)
            written = True

    summary = {
        "valid": valid,
        "research_id": state["research_id"],
        "counts": {k: len(state[k]) for k in ("evidence", "critiques", "hypotheses", "candidate_experiments",
                                               "experiments", "decisions", "limitations", "links")},
        "next_action": state["next_action"],
        "errors": state["validation"]["errors"],
        "warnings": state["validation"]["warnings"],
        "snapshot": out.relative_to(ROOT).as_posix(),
        "snapshot_updated": written,
        "inputs_sha256": state["provenance"]["inputs_sha256"],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False), file=sys.stderr if args.print_state else sys.stdout)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
