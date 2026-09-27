import os
import json
import logging
import warnings
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Initialize Gemini SDK (supports new google.genai and legacy google.generativeai)
_client = None
_legacy_model = None

try:
    from google import genai
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        _client = genai.Client(api_key=GEMINI_API_KEY)
except Exception:
    pass

if not _client and GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=GEMINI_API_KEY)
            for m in ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-pro"]:
                try:
                    _legacy_model = genai_legacy.GenerativeModel(m)
                    break
                except Exception:
                    continue
    except Exception:
        pass



def _call_gemini(prompt: str) -> Optional[str]:
    """Helper to query Gemini via modern google.genai or fallback google.generativeai."""
    # Reload .env dynamically so user-added keys take effect immediately
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_gemini_api_key_here":
        return None

    # 1. Try modern google.genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        for model_name in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
            try:
                resp = client.models.generate_content(model=model_name, contents=prompt)
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                logger.warning(f"google.genai model {model_name} failed: {e}")
                continue
    except Exception as e:
        logger.warning(f"google.genai client initialization failed: {e}")

    # 2. Try legacy google.generativeai SDK
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=api_key)
            for m in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
                try:
                    legacy_model = genai_legacy.GenerativeModel(m)
                    resp = legacy_model.generate_content(prompt)
                    if resp and resp.text:
                        return resp.text.strip()
                except Exception as e:
                    logger.warning(f"legacy genai model {m} failed: {e}")
                    continue
    except Exception as e:
        logger.warning(f"legacy genai configuration failed: {e}")

    return None


def _extract_json(text: str) -> str:
    """Extract valid JSON substring even if model wrapped it in markdown or extra text."""
    clean = text.strip()
    if "```json" in clean:
        clean = clean.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in clean:
        clean = clean.split("```", 1)[1].split("```", 1)[0].strip()
    
    first_brace = clean.find("{")
    first_bracket = clean.find("[")
    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        last_brace = clean.rfind("}")
        if last_brace != -1:
            clean = clean[first_brace:last_brace+1]
    elif first_bracket != -1:
        last_bracket = clean.rfind("]")
        if last_bracket != -1:
            clean = clean[first_bracket:last_bracket+1]
    return clean


