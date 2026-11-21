import json

import chat_service
import orchestrator
from agents import financial_aid, generative
from tools import tool_runner


def test_parse_plan_accepts_valid_plan():
    raw = json.dumps({"agent": "CAMPUS", "confidence": 0.92, "standalone_query": "LBJ hours Friday", "tool": "search_knowledge_base"})
    assert orchestrator.parse_plan(raw, "and friday?") == {
        "agent": "CAMPUS", "confidence": 0.92, "query": "LBJ hours Friday", "tool": "search_knowledge_base"}


def test_parse_plan_invalid_json_falls_back_safely():
    assert orchestrator.parse_plan("not json", "hello") == {
        "agent": "GENERAL", "confidence": 0.5, "query": "hello", "tool": "none"}


def test_parse_plan_unknown_agent_lowers_confidence_and_disables_tools():
    result = orchestrator.parse_plan(json.dumps({"agent": "SPORTS", "confidence": 0.99, "tool": "search_web"}), "q")
    assert result["agent"] == "GENERAL" and result["confidence"] <= 0.5 and result["tool"] == "none"


def test_parse_plan_repairs_missing_query_tool_and_bad_confidence():
    result = orchestrator.parse_plan(json.dumps({"agent": "ACADEMICS", "confidence": "high", "tool": "none"}), "drop deadline?")
    assert result == {"agent": "ACADEMICS", "confidence": 0.0, "query": "drop deadline?", "tool": "search_knowledge_base"}


def test_plan_sends_truncated_history_to_one_json_call(monkeypatch):
    calls = []

    def fake_chat(messages, system="", json_mode=False, model=None, reasoning_effort=None):
        calls.append({"messages": messages, "json_mode": json_mode, "model": model})
        return json.dumps({"agent": "ACADEMICS", "confidence": 0.9,
                           "standalone_query": "TXST last day to withdraw spring 2026", "tool": "search_knowledge_base"})

    monkeypatch.setattr(orchestrator, "chat", fake_chat)
    history = [{"role": "user", "content": "old"}] * 10 + [
        {"role": "user", "content": "When is the last day to withdraw in fall 2026?"},
        {"role": "assistant", "content": "x" * 5000},
    ]
    result = orchestrator.plan("And spring?", history)
    assert len(calls) == 1 and calls[0]["json_mode"] and calls[0]["model"] == orchestrator.PLANNER_MODEL
    payload = json.loads(calls[0]["messages"][0]["content"])
    assert payload["latest_message"] == "And spring?"
    assert len(payload["conversation"]) == orchestrator.HISTORY_TURNS
    assert payload["conversation"][-2]["content"].startswith("When is the last day to withdraw")
    assert len(payload["conversation"][-1]["content"]) <= orchestrator.HISTORY_CHARS + 1
    assert result["query"] == "TXST last day to withdraw spring 2026"


def test_route_keeps_backward_compatible_shape(monkeypatch):
    monkeypatch.setattr(orchestrator, "chat", lambda **_: json.dumps({"agent": "FINANCIAL_AID", "confidence": 0.8}))
    assert orchestrator.route("FAFSA?") == {"agent": "FINANCIAL_AID", "confidence": 0.8}


def test_tool_runner_dispatches_without_model_calls(monkeypatch):
    seen = {}
    monkeypatch.setattr(tool_runner, "retrieve", lambda q, collection_name, n_results: seen.setdefault("kb", (q, collection_name)) and "kb")
    monkeypatch.setattr(tool_runner, "search_web", lambda q: seen.setdefault("web", q) and "web")
    tool_runner.run_tool("parking", "campus")
    tool_runner.run_tool("event", "campus", tool="search_web")
    assert tool_runner.run_tool("hi", "general", tool="none") == ""
    assert seen["kb"] == ("parking", "campus")
    assert seen["web"].startswith("site:txst.edu") and seen["web"].endswith("event")


def test_generative_agent_searches_with_standalone_query(monkeypatch):
    searched = []
    monkeypatch.setattr(generative, "run_tool", lambda q, agent_type, tool: searched.append((q, agent_type, tool)) or "Source: https://x\nfact")
    monkeypatch.setattr(generative, "chat", lambda messages, system: messages[-1]["content"])
    plan = {"query": "LBJ Student Center hours Friday", "tool": "search_knowledge_base"}
    from agents import campus
    assert campus.run("and fridays?", [], plan=plan) == "and fridays?"
    assert searched == [("LBJ Student Center hours Friday", "campus", "search_knowledge_base")]


def test_financial_aid_selects_passages_for_standalone_query(monkeypatch):
    monkeypatch.setattr(financial_aid, "run_tool", lambda q, agent_type, tool: "context")
    seen = {}
    monkeypatch.setattr(financial_aid, "grounded_answer", lambda q, c, h: seen.setdefault("q", q))
    financial_aid.run("and for master's?", [], plan={"query": "SAP GPA for master's students", "tool": "search_knowledge_base"})
    assert seen["q"] == "SAP GPA for master's students"


def test_chat_service_plans_with_history_and_passes_plan(monkeypatch, tmp_path):
    import memory.memory as memory
    monkeypatch.setattr(memory, "MEMORY_FILE", tmp_path / "sessions.json")
    memory.save_history([{"role": "user", "content": "Where do commuters park?"},
                         {"role": "assistant", "content": "Perimeter lots."}], "s1")
    seen = {}

    def fake_plan(message, history):
        seen["history"] = history
        return {"agent": "CAMPUS", "confidence": 0.9, "query": "perimeter lots to central campus", "tool": "search_knowledge_base"}

    def fake_run(message, history, plan):
        seen["plan"] = plan
        return "Take the Bobcat Shuttle."

    monkeypatch.setattr(chat_service, "plan", fake_plan)
    monkeypatch.setattr(chat_service.campus, "run", fake_run)
    result = chat_service.answer("How do I get to class from there?", "s1")
    assert seen["history"][0]["content"] == "Where do commuters park?"
    assert seen["plan"]["query"] == "perimeter lots to central campus"
    assert result["response"] == "Take the Bobcat Shuttle." and len(memory.load_history("s1")) == 4


def test_low_confidence_asks_for_clarification_but_general_does_not(monkeypatch, tmp_path):
    import memory.memory as memory
    monkeypatch.setattr(memory, "MEMORY_FILE", tmp_path / "sessions.json")
    monkeypatch.setattr(chat_service, "plan", lambda m, h: {"agent": "CAMPUS", "confidence": 0.4, "query": m, "tool": "search_knowledge_base"})
    assert chat_service.answer("hours?")["response"] == chat_service.CLARIFY
    monkeypatch.setattr(chat_service, "plan", lambda m, h: {"agent": "GENERAL", "confidence": 0.4, "query": m, "tool": "none"})
    monkeypatch.setattr(chat_service.general, "run", lambda m, h, plan: "Hi there!")
    assert chat_service.answer("hey")["response"] == "Hi there!"
