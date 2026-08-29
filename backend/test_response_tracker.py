from core.database import SessionLocal
from engine.classifier import classify_email_content
from engine.email_tracker import process_incoming_email
from models.application import Application
from models.response import Response
from models.status_history import StatusHistory


def main():
    db = SessionLocal()
    try:
        print("--- Testing Response Tracker & Classifier ---")

        test_cases = [
            (
                "Invitation to Interview: Python Developer Role",
                "Hi, We were impressed by your resume and would like to schedule a Zoom interview next Monday.",
                "interview"
            ),
            (
                "Update regarding your application at Corteva",
                "Thank you for your interest. Unfortunately, we have decided to pursue other candidates at this time.",
                "rejection"
            ),
            (
                "Application Received - Software Engineer",
                "Thank you for applying. We have received your application and are reviewing it.",
                "seen"
            )
        ]

        print("\n1. Verifying Classifier Rules:")
        for subj, body, expected in test_cases:
            resp_type, mapped_status = classify_email_content(subj, body)
            print(f"  [{resp_type.upper()}] Subject: '{subj[:35]}...' -> Mapped Status: '{mapped_status}' (Expected: {expected})")
            assert resp_type == expected, f"Expected {expected}, got {resp_type}"

        print("\n2. Simulating Incoming Email Ingestion to DB:")
        app = db.query(Application).first()
        if not app:
            print("No applications found in DB. Run test_apply_engine.py first.")
            return

        initial_status = app.status
        print(f"  Current App #{app.id} Status: {initial_status}")

        # Simulate receiving an interview invitation email
        interview_subj = "Schedule technical round - Backend Role"
        interview_body = "We would like to invite you for a 30-minute screening interview call via Google Meet."
        
        resp = process_incoming_email(
            db=db,
            sender="recruiter@company.com",
            subject=interview_subj,
            body=interview_body
        )

        db.refresh(app)
        print(f"  New App #{app.id} Status: {app.status}")
        print(f"  Created Response ID: {resp.id if resp else 'None'}")

        # Check status history entry
        history = db.query(StatusHistory).filter(StatusHistory.application_id == app.id).all()
        print(f"  Status History Entries: {len(history)}")
        for h in history:
            print(f"    - {h.old_status} -> {h.new_status} (via {h.trigger} at {h.changed_at.strftime('%H:%M:%S')})")

    finally:
        db.close()


if __name__ == "__main__":
    main()