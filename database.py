import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "studypulse.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(reset_clean: bool = False):
    conn = get_connection()
    cursor = conn.cursor()

    if reset_clean:
        cursor.execute("DROP TABLE IF EXISTS study_sessions;")
        cursor.execute("DROP TABLE IF EXISTS flashcards;")
        cursor.execute("DROP TABLE IF EXISTS flashcard_decks;")
        cursor.execute("DROP TABLE IF EXISTS doubts;")
        cursor.execute("DROP TABLE IF EXISTS assignments;")
        cursor.execute("DROP TABLE IF EXISTS syllabus_topics;")
        cursor.execute("DROP TABLE IF EXISTS courses;")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT NOT NULL,
        instructor TEXT DEFAULT '',
        color TEXT DEFAULT '#6366f1',
        credits INTEGER DEFAULT 3,
        target_grade TEXT DEFAULT 'A',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS syllabus_topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        unit_name TEXT NOT NULL,
        topic_title TEXT NOT NULL,
        is_completed INTEGER DEFAULT 0,
        notes TEXT DEFAULT '',
        order_num INTEGER DEFAULT 0,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        due_date TEXT NOT NULL,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Pending',
        weight REAL DEFAULT 10.0,
        grade REAL DEFAULT NULL,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doubts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        question TEXT NOT NULL,
        intuition TEXT DEFAULT '',
        steps_json TEXT DEFAULT '[]',
        final_answer TEXT NOT NULL,
        tips TEXT DEFAULT '',
        practice_problem TEXT DEFAULT '',
        is_bookmarked INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flashcard_decks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT NOT NULL,
        subject TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id INTEGER NOT NULL,
        front TEXT NOT NULL,
        back TEXT NOT NULL,
        interval INTEGER DEFAULT 1,
        repetitions INTEGER DEFAULT 0,
        ease_factor REAL DEFAULT 2.5,
        next_review TEXT,
        FOREIGN KEY (deck_id) REFERENCES flashcard_decks (id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        duration_minutes INTEGER NOT NULL,
        session_type TEXT DEFAULT 'Pomodoro',
        notes TEXT DEFAULT '',
        completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE SET NULL
    );
    """)

    conn.commit()
    conn.close()

def seed_sample_data():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Sample Courses
    courses = [
        ("Calculus & Linear Algebra", "MATH-201", "Dr. Sarah Mitchell", "#6366f1", 4, "A"),
        ("Data Structures & Algorithms", "CS-204", "Prof. Alan Rivera", "#0ea5e9", 4, "A+"),
        ("Organic Chemistry I", "CHEM-105", "Dr. Emily Zhang", "#10b981", 3, "A")
    ]
    cursor.executemany(
        "INSERT INTO courses (name, code, instructor, color, credits, target_grade) VALUES (?, ?, ?, ?, ?, ?)",
        courses
    )
    conn.commit()

    # 2. Syllabus Topics
    syllabus = [
        (1, "Unit 1: Linear Transformations", "Matrices, Determinants and Inverses", 1, "Completed review"),
        (1, "Unit 1: Linear Transformations", "Eigenvalues and Eigenvectors", 0, "Practice problems"),
        (1, "Unit 2: Multivariable Calculus", "Partial Derivatives and Gradient", 0, "Formula list"),
        (2, "Unit 1: Advanced Trees", "AVL Trees and Rotations", 1, "Implemented in C++"),
        (2, "Unit 2: Graph Theory", "Dijkstra's Shortest Path Algorithm", 0, "Priority Queue"),
        (3, "Unit 1: Structure & Bonding", "Resonance Forms and Hybridization", 1, "Exam ready")
    ]
    cursor.executemany(
        "INSERT INTO syllabus_topics (course_id, unit_name, topic_title, is_completed, notes) VALUES (?, ?, ?, ?, ?)",
        syllabus
    )

    now = datetime.now()
    assignments = [
        (1, "Linear Algebra & Gradient Problem Set", (now + timedelta(days=2)).strftime("%Y-%m-%d"), "High", "Pending", 15.0, None),
        (2, "Graph Traversal & Dijkstra Project", (now + timedelta(days=4)).strftime("%Y-%m-%d"), "Urgent", "In Progress", 25.0, None)
    ]
    cursor.executemany(
        "INSERT INTO assignments (course_id, title, due_date, priority, status, weight, grade) VALUES (?, ?, ?, ?, ?, ?, ?)",
        assignments
    )

    conn.commit()
    conn.close()

# Database Helper Functions
def fetch_all_courses():
    conn = get_connection()
    courses = conn.execute("""
        SELECT c.*, 
            COUNT(DISTINCT s.id) as total_topics,
            SUM(CASE WHEN s.is_completed = 1 THEN 1 ELSE 0 END) as completed_topics,
            COUNT(DISTINCT a.id) as total_assignments,
            SUM(CASE WHEN a.status = 'Graded' OR a.status = 'Submitted' THEN 1 ELSE 0 END) as completed_assignments
        FROM courses c
        LEFT JOIN syllabus_topics s ON c.id = s.course_id
        LEFT JOIN assignments a ON c.id = a.course_id
        GROUP BY c.id
        ORDER BY c.name
    """).fetchall()
    conn.close()
    return [dict(c) for c in courses]

def get_course_details(course_id: int):
    conn = get_connection()
    course = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course:
        conn.close()
        return None
    
    topics = conn.execute("SELECT * FROM syllabus_topics WHERE course_id = ? ORDER BY unit_name, order_num, id", (course_id,)).fetchall()
    assignments = conn.execute("SELECT * FROM assignments WHERE course_id = ? ORDER BY due_date ASC", (course_id,)).fetchall()
    conn.close()
    
    res = dict(course)
    res["topics"] = [dict(t) for t in topics]
    res["assignments"] = [dict(a) for a in assignments]
    return res

def add_course(name: str, code: str, instructor: str, color: str, credits: int, target_grade: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO courses (name, code, instructor, color, credits, target_grade) VALUES (?, ?, ?, ?, ?, ?)",
        (name, code, instructor, color, credits, target_grade)
    )
    course_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return course_id

def update_course(course_id: int, name: str, code: str, instructor: str, color: str, credits: int, target_grade: str):
    conn = get_connection()
    conn.execute(
        "UPDATE courses SET name=?, code=?, instructor=?, color=?, credits=?, target_grade=? WHERE id=?",
        (name, code, instructor, color, credits, target_grade, course_id)
    )
    conn.commit()
    conn.close()

def delete_course(course_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    conn.commit()
    conn.close()

def add_syllabus_topic(course_id: int, unit_name: str, topic_title: str, notes: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO syllabus_topics (course_id, unit_name, topic_title, notes) VALUES (?, ?, ?, ?)",
        (course_id, unit_name, topic_title, notes)
    )
    topic_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return topic_id

def toggle_syllabus_topic(topic_id: int, is_completed: bool):
    conn = get_connection()
    conn.execute("UPDATE syllabus_topics SET is_completed = ? WHERE id = ?", (1 if is_completed else 0, topic_id))
    conn.commit()
    conn.close()

def delete_syllabus_topic(topic_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM syllabus_topics WHERE id = ?", (topic_id,))
    conn.commit()
    conn.close()

def fetch_all_assignments():
    conn = get_connection()
    assignments = conn.execute("""
        SELECT a.*, c.name as course_name, c.code as course_code, c.color as course_color
        FROM assignments a
        JOIN courses c ON a.course_id = c.id
        ORDER BY a.due_date ASC
    """).fetchall()
    conn.close()
    return [dict(a) for a in assignments]

def add_assignment(course_id: int, title: str, due_date: str, priority: str, weight: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO assignments (course_id, title, due_date, priority, status, weight) VALUES (?, ?, ?, ?, 'Pending', ?)",
        (course_id, title, due_date, priority, weight)
    )
    assignment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return assignment_id

def update_assignment_status(assignment_id: int, status: str, grade: Optional[float] = None):
    conn = get_connection()
    if grade is not None:
        conn.execute("UPDATE assignments SET status = ?, grade = ? WHERE id = ?", (status, grade, assignment_id))
    else:
        conn.execute("UPDATE assignments SET status = ? WHERE id = ?", (status, assignment_id))
    conn.commit()
    conn.close()

def delete_assignment(assignment_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM assignments WHERE id = ?", (assignment_id,))
    conn.commit()
    conn.close()

def fetch_all_doubts(search: Optional[str] = None, subject: Optional[str] = None, bookmarked_only: bool = False):
    conn = get_connection()
    query = "SELECT * FROM doubts WHERE 1=1"
    params = []
    if subject and subject != "All":
        query += " AND subject = ?"
        params.append(subject)
    if bookmarked_only:
        query += " AND is_bookmarked = 1"
    if search:
        query += " AND (question LIKE ? OR final_answer LIKE ? OR subject LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
    
    query += " ORDER BY created_at DESC"
    doubts = conn.execute(query, params).fetchall()
    conn.close()
    
    res = []
    for d in doubts:
        item = dict(d)
        try:
            item["steps"] = json.loads(item.get("steps_json", "[]"))
        except:
            item["steps"] = []
        res.append(item)
    return res

def save_doubt(subject: str, question: str, intuition: str, steps: list, final_answer: str, tips: str, practice_problem: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO doubts (subject, question, intuition, steps_json, final_answer, tips, practice_problem, is_bookmarked)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (subject, question, intuition, json.dumps(steps), final_answer, tips, practice_problem))
    doubt_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doubt_id

def toggle_doubt_bookmark(doubt_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_bookmarked FROM doubts WHERE id = ?", (doubt_id,))
    row = cursor.fetchone()
    if row:
        new_val = 0 if row["is_bookmarked"] else 1
        cursor.execute("UPDATE doubts SET is_bookmarked = ? WHERE id = ?", (new_val, doubt_id))
        conn.commit()
    conn.close()
    return new_val if row else 0

def delete_doubt(doubt_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM doubts WHERE id = ?", (doubt_id,))
    conn.commit()
    conn.close()

def fetch_decks():
    conn = get_connection()
    decks = conn.execute("""
        SELECT d.*, c.name as course_name, c.color as course_color,
               COUNT(f.id) as card_count
        FROM flashcard_decks d
        LEFT JOIN courses c ON d.course_id = c.id
        LEFT JOIN flashcards f ON d.id = f.deck_id
        GROUP BY d.id
        ORDER BY d.created_at DESC
    """).fetchall()
    conn.close()
    return [dict(d) for d in decks]

def get_deck_cards(deck_id: int):
    conn = get_connection()
    cards = conn.execute("SELECT * FROM flashcards WHERE deck_id = ? ORDER BY id ASC", (deck_id,)).fetchall()
    conn.close()
    return [dict(c) for c in cards]

def add_deck(title: str, subject: str, course_id: Optional[int] = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO flashcard_decks (title, subject, course_id) VALUES (?, ?, ?)", (title, subject, course_id))
    deck_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return deck_id

def add_card(deck_id: int, front: str, back: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO flashcards (deck_id, front, back) VALUES (?, ?, ?)", (deck_id, front, back))
    card_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return card_id

def log_study_session(course_id: Optional[int], duration_minutes: int, session_type: str, notes: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO study_sessions (course_id, duration_minutes, session_type, notes) VALUES (?, ?, ?, ?)",
        (course_id, duration_minutes, session_type, notes)
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_analytics_summary():
    conn = get_connection()
    
    # 1. Total study minutes
    total_minutes = conn.execute("SELECT COALESCE(SUM(duration_minutes), 0) FROM study_sessions").fetchone()[0]
    
    # 2. Total doubts solved
    total_doubts = conn.execute("SELECT COUNT(*) FROM doubts").fetchone()[0]
    
    # 3. Overall syllabus completion
    topic_stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed
        FROM syllabus_topics
    """).fetchone()
    total_topics = topic_stats["total"] or 0
    completed_topics = topic_stats["completed"] or 0
    syllabus_pct = round((completed_topics / total_topics * 100), 1) if total_topics > 0 else 0.0
    
    # 4. Daily study minutes for last 7 days
    daily_stats = conn.execute("""
        SELECT date(completed_at) as study_date, SUM(duration_minutes) as minutes
        FROM study_sessions
        WHERE completed_at >= datetime('now', '-6 days')
        GROUP BY date(completed_at)
        ORDER BY study_date ASC
    """).fetchall()
    
    # 5. Study time per course
    course_stats = conn.execute("""
        SELECT COALESCE(c.name, 'General Study') as course_name, 
               COALESCE(c.color, '#6366f1') as color,
               SUM(s.duration_minutes) as total_minutes
        FROM study_sessions s
        LEFT JOIN courses c ON s.course_id = c.id
        GROUP BY s.course_id
        ORDER BY total_minutes DESC
    """).fetchall()

    # 6. Current streak calculation (ONLY counts actual study sessions logged)
    session_dates = conn.execute("""
        SELECT DISTINCT date(completed_at) as s_date
        FROM study_sessions
        ORDER BY s_date DESC
    """).fetchall()
    
    streak = 0
    if session_dates:
        today = datetime.now().date()
        date_set = {datetime.strptime(row["s_date"], "%Y-%m-%d").date() for row in session_dates}
        curr = today if today in date_set else today - timedelta(days=1)
        while curr in date_set:
            streak += 1
            curr -= timedelta(days=1)

    conn.close()
    
    return {
        "total_study_hours": round(total_minutes / 60, 1),
        "total_study_minutes": total_minutes,
        "total_doubts_solved": total_doubts,
        "total_topics": total_topics,
        "completed_topics": completed_topics,
        "syllabus_completion_pct": syllabus_pct,
        "current_streak_days": streak,
        "daily_breakdown": [dict(r) for r in daily_stats],
        "course_breakdown": [dict(r) for r in course_stats]
    }
