"""
Unit & Integration Test Suite for FitBuddy
Verifies database operations, Gemini service responses, and FastAPI endpoints.
"""
import os
import json
from fastapi.testclient import TestClient
from database import engine, Base, SessionLocal
import models
from main import app
import gemini_service

def run_tests():
    print("=== [1] Testing Database & Models ===")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Test plan generation in gemini_service
    print("\n=== [2] Testing Gemini Service (Generation & Fallback) ===")
    sample_user = {
        "user_name": "Test Athlete",
        "age": 28,
        "gender": "Male",
        "height": 180.0,
        "weight": 78.0,
        "fitness_goal": "Lean Muscle Hypertrophy",
        "fitness_level": "Intermediate",
        "workout_location": "Commercial Gym",
        "available_equipment": "Barbells, Dumbbells, Cables",
        "days_per_week": 7,
        "injuries_limitations": "Mild lower back stiffness",
        "dietary_preference": "High Protein Balanced"
    }

    workout_json, nutrition, recovery = gemini_service.generate_7_day_plan(sample_user)
    assert workout_json is not None, "Workout JSON should not be None"
    plan_data = json.loads(workout_json)
    assert len(plan_data) == 7, f"Expected 7 days, got {len(plan_data)}"
    print(f"[OK] Successfully generated 7-day plan with {len(plan_data)} days.")
    print(f"[OK] Nutrition advice length: {len(nutrition)} chars.")
    print(f"[OK] Recovery protocol length: {len(recovery)} chars.")

    # Test feedback revision
    print("\n=== [3] Testing Feedback Engine Update ===")
    updated_json = gemini_service.update_plan_with_feedback(
        original_plan=workout_json,
        user_data=sample_user,
        feedback="Knee pain during squats, please replace with leg press and hip thrusts."
    )
    assert updated_json is not None, "Updated plan JSON should not be None"
    updated_data = json.loads(updated_json)
    assert len(updated_data) == 7, f"Expected 7 days in revised plan, got {len(updated_data)}"
    print("[OK] Successfully revised workout plan based on feedback.")

    # Test FastAPI endpoints with TestClient
    print("\n=== [4] Testing FastAPI Endpoints ===")
    client = TestClient(app)

    # 1. GET /
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "FitBuddy" in res.text
    print("[OK] GET / (Home) returned 200 OK.")

    # 2. POST /generate
    form_data = {
        "user_name": "Sarah Connor",
        "age": 30,
        "gender": "Female",
        "height": 168.0,
        "weight": 62.0,
        "fitness_goal": "Athletic Conditioning",
        "fitness_level": "Advanced",
        "workout_location": "Gym",
        "available_equipment": "Full Gym",
        "days_per_week": 7,
        "injuries_limitations": "None",
        "dietary_preference": "High Protein"
    }
    res = client.post("/generate", data=form_data, follow_redirects=False)
    assert res.status_code == 303, f"Expected 303 Redirect, got {res.status_code}"
    redirect_url = res.headers["location"]
    print(f"[OK] POST /generate created plan and redirected to {redirect_url}.")

    # 3. GET /plan/{id}
    res = client.get(redirect_url)
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "Sarah Connor" in res.text
    assert "7-Day Workout Routine" in res.text
    print(f"[OK] GET {redirect_url} rendered plan correctly.")

    plan_id = int(redirect_url.split("/")[-1])

    # 4. POST /plan/{id}/feedback
    fb_data = {"feedback": "Shorten Wednesday session to 30 mins."}
    res = client.post(f"/plan/{plan_id}/feedback", data=fb_data, follow_redirects=False)
    assert res.status_code == 303, f"Expected 303 Redirect, got {res.status_code}"
    print("[OK] POST /plan/{id}/feedback applied feedback and redirected.")

    # 5. Verify plan updated in DB and page
    res = client.get(f"/plan/{plan_id}")
    assert res.status_code == 200
    assert "Feedback Active" in res.text or "Shorten Wednesday" in res.text
    print("[OK] GET /plan/{id} successfully displays revised version with feedback toggle.")

    # 6. GET /admin
    res = client.get("/admin")
    assert res.status_code == 200
    assert "Sarah Connor" in res.text
    print("[OK] GET /admin rendered all plans table.")

    # 7. GET /health
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    print("[OK] GET /health returned healthy status.")


    db.close()
    print("\n=======================================================")
    print(" ALL TESTS PASSED SUCCESSFULLY! FITBUDDY IS READY. ")
    print("=======================================================\n")

if __name__ == "__main__":
    run_tests()
