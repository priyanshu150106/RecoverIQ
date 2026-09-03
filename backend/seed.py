"""Database Seeding Script for RecoverIQ Development.

Generates realistic SYNTHETIC customer profiles, payment events, recovery cases, and outcomes.
All records in this file are completely synthetic and for testing/hackathon purposes only.
"""
import sys
import os
from datetime import datetime, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models.customer import Customer
from app.models.payment_event import PaymentEvent
from app.models.recovery_case import RecoveryCase
from app.models.recovery_action import RecoveryAction
from app.models.recovery_outcome import RecoveryOutcome
from app.services.recovery_scoring import recovery_scorer
from app.schemas.event import NormalizedEvent, NormalizedCustomerInfo


def run_seed():
    """Drops existing tables, recreates schema, and seeds synthetic datasets."""
    print("[INFO] Resetting SQLite database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # 1. Synthetic Customers (14 realistic personas)
        customers_data = [
            # Loyal power buyers
            {"name": "Aarav Sharma", "email": "aarav.sharma@example.com", "phone": "+919876543210", "total": 6, "success": 5, "failed": 1, "paid": 1850000},
            {"name": "Priya Patel", "email": "priya.patel@example.com", "phone": "+919812345678", "total": 5, "success": 4, "failed": 1, "paid": 1200000},
            {"name": "Rohan Verma", "email": "rohan.verma@example.com", "phone": "+919823456789", "total": 8, "success": 8, "failed": 0, "paid": 3450000},
            {"name": "Ananya Iyer", "email": "ananya.iyer@example.com", "phone": "+919834567890", "total": 4, "success": 3, "failed": 1, "paid": 899900},
            
            # Mid-tier regular buyers
            {"name": "Vikram Singh", "email": "vikram.singh@example.com", "phone": "+919845678901", "total": 3, "success": 2, "failed": 1, "paid": 599800},
            {"name": "Sneha Kulkarni", "email": "sneha.k@example.com", "phone": "+919856789012", "total": 3, "success": 1, "failed": 2, "paid": 299900},
            {"name": "Kabir Mehta", "email": "kabir.mehta@example.com", "phone": "+919867890123", "total": 2, "success": 1, "failed": 1, "paid": 450000},
            {"name": "Neha Reddy", "email": "neha.reddy@example.com", "phone": "+919878901234", "total": 4, "success": 2, "failed": 2, "paid": 780000},
            
            # High-risk / repeat failure customers
            {"name": "Aditya Roy", "email": "aditya.roy@example.com", "phone": "+919889012345", "total": 4, "success": 0, "failed": 4, "paid": 0},
            {"name": "Pooja Deshmukh", "email": "pooja.d@example.com", "phone": "+919890123456", "total": 3, "success": 0, "failed": 3, "paid": 0},

            # New / first-time customers
            {"name": "Devansh Gupta", "email": "devansh.g@example.com", "phone": "+919901234567", "total": 1, "success": 0, "failed": 1, "paid": 0},
            {"name": "Meera Nambiar", "email": "meera.n@example.com", "phone": "+919912345678", "total": 1, "success": 0, "failed": 1, "paid": 0},
            {"name": "Tanmay Joshi", "email": "tanmay.j@example.com", "phone": "+919923456789", "total": 1, "success": 0, "failed": 1, "paid": 0},
            {"name": "Ishita Sen", "email": "ishita.sen@example.com", "phone": "+919934567890", "total": 1, "success": 0, "failed": 1, "paid": 0},
        ]

        customer_objs = {}
        for c in customers_data:
            cust = Customer(
                name=c["name"],
                email=c["email"],
                phone=c["phone"],
                total_transactions=c["total"],
                successful_transactions=c["success"],
                failed_transactions=c["failed"],
                total_paid=c["paid"],
                created_at=now - timedelta(days=30)
            )
            db.add(cust)
            db.flush()
            customer_objs[c["email"]] = cust

        print(f"[SUCCESS] Created {len(customer_objs)} synthetic customers.")

        # 2. Synthetic Payment Events
        events_data = [
            # High recovery potential
            {
                "email": "aarav.sharma@example.com",
                "type": "payment.failed",
                "amount": 450000, # Rs 4,500
                "status": "failed",
                "reason": "bank_authorization_timeout",
                "ext_id": "pay_test_001",
                "delta_hours": 2,
                "case_status": "DETECTED"
            },
            {
                "email": "priya.patel@example.com",
                "type": "payment.failed",
                "amount": 899900, # Rs 8,999
                "status": "failed",
                "reason": "issuer_unavailable_network_error",
                "ext_id": "pay_test_002",
                "delta_hours": 5,
                "case_status": "IN_PROGRESS"
            },
            {
                "email": "rohan.verma@example.com",
                "type": "payment.failed",
                "amount": 2500000, # Rs 25,000
                "status": "failed",
                "reason": "bank_downtime_intermittent",
                "ext_id": "pay_test_003",
                "delta_hours": 1,
                "case_status": "DETECTED"
            },

            # Expired payment links
            {
                "email": "ananya.iyer@example.com",
                "type": "payment_link.expired",
                "amount": 299900, # Rs 2,999
                "status": "expired",
                "reason": "payment_link_ttl_expired_24h",
                "ext_id": "plink_test_004",
                "delta_hours": 8,
                "case_status": "IN_PROGRESS"
            },
            {
                "email": "vikram.singh@example.com",
                "type": "payment_link.expired",
                "amount": 1200000, # Rs 12,000
                "status": "expired",
                "reason": "customer_inactivity_link_expired",
                "ext_id": "plink_test_005",
                "delta_hours": 14,
                "case_status": "DETECTED"
            },

            # Partial Payments
            {
                "email": "sneha.k@example.com",
                "type": "payment_link.partially_paid",
                "amount": 1500000, # Rs 15,000 total
                "status": "partially_paid",
                "reason": "partial_installment_1_received",
                "ext_id": "plink_test_006",
                "delta_hours": 4,
                "case_status": "IN_PROGRESS"
            },

            # Insufficient Balance
            {
                "email": "kabir.mehta@example.com",
                "type": "payment.failed",
                "amount": 99900, # Rs 999
                "status": "failed",
                "reason": "insufficient_funds_in_account",
                "ext_id": "pay_test_007",
                "delta_hours": 10,
                "case_status": "DETECTED"
            },
            {
                "email": "neha.reddy@example.com",
                "type": "payment.failed",
                "amount": 349900, # Rs 3,499
                "status": "failed",
                "reason": "insufficient_account_balance",
                "ext_id": "pay_test_008",
                "delta_hours": 18,
                "case_status": "IN_PROGRESS"
            },

            # Card Expiry & Auth Rejections
            {
                "email": "devansh.g@example.com",
                "type": "payment.failed",
                "amount": 1800000, # Rs 18,000
                "status": "failed",
                "reason": "card_expired_or_invalid_expiry",
                "ext_id": "pay_test_009",
                "delta_hours": 20,
                "case_status": "DETECTED"
            },
            {
                "email": "meera.n@example.com",
                "type": "payment.failed",
                "amount": 549900, # Rs 5,499
                "status": "failed",
                "reason": "card_declined_by_customer_bank",
                "ext_id": "pay_test_010",
                "delta_hours": 26,
                "case_status": "DETECTED"
            },

            # High Risk / Flagged Cases
            {
                "email": "aditya.roy@example.com",
                "type": "payment.failed",
                "amount": 2200000, # Rs 22,000
                "status": "failed",
                "reason": "repeated_failed_3ds_fraud_suspected",
                "ext_id": "pay_test_011",
                "delta_hours": 32,
                "case_status": "DETECTED"
            },
            {
                "email": "pooja.d@example.com",
                "type": "payment.failed",
                "amount": 1599900, # Rs 15,999
                "status": "failed",
                "reason": "blocked_card_high_velocity",
                "ext_id": "pay_test_012",
                "delta_hours": 38,
                "case_status": "DETECTED"
            },

            # Successfully Recovered Cases
            {
                "email": "aarav.sharma@example.com",
                "type": "payment.failed",
                "amount": 350000, # Rs 3,500
                "status": "failed",
                "reason": "bank_authorization_timeout",
                "ext_id": "pay_test_013",
                "delta_hours": 48,
                "case_status": "RECOVERED"
            },
            {
                "email": "priya.patel@example.com",
                "type": "payment_link.expired",
                "amount": 499900, # Rs 4,999
                "status": "expired",
                "reason": "payment_link_ttl_expired",
                "ext_id": "plink_test_014",
                "delta_hours": 60,
                "case_status": "RECOVERED"
            },
            {
                "email": "rohan.verma@example.com",
                "type": "payment.failed",
                "amount": 950000, # Rs 9,500
                "status": "failed",
                "reason": "network_timeout",
                "ext_id": "pay_test_015",
                "delta_hours": 72,
                "case_status": "RECOVERED"
            },

            # Baseline Transactions
            {
                "email": "aarav.sharma@example.com",
                "type": "payment.captured",
                "amount": 1500000, # Rs 15,000
                "status": "paid",
                "reason": None,
                "ext_id": "pay_test_016",
                "delta_hours": 90,
                "case_status": None
            },
            {
                "email": "rohan.verma@example.com",
                "type": "payment_link.paid",
                "amount": 2500000, # Rs 25,000
                "status": "paid",
                "reason": None,
                "ext_id": "plink_test_017",
                "delta_hours": 95,
                "case_status": None
            },
            {
                "email": "priya.patel@example.com",
                "type": "payment.captured",
                "amount": 700000, # Rs 7,000
                "status": "paid",
                "reason": None,
                "ext_id": "pay_test_018",
                "delta_hours": 100,
                "case_status": None
            },
            {
                "email": "ananya.iyer@example.com",
                "type": "payment.captured",
                "amount": 600000, # Rs 6,000
                "status": "paid",
                "reason": None,
                "ext_id": "pay_test_019",
                "delta_hours": 110,
                "case_status": None
            },
            {
                "email": "vikram.singh@example.com",
                "type": "payment.captured",
                "amount": 599800, # Rs 5,998
                "status": "paid",
                "reason": None,
                "ext_id": "pay_test_020",
                "delta_hours": 120,
                "case_status": None
            },
            {
                "email": "tanmay.j@example.com",
                "type": "payment_link.expired",
                "amount": 380000, # Rs 3,800
                "status": "expired",
                "reason": "payment_link_ttl_expired",
                "ext_id": "plink_test_021",
                "delta_hours": 6,
                "case_status": "DETECTED"
            },
            {
                "email": "ishita.sen@example.com",
                "type": "payment.failed",
                "amount": 149900, # Rs 1,499
                "status": "failed",
                "reason": "insufficient_funds",
                "ext_id": "pay_test_022",
                "delta_hours": 12,
                "case_status": "DETECTED"
            },
            {
                "email": "sneha.k@example.com",
                "type": "payment.failed",
                "amount": 299900, # Rs 2,999
                "status": "failed",
                "reason": "bank_authorization_timeout",
                "ext_id": "pay_test_023",
                "delta_hours": 16,
                "case_status": "DETECTED"
            },
            {
                "email": "kabir.mehta@example.com",
                "type": "payment.captured",
                "amount": 450000, # Rs 4,500
                "status": "paid",
                "reason": None,
                "ext_id": "pay_test_024",
                "delta_hours": 80,
                "case_status": None
            },
            {
                "email": "neha.reddy@example.com",
                "type": "payment.captured",
                "amount": 780000, # Rs 7,800
                "status": "paid",
                "reason": None,
                "ext_id": "pay_test_025",
                "delta_hours": 85,
                "case_status": None
            }
        ]

        created_cases_count = 0
        created_outcomes_count = 0

        for ev in events_data:
            cust = customer_objs[ev["email"]]
            event_time = now - timedelta(hours=ev["delta_hours"])

            pe = PaymentEvent(
                customer_id=cust.id,
                event_type=ev["type"],
                amount=ev["amount"],
                currency="INR",
                status=ev["status"],
                failure_reason=ev["reason"],
                external_event_id=ev["ext_id"],
                created_at=event_time
            )
            db.add(pe)
            db.flush()

            if ev["case_status"]:
                norm = NormalizedEvent(
                    event_type=ev["type"],
                    customer=NormalizedCustomerInfo(
                        name=cust.name,
                        email=cust.email,
                        phone=cust.phone
                    ),
                    amount=ev["amount"],
                    currency="INR",
                    status=ev["status"],
                    failure_reason=ev["reason"],
                    external_event_id=ev["ext_id"],
                    created_at=event_time
                )
                scoring = recovery_scorer.evaluate(norm, cust)

                rc = RecoveryCase(
                    customer_id=cust.id,
                    payment_event_id=pe.id,
                    risk_score=scoring["risk_score"],
                    recovery_probability=scoring["recovery_probability"],
                    recommended_action=scoring["recommended_action"],
                    confidence=scoring["confidence"],
                    status=ev["case_status"],
                    created_at=event_time
                )
                db.add(rc)
                db.flush()

                is_recovered = ev["case_status"] == "RECOVERED"
                is_partial = ev["type"] == "payment_link.partially_paid"
                is_in_progress = ev["case_status"] == "IN_PROGRESS"

                act = RecoveryAction(
                    recovery_case_id=rc.id,
                    action_type=scoring["recommended_action"],
                    status="EXECUTED" if (is_recovered or is_in_progress) else "PENDING",
                    external_reference=f"act_ref_{pe.id}",
                    payment_link_id=f"plink_seed_{pe.id}",
                    payment_link_url=f"https://rzp.io/i/seedLink{pe.id}",
                    created_at=event_time
                )
                db.add(act)
                db.flush()

                # 3. Seed measurable Recovery Outcomes
                outcome_status = "RECOVERED" if is_recovered else ("PARTIALLY_RECOVERED" if is_partial else ("PENDING" if is_in_progress else "FAILED"))
                amount_rec = ev["amount"] if is_recovered else (ev["amount"] // 2 if is_partial else 0)
                rec_pct = 100.0 if is_recovered else (50.0 if is_partial else 0.0)
                rec_time = event_time + timedelta(minutes=4) if is_recovered else None
                rec_sec = 240.0 if is_recovered else None

                outcome = RecoveryOutcome(
                    recovery_case_id=rc.id,
                    recovery_action_id=act.id,
                    strategy_type=scoring["recommended_action"],
                    outcome_status=outcome_status,
                    amount_at_risk=ev["amount"],
                    amount_recovered=amount_rec,
                    recovery_percentage=rec_pct,
                    execution_timestamp=event_time,
                    recovery_timestamp=rec_time,
                    time_to_recovery_seconds=rec_sec,
                    created_at=event_time
                )
                db.add(outcome)

                created_cases_count += 1
                created_outcomes_count += 1

        db.commit()
        print(f"[SUCCESS] Created {len(events_data)} synthetic payment events.")
        print(f"[SUCCESS] Created {created_cases_count} recovery cases.")
        print(f"[SUCCESS] Created {created_outcomes_count} recovery outcomes.")

        return {
            "customers": len(customer_objs),
            "events": len(events_data),
            "cases": created_cases_count,
            "outcomes": created_outcomes_count
        }

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error during seed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    result = run_seed()
    print("\n[SUCCESS] Seeding completed successfully!")
    print(f"Customers: {result['customers']} | Events: {result['events']} | Cases: {result['cases']} | Outcomes: {result['outcomes']}")
