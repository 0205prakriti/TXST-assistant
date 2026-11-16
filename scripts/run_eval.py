"""Score the assistant against evals/golden.jsonl.

Stages (run from the project root):
  python -m scripts.run_eval --stage retrieval   # offline: needs the Chroma index, no API key
  python -m scripts.run_eval --stage routing     # planner only: agent accuracy + follow-up rewrites
  python -m scripts.run_eval --stage answer      # end to end through chat_service.answer

Filters: --domain FINANCIAL_AID, --type follow_up, --limit 20.
Quality gates (exit code 1 when missed): --min-routing, --min-hit3, --min-facts.
Conversation history is written to a temporary file, never to memory/sessions.json.
"""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from unittest.mock import patch

from evals import metrics

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "evals" / "results"


def search_query(case):
    return case.get("standalone") or case["question"]


def retrieved_urls(query, domain, k):
    from rag.retriever import retrieve_records
    return [r["source"] for r in retrieve_records(query, domain.lower(), n_results=k)]


def eval_retrieval(cases, args):
    rows = []
    for case in cases:
        if case["domain"] == "GENERAL" or not case["expected_sources"] or case["type"] == "adversarial":
            continue
        urls = retrieved_urls(search_query(case), case["domain"], args.k)
        rows.append({
            "id": case["id"], "query": search_query(case), "retrieved": urls,
            "hit@1": metrics.hit_at_k(urls, case["expected_sources"], 1),
            "hit@3": metrics.hit_at_k(urls, case["expected_sources"], 3),
            "rr": metrics.reciprocal_rank(urls, case["expected_sources"]),
        })
    summary = {
        "cases": len(rows),
        "hit@1": metrics.mean([r["hit@1"] for r in rows]),
        "hit@3": metrics.mean([r["hit@3"] for r in rows]),
        f"mrr@{args.k}": metrics.mean([r["rr"] for r in rows]),
    }
    return rows, summary


def eval_routing(cases, args):
    from orchestrator import plan
    rows = []
    for index, case in enumerate(cases):
        start = monotonic()
        decision = plan(case["question"], case.get("history"))
        row = {"id": case["id"], "type": case["type"], "expected": case["domain"],
               "agent": decision["agent"], "confidence": decision["confidence"],
               "query": decision["query"], "tool": decision["tool"],
               "correct": decision["agent"] == case["domain"], "seconds": round(monotonic() - start, 2)}
        if args.with_retrieval and case["expected_sources"] and decision["agent"] != "GENERAL":
            urls = retrieved_urls(decision["query"], decision["agent"], args.k)
            row["rewrite_hit@3"] = metrics.hit_at_k(urls, case["expected_sources"], 3)
        rows.append(row)
        print(json.dumps(row), flush=True)
        _pause(args, start, index, cases)
    follow_ups = [r for r in rows if r["type"] == "follow_up"]
    summary = {
        "cases": len(rows),
        "routing_accuracy": metrics.mean([r["correct"] for r in rows]),
        "follow_up_routing_accuracy": metrics.mean([r["correct"] for r in follow_ups]),
        "rewrite_hit@3": metrics.mean([r.get("rewrite_hit@3") for r in rows]),
        "follow_up_rewrite_hit@3": metrics.mean([r.get("rewrite_hit@3") for r in follow_ups]),
        "confusions": dict(Counter(f"{r['expected']}->{r['agent']}" for r in rows if not r["correct"])),
        "p50_seconds": _percentile([r["seconds"] for r in rows], 50),
    }
    return rows, summary


