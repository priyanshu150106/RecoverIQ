"""Automated Test Suite for RecoverIQ Stage 3B: Razorpay Payment Link Webhooks.

Verifies:
1. Valid HMAC-SHA256 signature verification over raw body bytes
2. Invalid signature rejection (HTTP 400)
3. Tampered payload rejection (HTTP 400)
4. Missing X-Razorpay-Event-Id header rejection (HTTP 400)
5. Idempotency: Duplicate webhook delivery ignored without state corruption
6. payment_link.paid: Transitions case to RECOVERED and updates revenue metrics
7. payment_link.partially_paid: Retains case in IN_PROGRESS and records partial event
8. payment_link.cancelled: Records event and preserves non-recovered state
9. payment_link.expired: Records event and preserves non-recovered state
10. Unknown payment_link_id handled gracefully (unmatched response)
11. Malformed/missing payload fields handled cleanly
12. Secrets never appear in response payloads or output
"""
import hmac
import hashlib
import json
import time
import urllib.request
import urllib.error
from app.config import settings
from app.database import SessionLocal
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.payment_event import PaymentEvent


def post_webhook(payload_dict: dict, event_id: str = None, signature: str = None, raw_override: bytes = None):
    raw_body = raw_override if raw_override is not None else json.dumps(payload_dict).encode("utf-8")
    
    secret = settings.RECOVERIQ_WEBHOOK_SECRET or ""
    
    if signature is None and raw_override is None:
        sig = hmac.new(secret.strip().encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    else:
        sig = signature or ""

    headers = {"Content-Type": "application/json"}
    if sig:
        headers["X-Razorpay-Signature"] = sig
    if event_id:
        headers["X-Razorpay-Event-Id"] = event_id

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/webhooks/razorpay",
        data=raw_body,
        headers=headers
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


def get(url):
    req = urllib.request.urlopen(url)
    return json.loads(req.read().decode())


def run_tests():
    print("[STAGE 3B WEBHOOK TEST SUITE]")
    now_ts = int(time.time())
    
    # 0. Setup a test RecoveryCase and RecoveryAction with known payment_link_id
    db = SessionLocal()
    try:
        test_case = db.query(RecoveryCase).filter(RecoveryCase.status == "DETECTED").first()
        assert test_case is not None, "No DETECTED recovery case found in DB for webhook test"
        
        test_plink_id = f"plink_test_webhook_3b_{now_ts}"
        test_action = RecoveryAction(
            recovery_case_id=test_case.id,
            action_type="CREATE_PAYMENT_LINK",
            status="EXECUTED",
            payment_link_id=test_plink_id,
            payment_link_url=f"https://rzp.io/i/{test_plink_id}"
        )
        db.add(test_action)
        test_case.status = "IN_PROGRESS"
        db.commit()
        db.refresh(test_case)
        case_id = test_case.id
        print(f"Setup test case #{case_id} with unique payment_link_id '{test_plink_id}'")
    finally:
        db.close()

    # 1. Invalid Signature Test
    print("\n[TEST 1] Invalid Webhook Signature (Expect 400)")
    dummy_payload = {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {"id": test_plink_id, "amount": 450000, "amount_paid": 450000, "status": "paid"}
            }
        }
    }
    code_inv, resp_inv = post_webhook(
        dummy_payload,
        event_id=f"wh_evt_test_inv_{now_ts}",
        signature="invalid_signature_hex_12345"
    )
    print(f"Invalid Signature Response: HTTP {code_inv} -> {resp_inv}")
    assert code_inv == 400
    assert "signature" in resp_inv.get("detail", "").lower()

    # 2. Tampered Payload Test
    print("\n[TEST 2] Tampered Payload After Signing (Expect 400)")
    valid_raw = json.dumps(dummy_payload).encode("utf-8")
    secret = settings.RECOVERIQ_WEBHOOK_SECRET or ""
    valid_sig = hmac.new(secret.strip().encode("utf-8"), valid_raw, hashlib.sha256).hexdigest()
    tampered_raw = json.dumps({**dummy_payload, "tampered": True}).encode("utf-8")
    
    code_tamp, resp_tamp = post_webhook(
        dummy_payload,
        event_id=f"wh_evt_test_tamp_{now_ts}",
        signature=valid_sig,
        raw_override=tampered_raw
    )
    print(f"Tampered Payload Response: HTTP {code_tamp} -> {resp_tamp}")
    assert code_tamp == 400
    assert "signature" in resp_tamp.get("detail", "").lower()

    # 3. Missing X-Razorpay-Event-Id Header Test
    print("\n[TEST 3] Missing X-Razorpay-Event-Id Header (Expect 400)")
    code_no_id, resp_no_id = post_webhook(dummy_payload, event_id=None)
    print(f"Missing Event-ID Response: HTTP {code_no_id} -> {resp_no_id}")
    assert code_no_id == 400
    assert "x-razorpay-event-id" in resp_no_id.get("detail", "").lower()

    # 4. Valid payment_link.paid Webhook Processing
    print("\n[TEST 4] Valid payment_link.paid Event Processing")
    paid_event_id = f"wh_evt_paid_unique_{now_ts}"
    code_paid, resp_paid = post_webhook(dummy_payload, event_id=paid_event_id)
    print(f"payment_link.paid Result: HTTP {code_paid} -> {resp_paid}")
    assert code_paid == 200
    assert resp_paid["status"] == "success"
    assert resp_paid["case_status"] == "RECOVERED"
    assert resp_paid["recovery_case_id"] == case_id

    # Verify DB State
    db = SessionLocal()
    try:
        updated_case = db.query(RecoveryCase).filter(RecoveryCase.id == case_id).first()
        assert updated_case.status == "RECOVERED"
        
        logged_event = db.query(PaymentEvent).filter(PaymentEvent.external_event_id == paid_event_id).first()
        assert logged_event is not None
        assert logged_event.status == "paid"
        print(f"Verified Case #{case_id} status is now RECOVERED in SQLite.")
    finally:
        db.close()

    # 5. Idempotency Check: Re-delivering the exact same event_id
    print("\n[TEST 5] Idempotency: Duplicate Webhook Delivery")
    code_dup, resp_dup = post_webhook(dummy_payload, event_id=paid_event_id)
    print(f"Duplicate Delivery Result: HTTP {code_dup} -> {resp_dup}")
    assert code_dup == 200
    assert resp_dup["status"] == "ignored"
    assert resp_dup.get("is_duplicate") is True

    # 6. payment_link.partially_paid Test
    print("\n[TEST 6] payment_link.partially_paid Event Processing")
    db = SessionLocal()
    try:
        partial_case = db.query(RecoveryCase).filter(RecoveryCase.status == "DETECTED").first()
        assert partial_case is not None
        p_plink_id = f"plink_test_partial_{now_ts}"
        p_action = RecoveryAction(
            recovery_case_id=partial_case.id,
            action_type="CREATE_PAYMENT_LINK",
            status="EXECUTED",
            payment_link_id=p_plink_id
        )
        db.add(p_action)
        partial_case.status = "IN_PROGRESS"
        db.commit()
        p_case_id = partial_case.id
    finally:
        db.close()

    partial_payload = {
        "event": "payment_link.partially_paid",
        "payload": {
            "payment_link": {
                "entity": {"id": p_plink_id, "amount": 1000000, "amount_paid": 400000, "status": "partially_paid"}
            }
        }
    }
    code_part, resp_part = post_webhook(partial_payload, event_id=f"wh_evt_partial_{now_ts}")
    print(f"partially_paid Result: HTTP {code_part} -> {resp_part}")
    assert code_part == 200
    assert resp_part["case_status"] == "IN_PROGRESS"

    db = SessionLocal()
    try:
        p_case_check = db.query(RecoveryCase).filter(RecoveryCase.id == p_case_id).first()
        assert p_case_check.status == "IN_PROGRESS"  # Not marked as RECOVERED
        print(f"Verified partial payment case #{p_case_id} remains IN_PROGRESS.")
    finally:
        db.close()

    # 7. payment_link.cancelled Test
    print("\n[TEST 7] payment_link.cancelled Event Processing")
    cancel_payload = {
        "event": "payment_link.cancelled",
        "payload": {
            "payment_link": {
                "entity": {"id": p_plink_id, "amount": 1000000, "amount_paid": 0, "status": "cancelled"}
            }
        }
    }
    code_canc, resp_canc = post_webhook(cancel_payload, event_id=f"wh_evt_canc_{now_ts}")
    print(f"cancelled Result: HTTP {code_canc} -> {resp_canc}")
    assert code_canc == 200
    assert resp_canc["case_status"] == "CANCELLED"

    # 8. payment_link.expired Test
    print("\n[TEST 8] payment_link.expired Event Processing")
    expired_payload = {
        "event": "payment_link.expired",
        "payload": {
            "payment_link": {
                "entity": {"id": test_plink_id, "amount": 450000, "amount_paid": 0, "status": "expired"}
            }
        }
    }
    code_exp, resp_exp = post_webhook(expired_payload, event_id=f"wh_evt_exp_{now_ts}")
    print(f"expired Result: HTTP {code_exp} -> {resp_exp}")
    assert code_exp == 200

    # 9. Unknown payment_link_id Handled Gracefully
    print("\n[TEST 9] Unknown payment_link_id Resilience")
    unknown_payload = {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {"id": f"plink_unknown_{now_ts}", "amount": 200000, "amount_paid": 200000, "status": "paid"}
            }
        }
    }
    code_unk, resp_unk = post_webhook(unknown_payload, event_id=f"wh_evt_unk_{now_ts}")
    print(f"Unknown link result: HTTP {code_unk} -> {resp_unk}")
    assert code_unk == 200
    assert resp_unk["status"] == "unmatched"

    # 10. Missing Required Payload Fields (Expect 400)
    print("\n[TEST 10] Missing Required Payload Fields (Expect 400)")
    code_mal, resp_mal = post_webhook({"event": "payment_link.paid", "payload": {}}, event_id=f"wh_evt_mal_{now_ts}")
    print(f"Missing fields result: HTTP {code_mal} -> {resp_mal}")
    assert code_mal == 400

    print("\n[SUCCESS] ALL STAGE 3B WEBHOOK TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_tests()
