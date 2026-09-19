"""Run a small live evaluation through /chat, using temporary conversation storage.

Run from the project root: python -m scripts.evaluate_financial_aid
This uses the configured Groq API and may use web search. Citation checks verify
that links came from retrieved material; manually review answers for correctness.
"""
import argparse
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import app
from agents import financial_aid
import memory.memory as memory

CASES = [
    ("fafsa", "How do I apply for financial aid at TXST, and what school code goes on my FAFSA?"),
    ("scholarships", "How do continuing TXST students apply for scholarships through BOSS?"),
    ("verification", "I was selected for FAFSA verification. What should I do at TXST?"),
    ("sap", "What undergraduate GPA and completion rate do I need to maintain financial aid at TXST?"),
    ("disbursement", "What requirements must I complete before my financial aid can be disbursed?"),
    ("work_study", "Does receiving a work-study award guarantee me a campus job at TXST?"),
    ("deadline", "What is the FAFSA priority deadline at Texas State?"),
    ("personal_award", "Exactly how much financial aid will I personally receive at TXST this semester?"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--case", choices=[name for name, _ in CASES])
    parser.add_argument("--interval", type=float, default=20, help="Minimum seconds between cases to reduce rate-limit errors")
    args = parser.parse_args()
    results = []
    real_run_tool = financial_aid.run_tool
    with TemporaryDirectory(prefix="txst-evaluation-") as temporary:
        with patch.object(memory, "MEMORY_FILE", Path(temporary) / "sessions.json"), TestClient(app) as client:
            for name, question in CASES:
                if args.case and args.case != name:
                    continue
                contexts = []

                def capture(*call_args, **call_kwargs):
                    context = real_run_tool(*call_args, **call_kwargs)
                    contexts.append(context)
                    return context

                start = monotonic()
                with patch.object(financial_aid, "run_tool", capture):
                    response = client.post("/chat", json={"message": question})
                data = response.json()
                answer = data.get("response", "")
                citations = re.findall(r"\]\((https?://[^\s)]+)\)", answer)
                supplied_sources = re.findall(r"^Source: (https?://\S+)", "\n".join(contexts), re.MULTILINE)
                record = {
                    "case": name, "question": question, "status": response.status_code,
                    "agent": data.get("agent"), "answer": answer,
                    "seconds": round(monotonic() - start, 2),
                    "citations": citations, "supplied_sources": list(dict.fromkeys(supplied_sources)),
                    "citations_from_context": bool(citations) and set(citations).issubset(supplied_sources),
                }
                results.append(record)
                print(json.dumps(record), flush=True)
                if args.output:
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
                if not args.case and name != CASES[-1][0]:
                    sleep(max(0, args.interval - (monotonic() - start)))


if __name__ == "__main__":
    main()
