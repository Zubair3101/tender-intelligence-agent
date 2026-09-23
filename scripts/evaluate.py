"""Run the agent over the ground-truth set and report accuracy metrics.

    python scripts/evaluate.py data/eval/ground_truth.yaml
"""
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tender_agent.config import settings                       # noqa: E402
from tender_agent.eval.metrics import aggregate, combine, evaluate_fields  # noqa: E402
from tender_agent.observability import setup_tracing           # noqa: E402
from tender_agent.pipeline import run_pipeline                 # noqa: E402


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/eval/ground_truth.yaml"
    cases = yaml.safe_load(open(path, encoding="utf-8"))
    print(f"LangSmith tracing: {'on' if setup_tracing() else 'off'}\n")

    per_doc = []
    for case in cases:
        name = os.path.basename(case["pdf"])
        print(f"▶ {name}")
        state = run_pipeline(case["pdf"])
        rows = evaluate_fields(state.get("requirements", {}), case["fields"])
        metrics = aggregate(rows)
        per_doc.append({"document": name, "metrics": metrics, "rows": rows,
                        "decision": state.get("decision"),
                        "expected_decision": case.get("expected_decision"),
                        "timings": state.get("timings", {}), "errors": state.get("errors", [])})
        print(f"   coverage {metrics['coverage_pct']}% | accuracy {metrics['accuracy_pct']}% | "
              f"grounded {metrics['grounding_pct']}% | decision {state.get('decision')} "
              f"(expected {case.get('expected_decision')})")
        for r in rows:
            if not r["correct"]:
                print(f"   ✗ {r['field']}: got {r['predicted']!r}, expected {r['expected']!r}")

    overall = combine(per_doc)
    os.makedirs(settings.output_dir, exist_ok=True)
    out = os.path.join(settings.output_dir, "eval_results.json")
    json.dump({"overall": overall, "documents": per_doc}, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print("\n=== OVERALL ===")
    for k, v in overall.items():
        print(f"{k:24} {v}")
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
