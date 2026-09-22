"""Run the agent on a tender PDF:  python -m tender_agent.cli data/tenders/sample.pdf"""
import argparse
import uuid

from langgraph.types import Command

from .graph import build_graph

ICON = {"PASS": "✅", "FAIL": "❌", "UNKNOWN": "❔"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--auto-approve", action="store_true", help="accept the AI decision without prompting")
    args = ap.parse_args()

    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    result = graph.invoke({"pdf_path": args.pdf}, config)

    for err in result.get("errors", []):
        print(f"⚠️  {err}")
        if "__interrupt__" not in result:
            if result.get("errors"):
                print("Stopped early: extraction failed — see errors above.")
            else:
                print("Stopped early: document did not look like a tender.")
            return

    info = result["__interrupt__"][0].value
    print(f"\n📄 {info['tender_title']}\n")
    for c in info["checks"]:
        print(f"  {ICON[c['status']]} {c['name']:<15} {c['detail']}")
    print(f"\n🤖 AI decision: {info['decision']}  (score {info['score']}/100)\n{info['rationale']}\n")

    if args.auto_approve:
        final, notes = info["decision"], "auto-approved"
    else:
        final = input(f"Final decision [BID/REVIEW/NO-BID] (Enter = {info['decision']}): ").strip().upper() or info["decision"]
        notes = input("Notes (optional): ").strip()

    result = graph.invoke(Command(resume={"final_decision": final, "notes": notes}), config)
    print(f"\n📊 Report saved: {result['report_path']}")


if __name__ == "__main__":
    main()
