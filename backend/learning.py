import json

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from database import connect_db

router = APIRouter(prefix="/api", tags=["Learning and Assessments"])


class EnrollmentRequest(BaseModel):
    employee_id: int = Field(gt=0)
    course_id: int = Field(gt=0)


class ProgressRequest(BaseModel):
    progress: int = Field(ge=0, le=100)


class AssessmentRequest(BaseModel):
    employee_id: int = Field(gt=0)
    skill: str = Field(min_length=1, max_length=80)
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)


@router.get("/learning/courses")
def get_courses(skill: str | None = None):
    with connect_db() as db:
        if skill:
            rows = db.execute(
                "SELECT * FROM courses WHERE skill = ? ORDER BY id",
                (skill,)
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM courses ORDER BY id"
            ).fetchall()

        return {"courses": [dict(row) for row in rows]}


@router.get("/learning/enrollments")
def get_enrollments(employee_id: int | None = None):
    query = """
        SELECT en.id, en.employee_id, e.name AS employee_name,
               en.course_id, c.title AS course_title,
               c.skill, en.progress, en.status, en.created_at
        FROM enrollments en
        JOIN employees e ON e.id = en.employee_id
        JOIN courses c ON c.id = en.course_id
    """

    with connect_db() as db:
        if employee_id is not None:
            rows = db.execute(
                query + " WHERE en.employee_id = ? ORDER BY en.id DESC",
                (employee_id,)
            ).fetchall()
        else:
            rows = db.execute(
                query + " ORDER BY en.id DESC"
            ).fetchall()

        return {"enrollments": [dict(row) for row in rows]}


@router.post("/learning/enrollments", status_code=201)
def enroll_employee(request: EnrollmentRequest):
    with connect_db() as db:
        employee = db.execute(
            "SELECT id FROM employees WHERE id = ?",
            (request.employee_id,)
        ).fetchone()

        course = db.execute(
            "SELECT id FROM courses WHERE id = ?",
            (request.course_id,)
        ).fetchone()

        if not employee:
            raise HTTPException(404, "Employee not found.")

        if not course:
            raise HTTPException(404, "Course not found.")

        try:
            cursor = db.execute("""
                INSERT INTO enrollments (employee_id, course_id)
                VALUES (?, ?)
            """, (request.employee_id, request.course_id))
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise HTTPException(
                    409, "This employee is already enrolled in this course."
                )
            raise

        enrollment_id = cursor.lastrowid
        result = db.execute(
            "SELECT * FROM enrollments WHERE id = ?",
            (enrollment_id,)
        ).fetchone()

        return {
            "message": "Enrollment created successfully.",
            "enrollment": dict(result),
        }


@router.patch("/learning/enrollments/{enrollment_id}")
def update_progress(
    enrollment_id: int,
    request: ProgressRequest
):
    status = "Completed" if request.progress == 100 else "In Progress"

    with connect_db() as db:
        existing = db.execute(
            "SELECT id FROM enrollments WHERE id = ?",
            (enrollment_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(404, "Enrollment not found.")

        db.execute("""
            UPDATE enrollments
            SET progress = ?, status = ?
            WHERE id = ?
        """, (request.progress, status, enrollment_id))

        updated = db.execute(
            "SELECT * FROM enrollments WHERE id = ?",
            (enrollment_id,)
        ).fetchone()

        return {
            "message": "Learning progress updated.",
            "enrollment": dict(updated),
        }


@router.get("/assessments")
def get_assessments(
    employee_id: int | None = Query(default=None)
):
    query = """
        SELECT a.*, e.name AS employee_name
        FROM assessments a
        JOIN employees e ON e.id = a.employee_id
    """

    with connect_db() as db:
        if employee_id is not None:
            rows = db.execute(
                query + " WHERE a.employee_id = ? ORDER BY a.id DESC",
                (employee_id,)
            ).fetchall()
        else:
            rows = db.execute(
                query + " ORDER BY a.id DESC"
            ).fetchall()

        return {"assessments": [dict(row) for row in rows]}


@router.post("/assessments", status_code=201)
def submit_assessment(request: AssessmentRequest):
    if request.score > request.max_score:
        raise HTTPException(
            400, "Score cannot exceed the maximum score."
        )

    percentage = (request.score / request.max_score) * 100
    achieved_level = max(
        1, min(5, int((percentage / 100) * 5 + 0.9999))
    )

    with connect_db() as db:
        row = db.execute(
            "SELECT * FROM employees WHERE id = ?",
            (request.employee_id,)
        ).fetchone()

        if not row:
            raise HTTPException(404, "Employee not found.")

        skills = json.loads(row["skills_json"])
        old_level = int(skills.get(request.skill, 1))

        # A submitted assessment can raise the demo skill level.
        # It never lowers an employee's stored skill level.
        new_level = max(old_level, achieved_level)
        skills[request.skill] = new_level

        db.execute("""
            UPDATE employees
            SET skills_json = ?
            WHERE id = ?
        """, (json.dumps(skills), request.employee_id))

        cursor = db.execute("""
            INSERT INTO assessments
                (employee_id, skill, score, max_score, skill_level)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.employee_id,
            request.skill,
            request.score,
            request.max_score,
            achieved_level,
        ))

        saved = db.execute(
            "SELECT * FROM assessments WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()

        return {
            "message": "Assessment saved successfully.",
            "percentage": round(percentage, 2),
            "assessment": dict(saved),
            "previous_skill_level": old_level,
            "updated_skill_level": new_level,
            "note": (
                "The database employee profile was updated. "
                "Your existing skills.py demo data is separate."
            ),
        }