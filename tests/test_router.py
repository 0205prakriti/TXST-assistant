"""Live routing checks: these call the configured model and need GROQ_API_KEY."""
import os

import pytest

from orchestrator import route

pytestmark = pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="live model test; set GROQ_API_KEY")

def test_routes_academics():
    result = route("When is the last day to drop a class?")
    assert result["agent"] == "ACADEMICS"
    assert result["confidence"] > 0.6

def test_routes_campus():
    result = route("Where is the dining hall?")
    assert result["agent"] == "CAMPUS"
    assert result["confidence"] > 0.6

def test_routes_financial_aid():
    result = route("How do I apply for FAFSA?")
    assert result["agent"] == "FINANCIAL_AID"
    assert result["confidence"] > 0.6

def test_low_confidence_returns_valid_structure():
    result = route("asdfghjkl random gibberish")
    assert "agent" in result
    assert "confidence" in result

def test_follow_up_uses_conversation():
    history = [{"role": "user", "content": "Where do commuter students park at TXST?"},
               {"role": "assistant", "content": "Commuter parking is on the perimeter of campus."}]
    assert route("How do I get from there to central campus?", history)["agent"] == "CAMPUS"
