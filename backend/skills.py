
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/skills", tags=["Skills"])


# --------------------------------------------------
# DEMO EMPLOYEE DATA
# --------------------------------------------------

EMPLOYEES = [
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


# --------------------------------------------------
# REQUIRED SKILL LEVELS
# --------------------------------------------------

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


# --------------------------------------------------
# DEMONSTRATION COURSE CATALOG
# --------------------------------------------------

COURSE_CATALOG = {
    "Python": {
        "title": "Python Programming Fundamentals",
        "provider": "CapacityConnect Learning",
        "duration": "4 weeks",
        "level": "Beginner to Intermediate",
    },
    "SQL": {
        "title": "SQL and Database Skills",
        "provider": "CapacityConnect Learning",
        "duration": "3 weeks",
        "level": "Beginner to Intermediate",
    },
    "Machine Learning": {
        "title": "Machine Learning Essentials",
        "provider": "CapacityConnect Learning",
        "duration": "6 weeks",
        "level": "Intermediate",
    },
    "Cloud Computing": {
        "title": "Cloud Computing Fundamentals",
        "provider": "CapacityConnect Learning",
        "duration": "4 weeks",
        "level": "Beginner to Intermediate",
    },
}


# --------------------------------------------------
# INTERNAL TRAINER DATA
# --------------------------------------------------

TRAINERS = [
    {
        "id": 101,
        "name": "Priya Mehta",
        "role": "Senior ML Engineer",
        "skills": {
            "Python": 5,
            "Machine Learning": 5,
            "SQL": 3,
        },
        "availability": "Available",
        "sessions_per_week": 4,
    },
    {
        "id": 102,
        "name": "Karan Singh",
        "role": "Cloud Architect",
        "skills": {
            "Cloud Computing": 5,
            "Python": 4,
            "SQL": 3,
        },
        "availability": "Available",
        "sessions_per_week": 3,
    },
    {
        "id": 103,
        "name": "Neha Sharma",
        "role": "Data Engineering Lead",
        "skills": {
            "SQL": 5,
            "Python": 4,
            "Machine Learning": 3,
        },
        "availability": "Limited",
        "sessions_per_week": 1,
    },
    {
        "id": 104,
        "name": "Aditya Verma",
        "role": "Software Development Lead",
        "skills": {
            "Python": 5,
            "SQL": 4,
            "Cloud Computing": 3,
        },
        "availability": "Available",
        "sessions_per_week": 3,
    },
]


# --------------------------------------------------
# SKILL-GAP ANALYSIS
# --------------------------------------------------

def analyze_employee(employee):
    """Calculate employee skill gaps and course recommendations."""

    required = ROLE_REQUIREMENTS.get(employee["role"], {})
    current_skills = employee["skills"]

    gaps = []
    recommendations = []

    for skill, required_level in required.items():
        current_level = current_skills.get(skill, 0)
        gap = max(required_level - current_level, 0)

        if gap == 0:
            continue

        if gap >= 2:
            severity = "High"
            priority = 1
        else:
            severity = "Medium"
            priority = 2

        gaps.append({
            "skill": skill,
            "current_level": current_level,
            "required_level": required_level,
            "gap": gap,
            "severity": severity,
            "priority": priority,
        })

        course = COURSE_CATALOG.get(skill)

        if course:
            recommendations.append({
                "skill": skill,
                "title": course["title"],
                "provider": course["provider"],
                "duration": course["duration"],
                "level": course["level"],
                "reason": (
                    f"Improve {skill} from level "
                    f"{current_level} to level {required_level}."
                ),
                "priority": priority,
                "severity": severity,
            })

    gaps.sort(key=lambda item: (-item["gap"], item["skill"]))
    recommendations.sort(
        key=lambda item: (item["priority"], item["skill"])
    )

    return {
        "employee_id": employee["id"],
        "employee_name": employee["name"],
        "role": employee["role"],
        "skills": current_skills,
        "required_skills": required,
        "gaps": gaps,
        "recommendations": recommendations,
        "total_gaps": len(gaps),
        "high_priority_gaps": sum(
            1 for gap in gaps if gap["severity"] == "High"
        ),
    }


# --------------------------------------------------
# SPECIFIC ROUTES FIRST
# Keep these above /{employee_id}.
# --------------------------------------------------

@router.get("/trainers")
def get_trainers():
    """Return all available trainer profiles."""
    return {"trainers": TRAINERS}


@router.get("/gaps")
def get_all_skill_gaps():
    """Return aggregate and individual skill-gap analyses."""

    analyses = [analyze_employee(employee) for employee in EMPLOYEES]

    all_gaps = [
        gap
        for analysis in analyses
        for gap in analysis["gaps"]
    ]

    all_recommendations = [
        {
            **course,
            "employee_id": analysis["employee_id"],
            "employee_name": analysis["employee_name"],
        }
        for analysis in analyses
        for course in analysis["recommendations"]
    ]

    return {
        "summary": {
            "employees_analyzed": len(analyses),
            "total_skill_gaps": len(all_gaps),
            "high_priority_gaps": sum(
                1 for gap in all_gaps
                if gap["severity"] == "High"
            ),
            "courses_recommended": len(all_recommendations),
        },
        "employees": analyses,
        "recommendations": all_recommendations,
    }


@router.get("/{employee_id}/trainers")
def match_trainers(employee_id: int, skill: str = None):
    """Recommend trainers for a specific employee and skill."""

    employee = next(
        (item for item in EMPLOYEES if item["id"] == employee_id),
        None,
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    analysis = analyze_employee(employee)

    if not skill:
        if not analysis["gaps"]:
            return {
                "employee_id": employee_id,
                "employee_name": employee["name"],
                "message": "No skill gaps found. No trainer required.",
                "matches": [],
            }

        skill = analysis["gaps"][0]["skill"]

    required_skills = ROLE_REQUIREMENTS.get(employee["role"], {})

    if skill not in required_skills:
        raise HTTPException(
            status_code=400,
            detail="Skill is not defined for this employee's role",
        )

    current_level = employee["skills"].get(skill, 0)
    required_level = required_skills[skill]

    matches = []

    for trainer in TRAINERS:
        trainer_level = trainer["skills"].get(skill, 0)

        if trainer_level <= current_level:
            continue

        if trainer["availability"] == "Unavailable":
            continue

        expertise_score = round((trainer_level / 5) * 70)

        availability_score = (
            30 if trainer["availability"] == "Available" else 15
        )

        match_score = min(
            expertise_score + availability_score,
            100,
        )

        matches.append({
            "trainer_id": trainer["id"],
            "name": trainer["name"],
            "role": trainer["role"],
            "skill": skill,
            "trainer_level": trainer_level,
            "employee_level": current_level,
            "required_level": required_level,
            "match_score": match_score,
            "availability": trainer["availability"],
            "sessions_per_week": trainer["sessions_per_week"],
        })

    matches.sort(
        key=lambda item: (
            item["match_score"],
            item["trainer_level"],
            item["sessions_per_week"],
        ),
        reverse=True,
    )

    return {
        "employee_id": employee_id,
        "employee_name": employee["name"],
        "skill": skill,
        "current_level": current_level,
        "required_level": required_level,
        "matches": matches,
    }


@router.get("/{employee_id}/gaps")
def get_employee_gaps(employee_id: int):
    """Return the skill-gap analysis for one employee."""

    employee = next(
        (item for item in EMPLOYEES if item["id"] == employee_id),
        None,
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    return analyze_employee(employee)


# --------------------------------------------------
# GENERAL ROUTES LAST
# --------------------------------------------------

@router.get("/")
def get_employees():
    """Return all demonstration employees."""
    return {"employees": EMPLOYEES}


@router.get("/{employee_id}")
def get_employee(employee_id: int):
    """Return one employee by ID."""

    employee = next(
        (item for item in EMPLOYEES if item["id"] == employee_id),
        None,
    )

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    return employee
