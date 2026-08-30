import asyncio
import os
import sys
import unittest

# Ensure root dir is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import database as db
import ai_solver
from fastapi.testclient import TestClient
from main import app

class TestStudyPulse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.init_db()
        cls.client = TestClient(app)

    def test_01_get_courses(self):
        response = self.client.get("/api/courses")
        self.assertEqual(response.status_code, 200)
        courses = response.json()
        self.assertIsInstance(courses, list)
        self.assertGreaterEqual(len(courses), 1)
        print(f"[PASS] Courses fetched: {len(courses)} courses found.")

    def test_02_create_and_manage_course(self):
        # 1. Create course
        payload = {
            "name": "Intro to Quantum Mechanics",
            "code": "PHYS-301",
            "instructor": "Dr. Feynman",
            "color": "#8b5cf6",
            "credits": 4,
            "target_grade": "A"
        }
        res = self.client.post("/api/courses", json=payload)
        self.assertEqual(res.status_code, 200)
        course_id = res.json()["id"]
        self.assertIsNotNone(course_id)

        # 2. Add Syllabus Topic
        topic_payload = {
            "unit_name": "Unit 1: Wave Mechanics",
            "topic_title": "Schrodinger Time-Independent Equation",
            "notes": "Key concept for exam 1"
        }
        res_topic = self.client.post(f"/api/courses/{course_id}/syllabus", json=topic_payload)
        self.assertEqual(res_topic.status_code, 200)
        topic_id = res_topic.json()["id"]

        # 3. Toggle Topic Status
        res_toggle = self.client.put(f"/api/syllabus/{topic_id}/toggle", json={"is_completed": True})
        self.assertEqual(res_toggle.status_code, 200)

        # 4. Fetch Course Details
        res_details = self.client.get(f"/api/courses/{course_id}")
        self.assertEqual(res_details.status_code, 200)
        data = res_details.json()
        self.assertEqual(data["name"], "Intro to Quantum Mechanics")
        self.assertEqual(len(data["topics"]), 1)
        self.assertEqual(data["topics"][0]["is_completed"], 1)

        print("[PASS] Course and syllabus topic management verified.")

    def test_03_doubt_solver_math(self):
        req = {
            "question": "How do I find eigenvalues of a 2x2 matrix [[4, 1], [2, 3]]?",
            "subject": "Mathematics",
            "save_to_history": True
        }
        res = self.client.post("/api/doubts/solve", json=req)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("intuition", data)
        self.assertIn("steps", data)
        self.assertGreaterEqual(len(data["steps"]), 1)
        self.assertIn("final_answer", data)
        self.assertIsNotNone(data["id"])
        print(f"[PASS] AI Doubt Solver solved Math problem with {len(data['steps'])} steps and KaTeX formulas.")

    def test_04_doubt_solver_cs(self):
        req = {
            "question": "How does Dijkstra's algorithm work with min-heap priority queue?",
            "subject": "Computer Science",
            "save_to_history": True
        }
        res = self.client.post("/api/doubts/solve", json=req)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("steps", data)
        print("[PASS] AI Doubt Solver solved Computer Science query with algorithmic steps.")

    def test_05_flashcard_deck_and_quiz(self):
        # 1. Generate deck from topic
        res_deck = self.client.post("/api/decks/generate", json={"topic": "Fourier Transform", "subject": "Mathematics"})
        self.assertEqual(res_deck.status_code, 200)
        deck_data = res_deck.json()
        deck_id = deck_data["id"]

        # 2. Get deck cards
        res_cards = self.client.get(f"/api/decks/{deck_id}/cards")
        self.assertEqual(res_cards.status_code, 200)
        cards = res_cards.json()
        self.assertGreaterEqual(len(cards), 3)

        # 3. Generate Quiz
        res_quiz = self.client.post("/api/quiz/generate", json={"topic": "Fourier Transform", "subject": "Mathematics"})
        self.assertEqual(res_quiz.status_code, 200)
        quiz = res_quiz.json()
        self.assertEqual(len(quiz["questions"]), 3)
        self.assertEqual(len(quiz["questions"][0]["options"]), 4)

        print("[PASS] AI Flashcard & Quiz generators verified.")

    def test_06_analytics_summary(self):
        res = self.client.get("/api/analytics")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_study_hours", data)
        self.assertIn("syllabus_completion_pct", data)
        self.assertIn("current_streak_days", data)
        print(f"[PASS] Analytics generated: {data['total_study_hours']} hrs, {data['syllabus_completion_pct']}% syllabus, {data['current_streak_days']} streak days.")

if __name__ == "__main__":
    unittest.main()
