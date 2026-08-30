import os
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import database as db
import ai_solver

app = FastAPI(title="StudyPulse API", description="Course Tracking, Multi-Engine AI Doubt Solver & Study Enhancement Suite", version="2.0.0")

# Initialize database schema and seed data
db.init_db()

# Pydantic Schemas
class CourseCreate(BaseModel):
    name: str
    code: str
    instructor: Optional[str] = ""
    color: Optional[str] = "#6366f1"
    credits: Optional[int] = 3
    target_grade: Optional[str] = "A"

class SyllabusTopicCreate(BaseModel):
    unit_name: str
    topic_title: str
    notes: Optional[str] = ""

class ToggleTopic(BaseModel):
    is_completed: bool

class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    due_date: str
    priority: Optional[str] = "Medium"
    weight: Optional[float] = 10.0

class AssignmentUpdate(BaseModel):
    status: str
    grade: Optional[float] = None

class SolveDoubtRequest(BaseModel):
    question: str
    subject: Optional[str] = "General"
    api_key: Optional[str] = None
    provider: Optional[str] = "auto"
    mode: Optional[str] = "standard"
    save_to_history: Optional[bool] = True

class DeckCreate(BaseModel):
    title: str
    subject: str
    course_id: Optional[int] = None

class AutoDeckRequest(BaseModel):
    topic: str
    subject: Optional[str] = "General"
    course_id: Optional[int] = None

class CardCreate(BaseModel):
    front: str
    back: str

class QuizGenerateRequest(BaseModel):
    topic: str
    subject: Optional[str] = "General"

class StudySessionLog(BaseModel):
    course_id: Optional[int] = None
    duration_minutes: int
    session_type: Optional[str] = "Pomodoro"
    notes: Optional[str] = ""

# API Endpoints

# --- COURSES ---
@app.get("/api/courses")
def get_courses():
    return db.fetch_all_courses()

@app.post("/api/courses")
def create_course(course: CourseCreate):
    course_id = db.add_course(course.name, course.code, course.instructor, course.color, course.credits, course.target_grade)
    return {"id": course_id, "message": "Course created successfully"}

@app.get("/api/courses/{course_id}")
def get_course(course_id: int):
    c = db.get_course_details(course_id)
    if not c:
        raise HTTPException(status_code=404, detail="Course not found")
    return c

@app.put("/api/courses/{course_id}")
def update_course(course_id: int, course: CourseCreate):
    db.update_course(course_id, course.name, course.code, course.instructor, course.color, course.credits, course.target_grade)
    return {"message": "Course updated successfully"}

@app.delete("/api/courses/{course_id}")
def delete_course(course_id: int):
    db.delete_course(course_id)
    return {"message": "Course deleted successfully"}

# --- SYLLABUS ---
@app.post("/api/courses/{course_id}/syllabus")
def add_syllabus_topic(course_id: int, topic: SyllabusTopicCreate):
    topic_id = db.add_syllabus_topic(course_id, topic.unit_name, topic.topic_title, topic.notes)
    return {"id": topic_id, "message": "Topic added successfully"}

@app.put("/api/syllabus/{topic_id}/toggle")
def toggle_topic(topic_id: int, req: ToggleTopic):
    db.toggle_syllabus_topic(topic_id, req.is_completed)
    return {"message": "Topic status updated"}

@app.delete("/api/syllabus/{topic_id}")
def delete_syllabus_topic(topic_id: int):
    db.delete_syllabus_topic(topic_id)
    return {"message": "Topic deleted"}

# --- ASSIGNMENTS ---
@app.get("/api/assignments")
def get_assignments():
    return db.fetch_all_assignments()

@app.post("/api/assignments")
def create_assignment(a: AssignmentCreate):
    aid = db.add_assignment(a.course_id, a.title, a.due_date, a.priority, a.weight)
    return {"id": aid, "message": "Assignment created successfully"}

@app.put("/api/assignments/{assignment_id}")
def update_assignment(assignment_id: int, req: AssignmentUpdate):
    db.update_assignment_status(assignment_id, req.status, req.grade)
    return {"message": "Assignment status updated"}

