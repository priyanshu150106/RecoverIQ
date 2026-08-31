import urllib.request
import json

def get(url):
    req = urllib.request.urlopen(url)
    return json.loads(req.read().decode())

def post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode())

def run_tests():
    print("[TEST 1] GET /health")
    h = get("http://127.0.0.1:8000/health")
    print("Health response:", h)
    assert h["status"] == "healthy"

    print("\n[TEST 2] GET /api/dashboard/metrics")
    m = get("http://127.0.0.1:8000/api/dashboard/metrics")
    print("Metrics response:", json.dumps(m, indent=2))
    assert m["cases_detected"] >= 18
    assert m["total_revenue_processed"] > 0

    print("\n[TEST 3] GET /api/recovery-cases")
    cases = get("http://127.0.0.1:8000/api/recovery-cases")
    print(f"Total recovery cases returned: {len(cases)}")
    assert len(cases) >= 18
    first_case = cases[0]
    print(f"Case #1: Customer: {first_case['customer_name']} | Amount: Rs {first_case['amount']/100} | Prob: {first_case['recovery_probability']} | Action: {first_case['recommended_action']}")

    print("\n[TEST 4] GET /api/recovery-cases/{case_id}")
    detail = get(f"http://127.0.0.1:8000/api/recovery-cases/{first_case['id']}")
    print(f"Case #{detail['id']} Diagnostic Detail:")
    print(" - Customer:", detail["customer"]["name"], f"({detail['customer']['email']})")
    print(" - Payment Event ID:", detail["payment_event_id"], f"Status: {detail['payment_event']['status']}")
    print(" - Risk Score:", detail["risk_score"], "/ 100")
    print(" - Recovery Probability:", detail["recovery_probability"])
    print(" - Scoring Breakdown:", detail.get("scoring_breakdown"))
    print(" - Actions Count:", len(detail["recovery_actions"]))

    print("\n[TEST 5] POST /api/events (New Payment Failure)")
    test_event = {
        "event_type": "payment.failed",
        "customer": {
            "name": "Arjun Nair",
            "email": "arjun.nair@example.com",
            "phone": "+919999988888"
        },
        "amount": 499900,
        "failure_reason": "bank_authorization_timeout",
        "external_event_id": "pay_test_synthetic_999"
    }
    res_ingest = post("http://127.0.0.1:8000/api/events", test_event)
    print("Ingestion result:", res_ingest)
    assert res_ingest["status"] == "success"
    assert res_ingest["is_duplicate"] is False
    assert res_ingest["recovery_case_id"] is not None

    print("\n[TEST 6] POST /api/events (Duplicate Check on external_event_id)")
    res_dup = post("http://127.0.0.1:8000/api/events", test_event)
    print("Duplicate check result:", res_dup)
    assert res_dup["status"] == "success"
    assert res_dup["is_duplicate"] is True

    print("\n[SUCCESS] ALL BACKEND TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
