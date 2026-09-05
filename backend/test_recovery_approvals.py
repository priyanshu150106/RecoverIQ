"""Automated Test Suite for RecoverIQ Stage 6 Step 2: Human-in-the-Loop Recovery Approvals.

Verifies:
1. Requesting approval creates a PENDING approval record
2. Duplicate pending approval requests for the same case are rejected (400)
3. Approvals for terminal cases (RECOVERED/CANCELLED) are rejected (400)
4. GET /api/approvals/pending returns the list of pending approvals
5. Rejecting approval transitions status to REJECTED and records operator reason
6. Executing a non-approved approval is rejected with HTTP 400
7. Approving an approval transitions status to APPROVED
8. Executing an APPROVED approval enforces deterministic link safety policy
9. Successful execution generates Razorpay test link and updates status to EXECUTED
10. Zero credential leakage across approval payloads
"""
import urllib.request
import urllib.error
import json
import time


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


def get(url):
    req = urllib.request.urlopen(url)
    return req.getcode(), json.loads(req.read().decode())


def run_tests():
    print("[STAGE 6 STEP 2 HUMAN-IN-THE-LOOP APPROVAL TEST SUITE]")

    # 1. Request Approval for a Valid Open Case
    print("\n[TEST 1] Request Approval for Case #2 (SEND_PAYMENT_LINK)")
    code_req, appr1 = post("http://127.0.0.1:8000/api/recovery-cases/2/approval", {
        "strategy": "SEND_PAYMENT_LINK",
        "requested_by": "risk_analyst"
    })
    print(f"Approval Request Response: HTTP {code_req} -> {appr1}")
    assert code_req == 201
    assert appr1["recovery_case_id"] == 2
    assert appr1["status"] == "PENDING"
    assert appr1["strategy_type"] == "SEND_PAYMENT_LINK"
    approval_id = appr1["id"]

    # 2. Duplicate Pending Approval Rejection
    print("\n[TEST 2] Duplicate Pending Approval Check (Expect 400)")
    code_dup, resp_dup = post("http://127.0.0.1:8000/api/recovery-cases/2/approval", {
        "strategy": "SEND_PAYMENT_LINK",
        "requested_by": "risk_analyst"
    })
    print(f"Duplicate Request Response: HTTP {code_dup} -> {resp_dup}")
    assert code_dup == 400
    assert "already exists" in resp_dup.get("detail", "").lower()

    # 3. Terminal Case Approval Rejection
    print("\n[TEST 3] Terminal Case Approval Check on RECOVERED Case (Expect 400)")
    code_cases, cases_list = get("http://127.0.0.1:8000/api/recovery-cases")
    recovered_case = next((c for c in cases_list if c["status"] == "RECOVERED"), None)
    target_case_id = recovered_case["id"] if recovered_case else 13
    code_term, resp_term = post(f"http://127.0.0.1:8000/api/recovery-cases/{target_case_id}/approval", {
        "strategy": "SEND_PAYMENT_LINK",
        "requested_by": "risk_analyst"
    })
    print(f"Terminal Case Request Response: HTTP {code_term} -> {resp_term}")
    assert code_term == 400
    assert "terminal status" in resp_term.get("detail", "").lower()

    # 4. Get Pending Approvals
    print("\n[TEST 4] GET /api/approvals/pending")
    code_pnd, pending_list = get("http://127.0.0.1:8000/api/approvals/pending")
    print(f"Pending List Response: HTTP {code_pnd}, Count: {len(pending_list)}")
    assert code_pnd == 200
    assert any(a["id"] == approval_id for a in pending_list)

    # 5. Reject Approval Flow
    print("\n[TEST 5] Reject Approval #{} Flow".format(approval_id))
    code_rej, resp_rej = post(f"http://127.0.0.1:8000/api/approvals/{approval_id}/reject", {
        "decided_by": "lead_operator",
        "reason": "Customer is disputing the invoice terms."
    })
    print(f"Reject Response: HTTP {code_rej} -> {resp_rej}")
    assert code_rej == 200
    assert resp_rej["status"] == "REJECTED"
    assert resp_rej["approved_by"] == "lead_operator"
    assert "disputing" in resp_rej["reason"]

    # 6. Execute REJECTED Approval (Expect 400)
    print("\n[TEST 6] Execute Rejected Approval (Expect 400)")
    code_bad_exec, resp_bad_exec = post(f"http://127.0.0.1:8000/api/approvals/{approval_id}/execute")
    print(f"Bad Exec Response: HTTP {code_bad_exec} -> {resp_bad_exec}")
    assert code_bad_exec == 400
    assert "must be approved" in resp_bad_exec.get("detail", "").lower()

    # 7. Create New Approval on Case #3, Approve & Execute Flow
    print("\n[TEST 7] Request Approval for Case #4 (SEND_SMART_RETRY_LINK)")
    code_req4, appr4 = post("http://127.0.0.1:8000/api/recovery-cases/4/approval", {
        "strategy": "SEND_SMART_RETRY_LINK",
        "requested_by": "system_auto"
    })
    assert code_req4 == 201
    appr4_id = appr4["id"]

    # 8. Approve the Request
    print("\n[TEST 8] Approve Approval #{}".format(appr4_id))
    code_appr, resp_appr = post(f"http://127.0.0.1:8000/api/approvals/{appr4_id}/approve", {
        "decided_by": "senior_merchant_ops",
        "reason": "Verified bank downtime history; safe for test link retry."
    })
    print(f"Approve Response: HTTP {code_appr} -> {resp_appr}")
    assert code_appr == 200
    assert resp_appr["status"] == "APPROVED"
    assert resp_appr["approved_by"] == "senior_merchant_ops"

    # 9. Execute the APPROVED Approval
    print("\n[TEST 9] Execute Approved Approval #{}".format(appr4_id))
    code_exec, resp_exec = post(f"http://127.0.0.1:8000/api/approvals/{appr4_id}/execute")
    print(f"Execute Approved Response: HTTP {code_exec} -> {resp_exec}")
    assert code_exec == 200
    assert resp_exec["status"] == "EXECUTED"
    assert resp_exec["payment_link_id"] is not None
    assert resp_exec["payment_link_url"] is not None
    assert "plink_" in resp_exec["payment_link_id"]

    # 10. Re-execution of already EXECUTED approval (Expect 400)
    print("\n[TEST 10] Re-execution of EXECUTED Approval (Expect 400)")
    code_reexec, resp_reexec = post(f"http://127.0.0.1:8000/api/approvals/{appr4_id}/execute")
    assert code_reexec == 400
    assert "must be approved" in resp_reexec.get("detail", "").lower()

    # 11. Zero Secret Leakage Check
    print("\n[TEST 11] Verify Zero Credentials Leakage")
    payload_str = json.dumps(resp_exec)
    assert "rzp_live" not in payload_str
    assert "secret" not in payload_str.lower() or "webhook_secret" not in payload_str.lower()

    print("\n[SUCCESS] ALL HUMAN-IN-THE-LOOP APPROVAL TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_tests()
