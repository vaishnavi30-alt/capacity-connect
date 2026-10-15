
import json
import urllib.error
import urllib.request

from skills import ROLE_REQUIREMENTS, analyze_employee

BASE_URL = "http://127.0.0.1:8000"

# E1: Test actual GET API endpoints.
ENDPOINTS = [
    "/",
    "/api/dashboard",
    "/api/skills/",
    "/api/skills/gaps",
    "/api/skills/trainers",
    "/api/skills/1/trainers?skill=Machine%20Learning",
    "/api/learning/courses",
    "/api/learning/enrollments",
    "/api/assessments",
]

print("\n========== E1: API ROUTE TESTS ==========")

for endpoint in ENDPOINTS:
    try:
        request = urllib.request.Request(BASE_URL + endpoint)
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            print(f"\n{endpoint}")
            print(f"HTTP status: {response.status}")
            print(f"Response: {body[:300]}")

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        print(f"\n{endpoint}")
        print(f"HTTP status: {error.code}")
        print(f"Error: {body[:300]}")

    except Exception as error:
        print(f"\n{endpoint}")
        print(f"Request failed: {error}")

# E2: Test skill-gap calculation through the real function.
print("\n========== E2: SKILL-GAP TESTS ==========")

test_cases = [
    (2, 4, 2),
    (3, 4, 1),
    (4, 4, 0),
    (5, 3, 0),
    (1, 5, 4),
]

test_role = "__TemporarySkillGapTest__"

try:
    for index, (current, required, expected) in enumerate(
        test_cases, start=1
    ):
        skill = f"TestSkill{index}"

        ROLE_REQUIREMENTS[test_role] = {skill: required}

        employee = {
            "id": 999,
            "name": "Temporary Test Employee",
            "role": test_role,
            "skills": {skill: current},
        }

        result = analyze_employee(employee)

        matching_gap = next(
            (item["gap"] for item in result["gaps"]
             if item["skill"] == skill),
            0,
        )

        passed = matching_gap == expected

        print(
            f"Case {index}: current={current}, required={required}, "
            f"expected={expected}, actual={matching_gap}, "
            f"result={'PASS' if passed else 'FAIL'}"
        )

finally:
    ROLE_REQUIREMENTS.pop(test_role, None)

print("\n========== TEST RUN FINISHED ==========")
print("Save this terminal output for your research paper.")