@app.delete("/api/assignments/{assignment_id}")
def delete_assignment(assignment_id: int):
    db.delete_assignment(assignment_id)
    return {"message": "Assignment deleted"}

# --- AI DOUBT SOLVER ---
@app.get("/api/doubts")
def get_doubts(
    search: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    bookmarked: Optional[bool] = Query(False)
):
    return db.fetch_all_doubts(search=search, subject=subject, bookmarked_only=bookmarked)

@app.post("/api/doubts/solve")
async def solve_doubt_endpoint(req: SolveDoubtRequest):
    solution = await ai_solver.solve_doubt(
        question=req.question,
        subject=req.subject or "General",
        api_key=req.api_key,
        provider=req.provider or "auto",
        mode=req.mode or "standard"
    )
    
    doubt_id = None
    if req.save_to_history:
        doubt_id = db.save_doubt(
            subject=solution["subject"],
            question=req.question,
            intuition=solution["intuition"],
            steps=solution["steps"],
            final_answer=solution["final_answer"],
            tips=solution["tips"],
            practice_problem=solution["practice_problem"]
        )
    
    return {
        "id": doubt_id,
        "subject": solution["subject"],
        "question": req.question,
        "intuition": solution["intuition"],
        "steps": solution["steps"],
        "final_answer": solution["final_answer"],
        "tips": solution["tips"],
        "practice_problem": solution["practice_problem"],
        "is_bookmarked": 0
    }

@app.post("/api/doubts/{doubt_id}/bookmark")
def toggle_bookmark(doubt_id: int):
    new_val = db.toggle_doubt_bookmark(doubt_id)
    return {"is_bookmarked": new_val}

@app.delete("/api/doubts/{doubt_id}")
def delete_doubt(doubt_id: int):
    db.delete_doubt(doubt_id)
    return {"message": "Doubt deleted"}

# --- FLASHCARDS & QUIZZES ---
@app.get("/api/decks")
def get_decks():
    return db.fetch_decks()

@app.get("/api/decks/{deck_id}/cards")
def get_deck_cards(deck_id: int):
    return db.get_deck_cards(deck_id)

@app.post("/api/decks")
def create_deck(deck: DeckCreate):
    deck_id = db.add_deck(deck.title, deck.subject, deck.course_id)
    return {"id": deck_id, "message": "Deck created"}

@app.post("/api/decks/generate")
def generate_deck_from_topic(req: AutoDeckRequest):
    deck_id = db.add_deck(f"{req.topic} - Quick Mastery", req.subject or "General", req.course_id)
    cards = ai_solver.generate_flashcards_from_topic(req.topic, req.subject or "General")
    for c in cards:
        db.add_card(deck_id, c["front"], c["back"])
    return {"id": deck_id, "cards_count": len(cards), "message": "AI Flashcard deck generated successfully!"}

@app.post("/api/decks/{deck_id}/cards")
def add_card(deck_id: int, card: CardCreate):
    card_id = db.add_card(deck_id, card.front, card.back)
    return {"id": card_id, "message": "Card added"}

@app.post("/api/quiz/generate")
def generate_quiz(req: QuizGenerateRequest):
    questions = ai_solver.generate_quiz_from_topic(req.topic, req.subject or "General")
    return {
        "topic": req.topic,
        "subject": req.subject,
        "questions": questions
    }

# --- FOCUS SESSIONS & ANALYTICS ---
@app.post("/api/sessions")
def log_session(session: StudySessionLog):
    sid = db.log_study_session(session.course_id, session.duration_minutes, session.session_type, session.notes)
    return {"id": sid, "message": "Study session logged!"}

@app.get("/api/analytics")
def get_analytics():
    return db.get_analytics_summary()

@app.post("/api/reset-data")
def reset_all_data():
    """Resets database completely to clean slate (0 streaks, 0 hours, empty courses)."""
    db.init_db(reset_clean=True)
    return {"message": "All data has been reset to a fresh state!"}

@app.post("/api/seed-demo")
def seed_demo():
    """Loads sample courses and study data for exploration."""
    db.init_db(reset_clean=True)
    db.seed_sample_data()
    return {"message": "Sample demo data loaded!"}

# Mount Static Files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))
