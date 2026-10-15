import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database import connect_db

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])

ROLE_REQUIREMENTS = {
    "Software Engineer": {
        "Python": 4,
        "SQL": 3,
        "Machine Learning": 3,
        "Cloud Computing": 3,
    },
    "Data Analyst": {
        "Python": 3,
        "SQL": 4,
        "Machine Learning": 3,
        "Cloud Computing": 2,
    },
    "Cloud Engineer": {
        "Python": 3,
        "SQL": 3,
        "Machine Learning": 2,
        "Cloud Computing": 4,
    },
}


class SimulationRequest(BaseModel):
    employee_id: int = Field(gt=0)
    skill: str = Field(min_length=1, max_length=80)
    training_hours: float = Field(ge=0, le=100)


class AssistantRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    employee_id: int | None = None


@router.post("/simulate")
def simulate_capacity(request: SimulationRequest):
    with connect_db() as db:
        employee = db.execute(
            "SELECT * FROM employees WHERE id = ?",
            (request.employee_id,)
        ).fetchone()

        if not employee:
            raise HTTPException(404, "Employee not found.")

        skills = json.loads(employee["skills_json"])
        current = int(skills.get(request.skill, 1))

        role_skills = ROLE_REQUIREMENTS.get(employee["role"], {})
        required = int(role_skills.get(request.skill, 3))

        gap_before = max(0, required - current)

        # Illustrative assumption: every 10 training hours may
        # improve a skill by one level, up to level 5.
        projected_gain = min(2, request.training_hours / 10)
        projected = min(5, round(current + projected_gain, 2))
        projected_gap = max(0, round(required - projected, 2))

        all_levels = list(skills.values())
        current_capacity = round(
            sum(all_levels) / (len(all_levels) * 5) * 100, 1
        )

        simulated_skills = dict(skills)
        simulated_skills[request.skill] = projected
        simulated_capacity = round(
            sum(simulated_skills.values())
            / (len(simulated_skills) * 5) * 100,
            1,
        )

        return {
            "employee_id": employee["id"],
            "employee_name": employee["name"],
            "role": employee["role"],
            "skill": request.skill,
            "training_hours": request.training_hours,
            "current_level": current,
            "required_level": required,
            "gap_before": gap_before,
            "projected_gain": round(projected - current, 2),
            "projected_level": projected,
            "projected_gap": projected_gap,
            "current_capacity_score": current_capacity,
            "projected_capacity_score": simulated_capacity,
            "capacity_change": round(
                simulated_capacity - current_capacity, 1
            ),
            "is_simulation": True,
            "assumption": (
                "Illustrative projection only: 10 training hours may "
                "increase a skill by one level, capped at level 5. "
                "This is not a scientifically validated forecast."
            ),
        }


@router.post("/assistant")
def ask_assistant(request: AssistantRequest):
    question = request.question.lower()

    employee = None
    skills = {}

    if request.employee_id is not None:
        with connect_db() as db:
            employee = db.execute(
                "SELECT * FROM employees WHERE id = ?",
                (request.employee_id,)
            ).fetchone()

        if not employee:
            raise HTTPException(404, "Employee not found.")

        skills = json.loads(employee["skills_json"])

    if any(word in question for word in ["gap", "weak", "missing"]):
        if employee:
            requirements = ROLE_REQUIREMENTS.get(employee["role"], {})
            gaps = {
                skill: max(0, level - int(skills.get(skill, 1)))
                for skill, level in requirements.items()
            }
            gaps = {
                skill: gap for skill, gap in gaps.items() if gap > 0
            }

            if gaps:
                ordered = sorted(
                    gaps.items(), key=lambda item: item[1], reverse=True
                )
                details = ", ".join(
                    f"{skill}: {gap} level(s) below target"
                    for skill, gap in ordered
                )
                answer = (
                    f"For {employee['name']}, the identified role-based "
                    f"skill gaps are: {details}. Consider targeted training "
                    "and a follow-up assessment."
                )
            else:
                answer = (
                    f"No gaps were identified for {employee['name']} "
                    "against the configured role requirements."
                )
        else:
            answer = (
                "Open the Skill Gap Analysis page to compare employee "
                "skills with their role requirements. Select an employee "
                "to get a personalized analysis."
            )

    elif any(word in question for word in ["course", "learn", "training"]):
        answer = (
            "Start with a course related to the employee's largest skill "
            "gap. Open Learning Management to browse courses, enroll an "
            "employee and update progress."
        )

    elif any(word in question for word in ["trainer", "mentor"]):
        answer = (
            "Open the Internal Trainer Matcher, select an employee and "
            "choose the skill they need to improve. Compare expertise, "
            "availability and match scores before selecting a trainer."
        )

    elif any(word in question for word in ["capacity", "simulate", "hours"]):
        answer = (
            "Open the Capacity Simulator, select an employee and skill, "
            "then enter the proposed training hours. The projection is "
            "illustrative and does not change the stored skill level."
        )

    elif any(word in question for word in ["assessment", "score", "test"]):
        answer = (
            "Open Assessments to record a score. The prototype stores the "
            "assessment and may raise the database skill level according "
            "to its simple score-to-level rule."
        )

    else:
        answer = (
            "I can help you navigate CapacityConnect. Ask about skill "
            "gaps, courses, trainers, capacity simulation or assessments. "
            "This assistant currently uses rules, not a language model."
        )

    return {
        "answer": answer,
        "assistant_type": "rule_based_demo",
        "employee": employee["name"] if employee else None,
    }