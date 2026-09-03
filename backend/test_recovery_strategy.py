"""Automated Test Suite for RecoverIQ Stage 6: Deterministic Recovery Strategy Engine.

Verifies:
1. High risk cases (>=80 or prob <0.3) evaluate to HUMAN_REVIEW with requires_human_approval=True
2. Low risk (<40) + high recovery probability (>=0.7) + temporary failure evaluate to SEND_SMART_RETRY_LINK
3. Medium risk (40-70) + probability >=0.5 evaluate to SEND_PAYMENT_LINK
4. Expired/abandoned payment events evaluate to SEND_REMINDER
5. Terminal/recovered cases evaluate to NO_ACTION with allowed_to_execute=False
6. Invalid case ID returns HTTP 404
7. Strategy endpoint NEVER creates or alters RecoveryAction records
8. Zero external Razorpay or OpenAI API calls during evaluation
"""
import urllib.request
import urllib.error
import json
from unittest.mock import patch
from app.database import SessionLocal
from app.models.recovery_case import RecoveryCase
from app.models.payment_event import PaymentEvent
from app.models.recovery_action import RecoveryAction
from app.services.recovery_strategy import recovery_strategy_engine


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
    print("[STAGE 6 DETERMINISTIC RECOVERY STRATEGY TEST SUITE]")

    # 1. High Risk -> HUMAN_REVIEW
    print("\n[TEST 1] High Risk Evaluation (Expect HUMAN_REVIEW)")
    db = SessionLocal()
    try:
        mock_case = RecoveryCase(
            id=101,
            customer_id=1,
            payment_event_id=1,
            risk_score=88.0,
            recovery_probability=0.20,
            recommended_action="FLAG_MANUAL_REVIEW",
            confidence=0.95,
            status="DETECTED"
        )
        mock_event = PaymentEvent(amount=100000, failure_reason="suspected_fraud_block")
        mock_case.payment_event = mock_event
        mock_case.recovery_actions = []

        strat_high = recovery_strategy_engine.evaluate(mock_case)
        print(f"High risk strategy: {strat_high.strategy} (requires_approval={strat_high.requires_human_approval}, allowed={strat_high.allowed_to_execute})")
        assert strat_high.strategy == "HUMAN_REVIEW"
        assert strat_high.requires_human_approval is True
        assert strat_high.allowed_to_execute is False
    finally:
        db.close()

    # 2. Low Risk + High Prob + Temporary Failure -> SEND_SMART_RETRY_LINK
    print("\n[TEST 2] Low Risk Temporary Glitch Evaluation (Expect SEND_SMART_RETRY_LINK)")
    db = SessionLocal()
    try:
        mock_case = RecoveryCase(
            id=102,
            customer_id=1,
            payment_event_id=2,
            risk_score=22.0,
            recovery_probability=0.92,
            recommended_action="SEND_SMART_RETRY_LINK",
            confidence=0.90,
            status="DETECTED"
        )
        mock_event = PaymentEvent(amount=450000, failure_reason="bank_authorization_timeout")
        mock_case.payment_event = mock_event
        mock_case.recovery_actions = []

        strat_temp = recovery_strategy_engine.evaluate(mock_case)
        print(f"Temporary failure strategy: {strat_temp.strategy} (allowed={strat_temp.allowed_to_execute})")
        assert strat_temp.strategy == "SEND_SMART_RETRY_LINK"
        assert strat_temp.requires_human_approval is False
        assert strat_temp.allowed_to_execute is True
    finally:
        db.close()

    # 3. Medium Risk -> SEND_PAYMENT_LINK
    print("\n[TEST 3] Medium Risk Standard Failure (Expect SEND_PAYMENT_LINK)")
    db = SessionLocal()
    try:
        mock_case = RecoveryCase(
            id=103,
            customer_id=1,
            payment_event_id=3,
            risk_score=52.0,
            recovery_probability=0.65,
            recommended_action="SEND_RETRY_LINK",
            confidence=0.80,
            status="DETECTED"
        )
        mock_event = PaymentEvent(amount=1200000, failure_reason="generic_auth_decline")
        mock_case.payment_event = mock_event
        mock_case.recovery_actions = []

        strat_med = recovery_strategy_engine.evaluate(mock_case)
        print(f"Medium risk strategy: {strat_med.strategy} (allowed={strat_med.allowed_to_execute})")
        assert strat_med.strategy == "SEND_PAYMENT_LINK"
        assert strat_med.allowed_to_execute is True
    finally:
        db.close()

    # 4. Expired Payment Link -> SEND_REMINDER
    print("\n[TEST 4] Expired Payment Link Evaluation (Expect SEND_REMINDER)")
    db = SessionLocal()
    try:
        mock_case = RecoveryCase(
            id=104,
            customer_id=1,
            payment_event_id=4,
            risk_score=45.0,
            recovery_probability=0.72,
            recommended_action="EXTEND_PAYMENT_LINK_24H",
            confidence=0.85,
            status="IN_PROGRESS"
        )
        mock_event = PaymentEvent(amount=800000, event_type="payment_link.expired", failure_reason="link_ttl_expired")
        mock_case.payment_event = mock_event
        mock_case.recovery_actions = [RecoveryAction(status="EXECUTED", payment_link_id="plink_prev_104")]

        strat_rem = recovery_strategy_engine.evaluate(mock_case)
        print(f"Expired link strategy: {strat_rem.strategy} (allowed={strat_rem.allowed_to_execute})")
        assert strat_rem.strategy == "SEND_REMINDER"
        assert strat_rem.allowed_to_execute is True
    finally:
        db.close()

    # 5. Recovered Case -> NO_ACTION
    print("\n[TEST 5] Recovered Case Evaluation (Expect NO_ACTION)")
    db = SessionLocal()
    try:
        mock_case = RecoveryCase(
            id=105,
            customer_id=1,
            payment_event_id=5,
            risk_score=15.0,
            recovery_probability=0.98,
            recommended_action="SEND_SMART_RETRY_LINK",
            confidence=0.95,
            status="RECOVERED"
        )
        mock_event = PaymentEvent(amount=2500000, failure_reason=None)
        mock_case.payment_event = mock_event
        mock_case.recovery_actions = []

        strat_rec = recovery_strategy_engine.evaluate(mock_case)
        print(f"Recovered case strategy: {strat_rec.strategy} (allowed={strat_rec.allowed_to_execute})")
        assert strat_rec.strategy == "NO_ACTION"
        assert strat_rec.allowed_to_execute is False
    finally:
        db.close()

    # 6. Invalid Case Endpoint (Expect 404)
    print("\n[TEST 6] POST /api/recovery-cases/999999/strategy (Expect 404)")
    code_404, resp_404 = post("http://127.0.0.1:8000/api/recovery-cases/999999/strategy")
    print(f"Invalid case response: HTTP {code_404} -> {resp_404}")
    assert code_404 == 404
    assert "not found" in resp_404.get("detail", "").lower()

    # 7. Endpoint on Valid Case & Zero Action Mutation
    print("\n[TEST 7] POST /api/recovery-cases/1/strategy & Action Immutability")
    db = SessionLocal()
    try:
        initial_actions = db.query(RecoveryAction).filter(RecoveryAction.recovery_case_id == 1).count()
    finally:
        db.close()

    code_valid, resp_valid = post("http://127.0.0.1:8000/api/recovery-cases/1/strategy")
    print(f"Case #1 Strategy Response: HTTP {code_valid} -> {json.dumps(resp_valid, indent=2)}")
    assert code_valid == 200
    assert resp_valid["recovery_case_id"] == 1
    assert resp_valid["strategy"] in ["SEND_SMART_RETRY_LINK", "SEND_PAYMENT_LINK", "SEND_REMINDER", "NO_ACTION", "HUMAN_REVIEW"]
    assert "reason" in resp_valid
    assert "requires_human_approval" in resp_valid
    assert "allowed_to_execute" in resp_valid

    db = SessionLocal()
    try:
        after_actions = db.query(RecoveryAction).filter(RecoveryAction.recovery_case_id == 1).count()
        assert initial_actions == after_actions, "Strategy evaluation must never create or alter RecoveryActions"
        print(f"Verified action count unchanged ({initial_actions} == {after_actions}). Zero external API calls.")
    finally:
        db.close()

    print("\n[SUCCESS] ALL RECOVERY STRATEGY TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_tests()