def eval_answers(cases, args):
    import chat_service
    import memory.memory as memory
    from agents import financial_aid, generative

    rows = []
    with TemporaryDirectory(prefix="txst-eval-") as temporary:
        with patch.object(memory, "MEMORY_FILE", Path(temporary) / "sessions.json"):
            for index, case in enumerate(cases):
                contexts = []

                def capture(real):
                    def wrapper(*a, **kw):
                        context = real(*a, **kw)
                        contexts.append(context)
                        return context
                    return wrapper

                session_id = f"eval-{case['id']}"
                if case.get("history"):
                    memory.save_history(list(case["history"]), session_id)
                start = monotonic()
                with patch.object(generative, "run_tool", capture(generative.run_tool)), \
                        patch.object(financial_aid, "run_tool", capture(financial_aid.run_tool)):
                    result = chat_service.answer(case["question"], session_id)
                answer = result["response"]
                supplied = [line[len("Source: "):].strip() for context in contexts
                            for line in context.splitlines() if line.startswith("Source: ")]
                cited = metrics.citations(answer)
                row = {
                    "id": case["id"], "type": case["type"], "question": case["question"],
                    "expected_agent": case["domain"], "agent": result["agent"],
                    "agent_correct": result["agent"] == case["domain"], "query": result.get("query"),
                    "answer": answer, "citations": cited,
                    "facts": metrics.facts_present(answer, case["must_include"]),
                    "citations_grounded": metrics.citations_grounded(answer, supplied),
                    "cites_expected_source": (any(metrics.source_matches(u, case["expected_sources"]) for u in cited)
                                              if case["expected_sources"] and case["type"] in ("single", "follow_up")
                                              else None),
                    "fallback": metrics.is_fallback(answer),
                    "seconds": round(monotonic() - start, 2),
                }
                if case["type"] == "personal":
                    row["discloses_no_access"] = metrics.discloses_no_access(answer)
                rows.append(row)
                print(json.dumps(row, ensure_ascii=False), flush=True)
                _pause(args, start, index, cases)
    answerable = [r for r in rows if r["type"] in ("single", "follow_up")]
    summary = {
        "cases": len(rows),
        "routing_accuracy": metrics.mean([r["agent_correct"] for r in rows]),
        "fact_recall": metrics.mean([r["facts"] for r in rows]),
        "citation_grounded_rate": metrics.mean([r["citations_grounded"] for r in rows]),
        "cites_expected_source": metrics.mean([r["cites_expected_source"] for r in rows]),
        "fallback_rate_answerable": metrics.mean([r["fallback"] for r in answerable]),
        "personal_disclosure_rate": metrics.mean([r.get("discloses_no_access") for r in rows]),
        "p50_seconds": _percentile([r["seconds"] for r in rows], 50),
        "p95_seconds": _percentile([r["seconds"] for r in rows], 95),
    }
    return rows, summary


def _pause(args, start, index, cases):
    if args.interval and index < len(cases) - 1:
        sleep(max(0.0, args.interval - (monotonic() - start)))


def _percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1)))]


def check_gates(summary, args):
    failures = []
    gates = [("routing_accuracy", args.min_routing), ("hit@3", args.min_hit3), ("fact_recall", args.min_facts)]
    for key, minimum in gates:
        if minimum is not None and summary.get(key) is not None and summary[key] < minimum:
            failures.append(f"{key} {summary[key]} < {minimum}")
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", choices=["retrieval", "routing", "answer"], required=True)
    parser.add_argument("--domain", choices=["ACADEMICS", "CAMPUS", "FINANCIAL_AID", "GENERAL"])
    parser.add_argument("--type", dest="case_type")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--k", type=int, default=5, help="Chunks retrieved per query for retrieval metrics")
    parser.add_argument("--interval", type=float, default=0.0, help="Minimum seconds per case (rate limits)")
    parser.add_argument("--with-retrieval", action="store_true", help="Routing stage: also score rewritten queries")
    parser.add_argument("--min-routing", type=float)
    parser.add_argument("--min-hit3", type=float)
    parser.add_argument("--min-facts", type=float)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    cases = metrics.load_cases(domain=args.domain, case_type=args.case_type)[: args.limit]
    stage = {"retrieval": eval_retrieval, "routing": eval_routing, "answer": eval_answers}[args.stage]
    rows, summary = stage(cases, args)

    output = args.output or RESULTS_DIR / f"{args.stage}-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"stage": args.stage, "summary": summary, "rows": rows}, indent=2,
                                 ensure_ascii=False) + "\n", encoding="utf-8")
    print("\nSUMMARY " + json.dumps(summary, indent=2))
    print(f"Report: {output}")
    failures = check_gates(summary, args)
    if failures:
        print("Quality gate failed: " + "; ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