def generate_7_day_plan(user_data: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Generates a personalized 7-day workout plan, nutrition tips, and recovery advice using Gemini AI.
    Returns: (workout_plan_text, nutrition_tips_text, recovery_tips_text)
    """
    prompt = f"""
You are FitBuddy, an elite certified fitness coach and sports nutritionist.
Create a comprehensive, personalized 7-day fitness and lifestyle program for the following client:

Client Details:
- Name: {user_data.get('user_name')}
- Age: {user_data.get('age')}
- Gender: {user_data.get('gender')}
- Height: {user_data.get('height', 'Not specified')} cm
- Weight: {user_data.get('weight', 'Not specified')} kg
- Primary Fitness Goal: {user_data.get('fitness_goal')}
- Current Fitness Level: {user_data.get('fitness_level')}
- Workout Environment: {user_data.get('workout_location')}
- Available Equipment: {user_data.get('available_equipment', 'Standard gym equipment')}
- Preferred Workout Days: {user_data.get('days_per_week', 7)} days/week
- Physical Limitations / Injuries: {user_data.get('injuries_limitations', 'None')}
- Dietary Preference: {user_data.get('dietary_preference', 'Balanced')}

Return your response in valid JSON with three top-level keys:
1. "workout_plan": A structured 7-day plan. For each day (Day 1 to Day 7), include:
   - day_number: (1 to 7)
   - day_name: (e.g., "Day 1 - Push Hypertrophy", "Day 4 - Active Recovery & Mobility")
   - focus: (Muscle groups or focus area)
   - warm_up: (5-10 min specific warm-up exercises)
   - exercises: Array of objects with fields: exercise, sets, reps, rest, notes
   - cool_down: (Stretching / breathing)
2. "nutrition_tips": Comprehensive nutrition guidance including:
   - Daily estimated caloric and macronutrient targets
   - Ideal pre-workout and post-workout meal ideas
   - Meal timing and hydration strategies tailored to {user_data.get('dietary_preference')} diet
3. "recovery_tips": Evidence-based recovery advice including:
   - Sleep optimization techniques
   - Active recovery and mobility protocols
   - Injury prevention addressing: {user_data.get('injuries_limitations')}

Respond strictly with valid JSON. Do not include markdown code block quotes like ```json.
"""

    text = _call_gemini(prompt)
    if text:
        try:
            clean_text = _extract_json(text)
            data = json.loads(clean_text)
            
            workout_plan = json.dumps(data.get("workout_plan", []), indent=2)
            nutrition_tips = data.get("nutrition_tips", "")
            if isinstance(nutrition_tips, (dict, list)):
                nutrition_tips = json.dumps(nutrition_tips, indent=2)
                
            recovery_tips = data.get("recovery_tips", "")
            if isinstance(recovery_tips, (dict, list)):
                recovery_tips = json.dumps(recovery_tips, indent=2)
                
            return workout_plan, str(nutrition_tips), str(recovery_tips)
        except Exception as e:
            logger.error(f"Gemini API parse failed: {e}. Falling back to default comprehensive plan.")
            return _generate_fallback_plan(user_data)
    else:
        return _generate_fallback_plan(user_data)


def update_plan_with_feedback(original_plan: str, user_data: Dict[str, Any], feedback: str) -> str:
    """
    Updates an existing workout plan based on user feedback using Gemini AI.
    Returns: updated_workout_plan_text
    """
    prompt = f"""
You are FitBuddy, an elite personal trainer. 
The client {user_data.get('user_name')} has provided specific feedback on their current 7-day workout plan.

Client Profile:
- Goal: {user_data.get('fitness_goal')}
- Level: {user_data.get('fitness_level')}
- Limitations/Injuries: {user_data.get('injuries_limitations')}
- Equipment: {user_data.get('available_equipment')}

Current Plan:
{original_plan}

Client Feedback / Adjustment Request:
"{feedback}"

Task:
Revise the 7-day workout plan to directly solve and address the client's feedback while keeping their fitness goal on track.
Return your updated plan in valid JSON format matching the original structure:
Array of 7 day objects with:
- day_number
- day_name
- focus
- warm_up
- exercises (array of objects: exercise, sets, reps, rest, notes)
- cool_down
- changes_applied: (A brief 1-2 sentence note describing what was specifically adjusted for this day in response to the feedback)

Respond strictly with valid JSON. Do not include markdown code block quotes like ```json.
"""

    text = _call_gemini(prompt)
    if text:
        try:
            clean_text = _extract_json(text)
            parsed = json.loads(clean_text)
            if isinstance(parsed, dict) and "workout_plan" in parsed:
                parsed = parsed["workout_plan"]
            return json.dumps(parsed, indent=2)
        except Exception as e:
            logger.error(f"Gemini API feedback parse failed: {e}. Generating fallback revised plan.")
            return _generate_fallback_feedback_plan(original_plan, feedback)
    else:
        return _generate_fallback_feedback_plan(original_plan, feedback)



def _generate_fallback_plan(user_data: Dict[str, Any]) -> Tuple[str, str, str]:
    """Generates an intelligent default 7-day program when API is offline or key is unconfigured."""
    goal = user_data.get("fitness_goal", "Overall Fitness")
    level = user_data.get("fitness_level", "Intermediate")
    loc = user_data.get("workout_location", "Gym")
    equip = user_data.get("available_equipment", "Standard weights")
    injuries = user_data.get("injuries_limitations", "None")
    diet = user_data.get("dietary_preference", "Balanced")

    days = [
        {
            "day_number": 1,
            "day_name": "Day 1 - Upper Body Push & Core",
            "focus": "Chest, Shoulders, Triceps, Anterior Core",
            "warm_up": "5 mins arm circles, cat-cow stretch, band pull-aparts, light push-ups.",
            "exercises": [
                {"exercise": "Dumbbell or Barbell Bench Press", "sets": "4", "reps": "8-10", "rest": "90s", "notes": f"Control eccentric tempo. Adjusted for {level} level."},
                {"exercise": "Overhead Dumbbell Shoulder Press", "sets": "3", "reps": "10-12", "rest": "75s", "notes": "Engage core, avoid arching lower back."},
                {"exercise": "Incline Dumbbell Flyes / Push-ups", "sets": "3", "reps": "12-15", "rest": "60s", "notes": "Deep chest stretch at the bottom."},
                {"exercise": "Cable Rope or Dumbbell Tricep Extensions", "sets": "3", "reps": "12-15", "rest": "60s", "notes": "Lock out elbow at the bottom."},
                {"exercise": "Plank to Shoulder Taps", "sets": "3", "reps": "45s", "rest": "45s", "notes": "Keep hips square to the ground."}
            ],
            "cool_down": "5 mins chest door-frame stretch, overhead tricep stretch, deep diaphragmatic breathing."
        },
        {
            "day_number": 2,
            "day_name": "Day 2 - Lower Body Strength & Glute Focus",
            "focus": "Quadriceps, Hamstrings, Glutes, Calves",
            "warm_up": "5 mins bodyweight squats, leg swings, glute bridges, ankle circles.",
            "exercises": [
                {"exercise": "Goblet Squats or Barbell Back Squats", "sets": "4", "reps": "8-10", "rest": "90s", "notes": f"Safety caution: keep knees tracked over toes. Mindful of {injuries}."},
                {"exercise": "Romanian Deadlifts (Dumbbell or Barbell)", "sets": "3", "reps": "10-12", "rest": "90s", "notes": "Hinge at the hips, neutral spine."},
                {"exercise": "Walking Lunges or Bulgarian Split Squats", "sets": "3", "reps": "10 per leg", "rest": "75s", "notes": "Step forward with steady balance."},
                {"exercise": "Lying Leg Curls or Swiss Ball Curls", "sets": "3", "reps": "12-15", "rest": "60s", "notes": "Squeeze hamstrings at peak contraction."},
                {"exercise": "Standing Calf Raises", "sets": "4", "reps": "15-20", "rest": "45s", "notes": "Full stretch at bottom, 2-sec hold at top."}
            ],
            "cool_down": "5 mins hamstring forward fold, quad stretch, pigeon pose."
        },
        {
            "day_number": 3,
            "day_name": "Day 3 - Active Recovery, Mobility & Core Flow",
            "focus": "Joint Mobility, Heart Rate Recovery, Spine Health",
            "warm_up": "3 mins brisk walking or light cycling.",
            "exercises": [
                {"exercise": "World's Greatest Stretch", "sets": "3", "reps": "5 each side", "rest": "30s", "notes": "Move through thoracic rotation slowly."},
                {"exercise": "Bird-Dog Isometric Holds", "sets": "3", "reps": "10 each side", "rest": "45s", "notes": "3-second squeeze at full extension."},
                {"exercise": "Zone 2 Low-Intensity Cardio (Walk/Incline)", "sets": "1", "reps": "25-30 mins", "rest": "None", "notes": "Nasal breathing pace to promote blood flow."}
            ],
            "cool_down": "Child's pose, foam rolling on quads and lats."
        },
        {
            "day_number": 4,
            "day_name": "Day 4 - Upper Body Pull & Posterior Chain",
            "focus": "Lats, Rhomboids, Biceps, Rear Delts",
            "warm_up": "5 mins band pull-aparts, scapular pull-ups or shrugs, dead hangs.",
            "exercises": [
                {"exercise": "Lat Pulldown or Pull-ups", "sets": "4", "reps": "8-10", "rest": "90s", "notes": "Drive elbows down toward hips."},
                {"exercise": "Bent-Over Dumbbell Rows", "sets": "3", "reps": "10-12", "rest": "75s", "notes": "Keep back flat and squeeze shoulder blades."},
                {"exercise": "Face Pulls with Resistance Band/Cable", "sets": "3", "reps": "15", "rest": "60s", "notes": "Great for posture and rear deltoid health."},
                {"exercise": "Incline Dumbbell Bicep Curls", "sets": "3", "reps": "12", "rest": "60s", "notes": "Full elbow extension without swinging."},
                {"exercise": "Hanging Knee Raises / Reverse Crunches", "sets": "3", "reps": "12-15", "rest": "45s", "notes": "Curl pelvis upwards into ribs."}
            ],
            "cool_down": "Lat stretch against wall, cross-body shoulder stretch."
        },
        {
            "day_number": 5,
            "day_name": "Day 5 - Full Body Functional & Conditioning",
            "focus": "Compound Multi-Joint Movements, Metabolic Conditioning",
            "warm_up": "5 mins jumping jacks, inchworms, high knees.",
            "exercises": [
                {"exercise": "Dumbbell Thrusters (Squat to Press)", "sets": "4", "reps": "10", "rest": "75s", "notes": "Power through the legs to assist the press."},
                {"exercise": "Kettlebell or Dumbbell Swings", "sets": "4", "reps": "15", "rest": "60s", "notes": "Explosive hip hinge, do not squat."},
                {"exercise": "Renegade Rows to Push-up", "sets": "3", "reps": "8 per side", "rest": "60s", "notes": "Widen feet for stability."},
                {"exercise": "Farmer's Carries", "sets": "3", "reps": "40 meters", "rest": "60s", "notes": "Grip strength and total core stabilization."}
            ],
            "cool_down": "Cobra stretch, hip flexor kneeling stretch, deep breathing."
        },
        {
            "day_number": 6,
            "day_name": "Day 6 - High-Intensity Intervals (HIIT) & Core",
            "focus": "Cardiovascular Endurance, Fat Burn, Core Stability",
            "warm_up": "5 mins dynamic skipping, arm crossovers, butt kicks.",
            "exercises": [
                {"exercise": "Interval Sprint / Cycle (30s sprint, 60s cruise)", "sets": "8 rounds", "reps": "12 mins total", "rest": "As prescribed", "notes": "Give 85% effort during sprint intervals."},
                {"exercise": "Medicine Ball Slams or Mountain Climbers", "sets": "3", "reps": "45s on / 15s off", "rest": "45s", "notes": "Engage abs as you slam."},
                {"exercise": "Hollow Body Rock or Deadbug", "sets": "3", "reps": "30s", "rest": "30s", "notes": "Press lower back firmly into the floor."}
            ],
            "cool_down": "Gentle 5-min walk, hamstring stretch, calf stretch."
        },
        {
            "day_number": 7,
            "day_name": "Day 7 - Rest, Deep Recovery & Mind-Body Reset",
            "focus": "Full CNS Reset, Tissue Regeneration & Mental Prep",
            "warm_up": "None required - gentle breathing.",
            "exercises": [
                {"exercise": "Gentle Nature Walk or Restorative Yoga", "sets": "1", "reps": "30-45 mins", "rest": "None", "notes": "No intense strain; promote parasympathetic state."},
                {"exercise": "Full Body Foam Rolling & Static Stretching", "sets": "1", "reps": "15 mins", "rest": "None", "notes": "Spend 60s on any tight muscles."}
            ],
            "cool_down": "10 mins mindfulness meditation or box breathing (4s in, 4s hold, 4s out, 4s hold)."
        }
    ]

    nutrition = f"""### Personalized Nutrition Blueprint ({diet} Approach)
- **Goal Alignment:** Tailored specifically for **{goal}** at an **{level}** fitness level.
- **Estimated Daily Intake:** Calibrated for your body composition and training energy expenditure.
- **Macronutrient Strategy:**
  - **Protein:** 1.8g - 2.2g per kg of body weight to support muscle protein synthesis and recovery.
  - **Complex Carbohydrates:** Oats, brown rice, sweet potatoes, and quinoa timed primarily around workouts.
  - **Healthy Fats:** Avocados, nuts, seeds, extra virgin olive oil for hormonal balance.
- **Nutrient Timing:**
  - **Pre-Workout (60-90 min before):** Easily digestible carbohydrates + 20-25g protein (e.g., oatmeal with berries and protein shake, or rice cakes with banana and nut butter).
  - **Post-Workout (within 45 min):** 30g fast-absorbing protein + carbohydrates to replenish glycogen stores.
- **Hydration Target:** Minimum 3.0 to 3.5 liters of water daily, adding electrolytes on intense training days."""

    recovery = f"""### Science-Backed Recovery & Longevity Protocol
- **Sleep Architecture:** Aim for 7.5 to 9 hours of quality sleep. Keep your bedroom cool (65°F/18°C) and eliminate blue light screens 45 minutes before sleep.
- **Injury Mitigation ({injuries}):**
  - Always perform the dedicated dynamic warm-up before lifting loads.
  - Never push through acute, sharp joint pain.
- **Active Tissue Recovery:** Perform targeted myofascial release (foam rolling) 2-3 times per week on hamstrings, quads, and upper back.
- **Post-Workout Cool Down:** Spend 5 minutes performing diaphragmatic breathing immediately following workouts to down-regulate your central nervous system from sympathetic to parasympathetic state."""

    return json.dumps(days, indent=2), nutrition, recovery


def _generate_fallback_feedback_plan(original_plan: str, feedback: str) -> str:
    """Updates the JSON workout plan with user feedback modifications in fallback mode."""
    try:
        plan_list = json.loads(original_plan)
    except Exception:
        return original_plan

    lower_fb = feedback.lower()

    for day in plan_list:
        day["changes_applied"] = f"Adjusted exercises and pacing based on your feedback: '{feedback[:60]}...'"
        
        # Knee or squat adjustment
        if "knee" in lower_fb or "squat" in lower_fb or "joint" in lower_fb:
            for ex in day.get("exercises", []):
                if "squat" in ex.get("exercise", "").lower() or "lunge" in ex.get("exercise", "").lower():
                    ex["exercise"] = "Leg Press (Foot Placed High) / Glute Bridge (Low Knee Stress)"
                    ex["notes"] = "Modified to knee-friendly variation per your feedback."

        # Time constraint adjustment
        if "time" in lower_fb or "shorter" in lower_fb or "busy" in lower_fb or "minute" in lower_fb:
            day["focus"] += " (Time-Optimized Superset Protocol)"
            for ex in day.get("exercises", []):
                ex["rest"] = "45s"
                ex["notes"] += " [Fast-paced superset to fit tight schedule]"

        # Intensity adjustment
        if "hard" in lower_fb or "heavy" in lower_fb or "tired" in lower_fb or "sore" in lower_fb:
            for ex in day.get("exercises", []):
                ex["sets"] = str(max(2, int(ex.get("sets", "3").split()[0]) - 1))
                ex["notes"] = "Volume scaled back for better recovery."
        elif "easy" in lower_fb or "increase" in lower_fb or "more" in lower_fb:
            for ex in day.get("exercises", []):
                ex["notes"] = "Progressive overload applied (+10% load or extra reps)."

    return json.dumps(plan_list, indent=2)
