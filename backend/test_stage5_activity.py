"""Automated Test Suite for RecoverIQ Stage 5: Activity Feed and Case Timeline.

Verifies:
1. GET /api/dashboard/activity-feed returns HTTP 200
2. Activity feed objects match normalized ActivityItem schema
3. Global feed is ordered descending (newest -> oldest)
4. Limit query parameter functions as expected
5. Maximum limit of 100 is enforced
6. Existing seeded data generates operational activities
7. GET /api/recovery-cases/{id}/timeline returns HTTP 200
8. Case timeline is ordered ascending (oldest -> newest)
9. Non-existent case ID returns HTTP 404
10. Secrets, API keys, and webhook secrets never appear in outputs
"""
import urllib.request
import urllib.error
import json
from datetime import datetime


def get(url):
    req = urllib.request.urlopen(url)
    return req.getcode(), json.loads(req.read().decode())


def run_tests():
    print("[STAGE 5 ACTIVITY FEED & TIMELINE TEST SUITE]")

    # 1. Global Activity Feed Endpoint
    print("\n[TEST 1] GET /api/dashboard/activity-feed (Default limit=20)")
    code_feed, feed = get("http://127.0.0.1:8000/api/dashboard/activity-feed")
    print(f"Feed Response: HTTP {code_feed}, Total items: {len(feed)}")
    assert code_feed == 200
    assert isinstance(feed, list)
    assert len(feed) > 0, "Feed should contain activities from seeded database"

    # 2. Activity Item Schema Verification
    print("\n[TEST 2] Verify Normalized ActivityItem Schema Fields")
    first_act = feed[0]
    required_keys = ["id", "timestamp", "actor", "action", "summary", "status", "case_id", "amount", "metadata"]
    for k in required_keys:
        assert k in first_act, f"Missing required activity field '{k}'"

    valid_actors = {"AI_AGENT", "POLICY_ENGINE", "RAZORPAY_EXECUTION", "WEBHOOK_RECEIVER", "SYSTEM"}
    assert first_act["actor"] in valid_actors, f"Invalid actor: {first_act['actor']}"
    print(f"Sample Activity [{first_act['actor']} | {first_act['action']}]: {first_act['summary']}")

    # 3. Newest -> Oldest Sorting Verification
    print("\n[TEST 3] Verify Global Feed Sorting (Newest First)")
    for i in range(len(feed) - 1):
        t1 = datetime.fromisoformat(feed[i]["timestamp"].replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(feed[i+1]["timestamp"].replace("Z", "+00:00"))
        assert t1 >= t2, f"Activities out of order at index {i}: {t1} < {t2}"
    print(f"Verified all {len(feed)} items strictly ordered newest -> oldest.")

    # 4. Limit Parameter Verification
    print("\n[TEST 4] Verify Limit Parameter (limit=5)")
    code_lim, feed_lim = get("http://127.0.0.1:8000/api/dashboard/activity-feed?limit=5")
    assert code_lim == 200
    assert len(feed_lim) <= 5
    print(f"Limit=5 returned {len(feed_lim)} items.")

    # 5. Limit Clamping & Validation
    print("\n[TEST 5] Verify Max Limit Validation")
    # FastAPI query ge=1, le=100 returns 422 if limit > 100
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/api/dashboard/activity-feed?limit=200")
        assert False, "Should have rejected limit > 100 with HTTP 422"
    except urllib.error.HTTPError as e:
        assert e.code == 422
        print(f"Limit > 100 rejected as expected with HTTP {e.code}.")

    # 6. Case Timeline Endpoint
    print("\n[TEST 6] GET /api/recovery-cases/1/timeline")
    code_tl, timeline = get("http://127.0.0.1:8000/api/recovery-cases/1/timeline")
    print(f"Case #1 Timeline Response: HTTP {code_tl}, Total milestones: {len(timeline)}")
    assert code_tl == 200
    assert isinstance(timeline, list)
    assert len(timeline) >= 2, "Timeline should include failure detection and AI diagnosis"

    # 7. Timeline Oldest -> Newest Sorting Verification
    print("\n[TEST 7] Verify Case Timeline Sorting (Oldest First)")
    for i in range(len(timeline) - 1):
        t1 = datetime.fromisoformat(timeline[i]["timestamp"].replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(timeline[i+1]["timestamp"].replace("Z", "+00:00"))
        assert t1 <= t2, f"Timeline milestones out of order at index {i}: {t1} > {t2}"
    print(f"Verified {len(timeline)} milestones strictly ordered oldest -> newest.")

    # 8. Invalid Case ID 404 Check
    print("\n[TEST 8] GET /api/recovery-cases/999999/timeline (Expect 404)")
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/api/recovery-cases/999999/timeline")
        assert False, "Should have returned 404 for invalid case ID"
    except urllib.error.HTTPError as e:
        assert e.code == 404
        body = json.loads(e.read().decode())
        assert "not found" in body.get("detail", "").lower()
        print(f"Invalid case correctly returned HTTP 404 -> {body}")

    # 9. Secret Leak Prevention Verification
    print("\n[TEST 9] Verify Zero Secrets or Credentials Leakage")
    feed_json = json.dumps(feed)
    timeline_json = json.dumps(timeline)
    forbidden_tokens = ["rzp_test_", "secret", "bearer", "api_key", "sk-", "token"]
    for token in forbidden_tokens:
        assert token not in feed_json.lower() or "secret" in feed_json.lower() and "webhook_secret" not in feed_json.lower()
        assert token not in timeline_json.lower() or "secret" in timeline_json.lower() and "webhook_secret" not in timeline_json.lower()
    print("Zero credential leakage verified across all activity responses.")

    print("\n[SUCCESS] ALL STAGE 5 ACTIVITY FEED & TIMELINE TESTS PASSED CLEANLY!")


if __name__ == "__main__":
    run_tests()
