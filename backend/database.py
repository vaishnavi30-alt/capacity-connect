import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "capacityconnect.db"

DEMO_EMPLOYEES = [
    {
        "id": 1,
        "name": "Aarav Sharma",
        "role": "Software Engineer",
        "skills": {
            "Python": 4,
            "SQL": 3,
            "Machine Learning": 2,
            "Cloud Computing": 2,
        },
    },
    {
        "id": 2,
        "name": "Ananya Verma",
        "role": "Data Analyst",
        "skills": {
            "Python": 3,
            "SQL": 4,
            "Machine Learning": 3,
            "Cloud Computing": 1,
        },
    },
    {
        "id": 3,
        "name": "Rohan Mehta",
        "role": "Cloud Engineer",
        "skills": {
            "Python": 2,
            "SQL": 2,
            "Machine Learning": 1,
            "Cloud Computing": 4,
        },
    },
]

DEMO_COURSES = [
    (
        1, "Python for Professionals", "Python", "Beginner",
        8, "CapacityConnect Academy",
        "Build Python programming fundamentals through practical exercises."
    ),
    (
        2, "Advanced SQL and Database Design", "SQL", "Intermediate",
        10, "CapacityConnect Academy",
        "Practice queries, joins, database design and data analysis."
    ),
    (
        3, "Machine Learning Foundations", "Machine Learning", "Beginner",
        12, "CapacityConnect Academy",
        "Learn supervised learning, model evaluation and core ML concepts."
    ),
    (
        4, "Cloud Computing Essentials", "Cloud Computing", "Beginner",
        9, "CapacityConnect Academy",
        "Understand cloud infrastructure, deployment and essential services."
    ),
    (
        5, "Applied Machine Learning", "Machine Learning", "Intermediate",
        15, "CapacityConnect Academy",
        "Explore model training, feature engineering and evaluation."
    ),
    (
        6, "Python Data Analysis", "Python", "Intermediate",
        10, "CapacityConnect Academy",
        "Work with datasets, data cleaning and analytical workflows."
    ),
]


def connect_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with connect_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                role TEXT NOT NULL,
                skills_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                skill TEXT NOT NULL,
                level TEXT NOT NULL,
                duration_hours INTEGER NOT NULL,
                provider TEXT NOT NULL,
                description TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                progress INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Enrolled',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(employee_id, course_id),
                FOREIGN KEY(employee_id) REFERENCES employees(id),
                FOREIGN KEY(course_id) REFERENCES courses(id)
            );

            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                skill TEXT NOT NULL,
                score REAL NOT NULL,
                max_score REAL NOT NULL,
                skill_level INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            );
        """)

        for employee in DEMO_EMPLOYEES:
            db.execute("""
                INSERT OR IGNORE INTO employees
                    (id, name, role, skills_json)
                VALUES (?, ?, ?, ?)
            """, (
                employee["id"],
                employee["name"],
                employee["role"],
                json.dumps(employee["skills"]),
            ))

        for course in DEMO_COURSES:
            db.execute("""
                INSERT OR IGNORE INTO courses
                    (id, title, skill, level, duration_hours,
                     provider, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, course)


def row_to_dict(row):
    return dict(row) if row else None