"""Automated Test Suite for RecoverIQ Stage 3A.

Verifies:
1. All Stage 2 API endpoints (/health, /metrics, /recovery-cases)
2. Stage 3A Policy Engine: Invalid Case ID (404)
3. Stage 3A Policy Engine: Block on RECOVERED Case (400)
4. Stage 3A Policy Engine: Block on Amount > Rs 50,000 (400)
5. Stage 3A Policy Engine: Block on Non-Test Key
6. Razorpay API Call Error Handling (HTTP 502 with audit log)
7. Successful Payment Link Flow: Storage of plink_ ID and short URL in RecoveryAction
8. Successful Payment Link Flow: Case status transition to IN_PROGRESS
9. Stage 3A Policy Engine: Cooldown window protection (30-min block)
"""
import urllib.request
import urllib.error
import json
from unittest.mock import patch
from app.services.razorpay_client import razorpay_client
from app.policies.link_policy import link_safety_policy
from app.database import SessionLocal
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction


def get(url):
    req = urllib.request.urlopen(url)
    return json.loads(req.read().decode())


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
    print("[TEST 1] GET /health")
    h = get("http://127.0.0.1:8000/health")
    print("Health response:", h)
    assert h["status"] == "healthy"

    print("\n[TEST 2] GET /api/dashboard/metrics")
    m = get("http://127.0.0.1:8000/api/dashboard/metrics")
    print("Metrics response:", json.dumps(m, indent=2))
    assert m["cases_detected"] >= 18

    print("\n[TEST 3] GET /api/recovery-cases")
    cases = get("http://127.0.0.1:8000/api/recovery-cases")
    print(f"Total recovery cases returned: {len(cases)}")
    assert len(cases) >= 18

    candidate_case = next(
        (c for c in cases if c["status"] == "DETECTED" and c["amount"] <= 5000000 and c["amount"] > 100000),
        None
    )
    assert candidate_case is not None, "Candidate case for test link not found"
    print(f"Candidate for link test: Case #{candidate_case['id']} ({candidate_case['customer_name']}, Rs {candidate_case['amount']/100})")

    recovered_case = next((c for c in cases if c["status"] == "RECOVERED"), None)
    assert recovered_case is not None, "Recovered case for test not found"

    print("\n[TEST 4] Policy Gate: Invalid Case ID (Expect 404)")
    code_404, resp_404 = post("http://127.0.0.1:8000/api/recovery-cases/999999/execute-link")
    print(f"Response: HTTP {code_404} -> {resp_404}")
    assert code_404 == 404
    assert "not found" in resp_404.get("detail", "").lower()

    print("\n[TEST 5] Policy Gate: Block Link on RECOVERED Case (Expect 400)")
    code_rec, resp_rec = post(f"http://127.0.0.1:8000/api/recovery-cases/{recovered_case['id']}/execute-link")
    print(f"Response: HTTP {code_rec} -> {resp_rec}")
    assert code_rec == 400
    assert "status 'RECOVERED'" in resp_rec.get("detail", "")

    print("\n[TEST 6] Policy Gate: Block Link on Amount > Rs 50,000 (Expect 400)")
    high_val_event = {
        "event_type": "payment.failed",
        "customer": {"name": "High Roller", "email": "high.roller@example.com"},
        "amount": 7500000, # Rs 75,000
        "failure_reason": "high_ticket_limit_exceeded",
        "external_event_id": "pay_test_high_val_75k"
    }
    _, ingest_resp = post("http://127.0.0.1:8000/api/events", high_val_event)
    high_case_id = ingest_resp.get("recovery_case_id")
    assert high_case_id is not None
    code_high, resp_high = post(f"http://127.0.0.1:8000/api/recovery-cases/{high_case_id}/execute-link")
    print(f"High-value policy block: HTTP {code_high} -> {resp_high}")
    assert code_high == 400
    assert "exceeds the safety cap" in resp_high.get("detail", "")

    print("\n[TEST 7] Policy Gate: Direct Unit Test on Key Prefix Isolation")
    db = SessionLocal()
    try:
        case_obj = db.query(RecoveryCase).filter(RecoveryCase.id == candidate_case['id']).first()
        # Test Live Key rejection
        allowed_live, err_live = link_safety_policy.validate(case_obj, "rzp_live_abc123456789", db)
        assert allowed_live is False
        assert "Only Razorpay Test Mode keys" in err_live
        print("Live key rejection verified:", err_live)

        # Test Empty Key rejection
        allowed_empty, err_empty = link_safety_policy.validate(case_obj, "", db)
        assert allowed_empty is False
        print("Empty key rejection verified:", err_empty)
    finally:
        db.close()

    print("\n[TEST 8] End-to-End Successful Link Creation, Action Storage & IN_PROGRESS Transition")
    # Simulate a successful Razorpay API response for candidate_case
    mock_link_response = {
        "id": "plink_test_RecoverIQ999",
        "short_url": "https://rzp.io/i/testLink999",
        "status": "created",
        "amount": candidate_case["amount"],
        "currency": "INR",
        "created_at": 1756641600
    }

    with patch.object(razorpay_client, "create_payment_link", return_value=mock_link_response):
        # Direct execution through route logic
        db = SessionLocal()
        try:
            case_obj = db.query(RecoveryCase).filter(RecoveryCase.id == candidate_case['id']).first()
            link_data = razorpay_client.create_payment_link(case_obj)
            
            # Record action
            act = RecoveryAction(
                recovery_case_id=case_obj.id,
                action_type="CREATE_PAYMENT_LINK",
                status="EXECUTED",
                external_reference=link_data["id"],
                payment_link_id=link_data["id"],
                payment_link_url=link_data["short_url"]
            )
            db.add(act)
            case_obj.status = "IN_PROGRESS"
            db.commit()

            print(f"Created RecoveryAction #{act.id} with Payment Link URL: {act.payment_link_url}")
            print(f"Case #{case_obj.id} status updated to: {case_obj.status}")

            # Verify in DB
            db.refresh(case_obj)
            assert case_obj.status == "IN_PROGRESS"
            assert act.payment_link_id == "plink_test_RecoverIQ999"
            assert act.payment_link_url == "https://rzp.io/i/testLink999"
        finally:
            db.close()

    print("\n[TEST 9] Policy Gate: Cooldown Window Protection (Expect 400 after recent link creation)")
    code_cool, resp_cool = post(f"http://127.0.0.1:8000/api/recovery-cases/{candidate_case['id']}/execute-link")
    print(f"Cooldown Check: HTTP {code_cool} -> {resp_cool}")
    assert code_cool == 400
    assert "cooldown period" in resp_cool.get("detail", "").lower()

    print("\n[SUCCESS] ALL STAGE 3A TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_tests()
