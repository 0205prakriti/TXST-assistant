from orchestrator import route

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