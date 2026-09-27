# FitBuddy – AI Fitness Plan Generator using Gemini Models

An intelligent full-stack fitness and nutrition program generator built with **FastAPI**, **Jinja2**, **SQLite + SQLAlchemy**, and **Google Gemini AI**.

---

## Features

- **Personalized 7-Day Workout Program**: Tailored to individual anatomy, experience level, available equipment, injuries, and goals.
- **Scientific Nutrition & Recovery Blueprint**: Daily calorie and macro recommendations, pre/post-workout meal timing, and sleep/mobility protocols.
- **Adaptive Feedback Engine**: Users can submit feedback (e.g. knee discomfort during squats, time constraints) and Gemini re-optimizes the plan automatically.
- **Dual Plan Versioning**: Stores both original and revised routines so users can compare changes anytime.
- **Interactive Workout Tracking**: Interactive day-by-day tabs with set-completion checkboxes.
- **Admin & Repository Dashboard**: View and manage all user plans, filter by goals, and monitor statistics.
- **Resilient Fallback Mode**: Fully testable immediately even before an API key is configured.

---

## Project Structure

```text
buddy/
├── .env.example            # Environment variables template
├── .env                    # Active local environment variables
├── requirements.txt        # Python package dependencies
├── database.py             # SQLAlchemy engine & session setup
├── models.py               # Database schemas (FitnessPlan)
├── schemas.py              # Pydantic validation models
├── gemini_service.py       # Google Gemini AI integration & feedback logic
├── main.py                 # FastAPI application routes & handlers
├── test_app.py             # Test suite verifying all routes & features
├── static/
│   ├── css/
│   │   └── style.css       # Responsive dark-theme fitness design system
│   └── js/
│       └── main.js         # Interactive tab switching, feedback & search
└── templates/
    ├── base.html           # Master layout with navigation and footer
    ├── index.html          # Homepage & fitness questionnaire form
    ├── plan.html           # 7-day routine, nutrition, recovery & feedback
    ├── admin.html          # All-users / admin plans repository
    └── error.html          # Error handling view
```

---

## Getting Started

### 1. Installation

Open your terminal or command prompt in the project root:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Open `.env` (or copy from `.env.example`) and insert your Google Gemini API key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

> **Note:** If no API key is provided, the application runs in comprehensive fallback demo mode so all features and routes remain 100% operational.

### 3. Run the Application

Start the local server with Uvicorn:

```bash
uvicorn main:app --reload
```

### 4. Open in Browser

Navigate to:

```text
http://127.0.0.1:8000
```
