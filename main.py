import os
import json
import logging
from typing import Optional
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Local modules
import models
from database import engine, get_db
import gemini_service

# Load environment configuration
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fitbuddy")

# Ensure database tables exist
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI application
app = FastAPI(
    title="FitBuddy – AI Fitness Plan Generator",
    description="Intelligent 7-day personalized workout and nutrition plan generator powered by Google Gemini.",
    version="1.0.0"
)

# Mount static assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Initialize Jinja2 Templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=templates_dir)

# Register custom Jinja2 filters
def parse_json_filter(value):
    """Safely parse JSON string into Python object inside templates."""
    if not value:
        return []
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return []

templates.env.filters["parse_json"] = parse_json_filter


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home_view(request: Request, db: Session = Depends(get_db)):
    """Render the homepage with the fitness questionnaire and generator form."""
    total_plans = db.query(models.FitnessPlan).count()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "total_plans_count": total_plans,
            "api_configured": bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here")
        }
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate_plan_endpoint(
    request: Request,
    user_name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    height: Optional[float] = Form(None),
    weight: Optional[float] = Form(None),
    fitness_goal: str = Form(...),
    fitness_level: str = Form(...),
    workout_location: str = Form(...),
    available_equipment: Optional[str] = Form("Standard Gym Equipment"),
    days_per_week: int = Form(7),
    injuries_limitations: Optional[str] = Form("None"),
    dietary_preference: Optional[str] = Form("Balanced"),
    db: Session = Depends(get_db)
):
    """Process user form inputs, generate 7-day AI plan + nutrition/recovery, and persist in database."""
    user_data = {
        "user_name": user_name.strip(),
        "age": age,
        "gender": gender,
        "height": height,
        "weight": weight,
        "fitness_goal": fitness_goal,
        "fitness_level": fitness_level,
        "workout_location": workout_location,
        "available_equipment": available_equipment or "Standard Gym Equipment",
        "days_per_week": days_per_week,
        "injuries_limitations": injuries_limitations or "None",
        "dietary_preference": dietary_preference or "Balanced"
    }

    try:
        # Call Gemini AI service
        workout_plan, nutrition_tips, recovery_tips = gemini_service.generate_7_day_plan(user_data)

        # Store in SQLite database
        new_plan = models.FitnessPlan(
            user_name=user_data["user_name"],
            age=user_data["age"],
            gender=user_data["gender"],
            height=user_data["height"],
            weight=user_data["weight"],
            fitness_goal=user_data["fitness_goal"],
            fitness_level=user_data["fitness_level"],
            workout_location=user_data["workout_location"],
            available_equipment=user_data["available_equipment"],
            days_per_week=user_data["days_per_week"],
            injuries_limitations=user_data["injuries_limitations"],
            dietary_preference=user_data["dietary_preference"],
            original_workout_plan=workout_plan,
            nutrition_tips=nutrition_tips,
            recovery_tips=recovery_tips,
            feedback_applied=False
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)

        # Redirect to plan detail page
        return RedirectResponse(url=f"/plan/{new_plan.id}", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        logger.error(f"Error generating plan: {e}")
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "error_title": "Generation Failed",
                "error_message": f"Unable to generate fitness plan: {str(e)}"
            },
            status_code=500
        )


@app.get("/plan/{plan_id}", response_class=HTMLResponse)
async def view_plan(request: Request, plan_id: int, updated: Optional[bool] = False, db: Session = Depends(get_db)):
    """Render the generated 7-day fitness plan, nutrition tips, recovery advice, and feedback form."""
    plan = db.query(models.FitnessPlan).filter(models.FitnessPlan.id == plan_id).first()
    if not plan:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "error_title": "Plan Not Found",
                "error_message": f"Fitness plan #{plan_id} could not be found."
            },
            status_code=404
        )

    return templates.TemplateResponse(
        request=request,
        name="plan.html",
        context={
            "plan": plan,
            "just_updated": updated,
            "api_configured": bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here")
        }
    )


@app.post("/plan/{plan_id}/feedback", response_class=HTMLResponse)
async def submit_feedback(
    request: Request,
    plan_id: int,
    feedback: str = Form(...),
    db: Session = Depends(get_db)
):
    """Receive feedback from user, request Gemini to adapt the plan, and store the updated version."""
    plan = db.query(models.FitnessPlan).filter(models.FitnessPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    user_profile = {
        "user_name": plan.user_name,
        "fitness_goal": plan.fitness_goal,
        "fitness_level": plan.fitness_level,
        "injuries_limitations": plan.injuries_limitations,
        "available_equipment": plan.available_equipment,
    }

    try:
        # Generate adapted plan using feedback
        updated_plan_json = gemini_service.update_plan_with_feedback(
            original_plan=plan.original_workout_plan,
            user_data=user_profile,
            feedback=feedback.strip()
        )

        # Update database record
        plan.user_feedback = feedback.strip()
        plan.updated_workout_plan = updated_plan_json
        plan.feedback_applied = True
        db.commit()

        return RedirectResponse(url=f"/plan/{plan_id}?updated=true", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        logger.error(f"Error applying feedback to plan {plan_id}: {e}")
        db.rollback()
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={
                "error_title": "Update Failed",
                "error_message": f"Could not adjust plan with feedback: {str(e)}"
            },
            status_code=500
        )


@app.get("/admin", response_class=HTMLResponse)
@app.get("/plans", response_class=HTMLResponse)
async def admin_all_plans_view(request: Request, db: Session = Depends(get_db)):
    """Admin / All Users view displaying all generated plans and system metrics."""
    plans = db.query(models.FitnessPlan).order_by(models.FitnessPlan.created_at.desc()).all()
    
    total_plans = len(plans)
    feedback_plans = sum(1 for p in plans if p.feedback_applied)
    
    # Calculate goal distributions
    goals_count = {}
    for p in plans:
        goals_count[p.fitness_goal] = goals_count.get(p.fitness_goal, 0) + 1
    top_goal = max(goals_count, key=goals_count.get) if goals_count else "None"

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "plans": plans,
            "total_plans": total_plans,
            "feedback_plans": feedback_plans,
            "top_goal": top_goal
        }
    )



@app.post("/plan/{plan_id}/delete")
async def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete a plan from the database (admin action)."""
    plan = db.query(models.FitnessPlan).filter(models.FitnessPlan.id == plan_id).first()
    if plan:
        db.delete(plan)
        db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/health")
async def health_check():
    """Health check endpoint for local monitoring."""
    return {
        "status": "healthy",
        "app": "FitBuddy",
        "version": "1.0.0",
        "database": "SQLite connected",
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here")
    }
