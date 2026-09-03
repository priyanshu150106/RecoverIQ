"""Automated Test Suite for RecoverIQ Stage 4: AI Recovery Agent.

Verifies:
1. Valid structured AI response generation and parsing
2. Invalid recovery probability rejected (< 0.0 or > 1.0)
3. Invalid confidence score rejected (< 0.0 or > 1.0)
4. Invalid urgency value rejected
5. Invalid policy recommendation rejected
6. Missing OPENAI_API_KEY fallback to deterministic scoring
7. Simulated OpenAI API failure fallback
8. Malformed JSON AI response fallback
9. AI endpoint returns HTTP 404 on invalid case ID
10. AI endpoint generates structured recommendation on valid case
11. AI endpoint NEVER executes Razorpay actions (RecoveryAction count unchanged)
"""
import json
import urllib.request
import urllib.error
from unittest.mock import MagicMock, patch
from pydantic import ValidationError
from app.config import settings
from app.database import SessionLocal
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.schemas.ai_recommendation import (
    AIRecoveryRecommendation,
    AIRecoveryRecommendationResponse,
)
from app.ai.recovery_agent import AIRecoveryAgent, ai_recovery_agent


def post(url, data=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data or {}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        res = urllib.request.urlopen(req)
        return res.getcode(), json.loads(res.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"detail": body}
        return e.code, parsed


def run_tests():
    print("[STAGE 4 AI RECOVERY AGENT TEST SUITE]")

    # 1. Valid Structured AI Recommendation Schema
    print("\n[TEST 1] Valid Structured AI Response Validation")
    valid_payload = {
        "recovery_probability": 0.91,
        "recommended_action": "SEND_SMART_RETRY_LINK",
        "urgency": "HIGH",
        "confidence": 0.89,
        "reasoning": "Customer has a strong payment history and this failure appears to be a temporary bank network glitch.",
        "signals": [
            "7 previous successful transactions",
            "High historical payment value",
            "Recent bank timeout failure"
        ],
        "policy_recommendation": "ALLOW"
    }
    validated = AIRecoveryRecommendation.model_validate(valid_payload)
    assert validated.recovery_probability == 0.91
    assert validated.urgency == "HIGH"
    assert validated.policy_recommendation == "ALLOW"
    print("Valid structured recommendation parsed successfully.")

    # 2. Invalid Probability Rejected
    print("\n[TEST 2] Invalid Recovery Probability Rejected (<0 or >1)")
    try:
        AIRecoveryRecommendation.model_validate({**valid_payload, "recovery_probability": 1.5})
        assert False, "Should have raised ValidationError for probability > 1.0"
    except ValidationError:
        print("Probability 1.5 correctly rejected by Pydantic.")

    try:
        AIRecoveryRecommendation.model_validate({**valid_payload, "recovery_probability": -0.1})
        assert False, "Should have raised ValidationError for probability < 0.0"
    except ValidationError:
        print("Probability -0.1 correctly rejected by Pydantic.")

    # 3. Invalid Confidence Rejected
    print("\n[TEST 3] Invalid Confidence Rejected (<0 or >1)")
    try:
        AIRecoveryRecommendation.model_validate({**valid_payload, "confidence": 1.2})
        assert False, "Should have raised ValidationError for confidence > 1.0"
    except ValidationError:
        print("Confidence 1.2 correctly rejected by Pydantic.")

    # 4. Invalid Urgency Rejected
    print("\n[TEST 4] Invalid Urgency Rejected (Must be LOW | MEDIUM | HIGH)")
    try:
        AIRecoveryRecommendation.model_validate({**valid_payload, "urgency": "CRITICAL"})
        assert False, "Should have raised ValidationError for invalid urgency"
    except ValidationError:
        print("Invalid urgency 'CRITICAL' correctly rejected by Pydantic.")

    # 5. Invalid Policy Decision Rejected
    print("\n[TEST 5] Invalid Policy Decision Rejected (Must be ALLOW | BLOCK | REVIEW)")
    try:
        AIRecoveryRecommendation.model_validate({**valid_payload, "policy_recommendation": "EXECUTE_NOW"})
        assert False, "Should have raised ValidationError for invalid policy recommendation"
    except ValidationError:
        print("Invalid policy decision 'EXECUTE_NOW' correctly rejected by Pydantic.")

    # 6. Missing OPENAI_API_KEY Fallback
    print("\n[TEST 6] Missing OPENAI_API_KEY Fallback to Deterministic Scoring")
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).first()
        assert case is not None, "No recovery case in database"

        with patch.object(settings, "OPENAI_API_KEY", None):
            res_fallback = ai_recovery_agent.generate_recommendation(case=case)
            assert res_fallback.source == "fallback"
            assert res_fallback.recommendation.recovery_probability == case.recovery_probability
            assert res_fallback.recommendation.recommended_action == case.recommended_action
            print(f"Fallback verified: source='{res_fallback.source}', action='{res_fallback.recommendation.recommended_action}'")
    finally:
        db.close()

    # 7. Simulated OpenAI API Failure Fallback
    print("\n[TEST 7] Simulated OpenAI API Failure Fallback")
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).first()
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API rate limit / 500 error")

        with patch.object(settings, "OPENAI_API_KEY", "dummy_key"):
            res_error = ai_recovery_agent.generate_recommendation(case=case, client=mock_client)
            assert res_error.source == "fallback"
            print(f"API Error handled safely: fallback triggered (source='{res_error.source}')")
    finally:
        db.close()

    # 8. Malformed AI JSON Response Fallback
    print("\n[TEST 8] Malformed AI JSON Response Fallback")
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).first()
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "{ malformed json without closing brace"
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        with patch.object(settings, "OPENAI_API_KEY", "dummy_key"):
            res_malformed = ai_recovery_agent.generate_recommendation(case=case, client=mock_client)
            assert res_malformed.source == "fallback"
            print("Malformed JSON gracefully fell back to deterministic engine.")
    finally:
        db.close()

    # 9. AI Endpoint 404 on Invalid Case ID
    print("\n[TEST 9] AI Endpoint Invalid Case ID (Expect 404)")
    code_404, resp_404 = post("http://127.0.0.1:8000/api/recovery-cases/999999/ai-recommendation")
    print(f"Invalid case response: HTTP {code_404} -> {resp_404}")
    assert code_404 == 404
    assert "not found" in resp_404.get("detail", "").lower()

    # 10. AI Endpoint on Valid Case & Source Flag
    print("\n[TEST 10] AI Endpoint Valid Case")
    db = SessionLocal()
    try:
        case = db.query(RecoveryCase).first()
        case_id = case.id
        initial_action_count = db.query(RecoveryAction).filter(RecoveryAction.recovery_case_id == case_id).count()
    finally:
        db.close()

    code_valid, resp_valid = post(f"http://127.0.0.1:8000/api/recovery-cases/{case_id}/ai-recommendation")
    print(f"AI endpoint response: HTTP {code_valid} -> {json.dumps(resp_valid, indent=2)}")
    assert code_valid == 200
    assert resp_valid["status"] == "success"
    assert resp_valid["recovery_case_id"] == case_id
    assert resp_valid["source"] in ["ai", "fallback"]
    assert "recommendation" in resp_valid
    assert "recovery_probability" in resp_valid["recommendation"]
    assert "urgency" in resp_valid["recommendation"]
    assert "signals" in resp_valid["recommendation"]
    assert len(resp_valid["recommendation"]["signals"]) >= 1

    # 11. Verify AI Endpoint NEVER executes Razorpay actions
    print("\n[TEST 11] Verify AI Endpoint Never Executes Razorpay Actions")
    db = SessionLocal()
    try:
        after_action_count = db.query(RecoveryAction).filter(RecoveryAction.recovery_case_id == case_id).count()
        assert after_action_count == initial_action_count, "AI Endpoint must never create or execute financial actions"
        print(f"RecoveryAction count verified unchanged ({initial_action_count} -> {after_action_count}). Zero Razorpay API calls.")
    finally:
        db.close()

    print("\n[SUCCESS] ALL STAGE 4 AI AGENT TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_tests()
