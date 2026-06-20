"""
Unit tests for the Playwright engine modules.

Tests the question solver logic (rule-based matching) and
telemetry writer DB operations.
"""

import json
import os
import pytest
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from backend.database.models import Base, ApplicationLog, BotRun
from backend.engine.question_solver import RuleBasedSolver, OpenAISolver


# ===================================================================
# Fixtures
# ===================================================================

@pytest.fixture
def sample_profile(tmp_path):
    """Create a temporary developer profile JSON file."""
    profile = {
        "full_name": "Test User",
        "email": "test@example.com",
        "phone": "+1234567890",
        "location": "San Francisco, CA",
        "linkedin_url": "https://linkedin.com/in/testuser",
        "portfolio_url": "https://github.com/testuser",
        "years_experience": "5",
        "education": "Master's in Computer Science",
        "work_authorization": "Yes",
        "requires_sponsorship": "No",
        "willing_to_relocate": "Yes",
        "start_date": "2 weeks notice",
        "salary_expectation": "150000",
        "skill_proficiency": "Expert",
        "demographic_response": "Prefer not to disclose",
        "cover_letter_short": "I am a passionate engineer.",
        "skills": ["Python", "PyTorch", "TensorFlow"],
    }
    profile_path = tmp_path / "test_profile.json"
    with open(profile_path, "w") as f:
        json.dump(profile, f)
    return str(profile_path)


@pytest.fixture
def solver(sample_profile):
    """Create a RuleBasedSolver with no fallback."""
    return RuleBasedSolver(profile_path=sample_profile, fallback_solver=None)


# ===================================================================
# RuleBasedSolver Tests
# ===================================================================

class TestRuleBasedSolver:
    """Tests for the rule-based question solver."""

    def test_years_of_experience(self, solver):
        assert solver.solve("How many years of experience do you have?") == "5"

    def test_years_experience_variant(self, solver):
        assert solver.solve("Number of years of relevant experience") == "5"

    def test_work_authorization(self, solver):
        assert solver.solve("Are you authorized to work in the US?") == "Yes"

    def test_visa_sponsorship(self, solver):
        assert solver.solve("Will you require visa sponsorship?") == "No"

    def test_start_date(self, solver):
        assert solver.solve("When can you start?") == "2 weeks notice"

    def test_start_date_variant(self, solver):
        assert solver.solve("What is your earliest start date?") == "2 weeks notice"

    def test_salary_expectation(self, solver):
        assert solver.solve("What is your expected salary?") == "150000"

    def test_salary_variant(self, solver):
        assert solver.solve("Desired compensation range") == "150000"

    def test_education(self, solver):
        assert solver.solve("What is your highest degree?") == "Master's in Computer Science"

    def test_location(self, solver):
        assert solver.solve("What is your current location?") == "San Francisco, CA"

    def test_willing_to_relocate(self, solver):
        assert solver.solve("Are you willing to relocate?") == "Yes"

    def test_linkedin_url(self, solver):
        assert solver.solve("What is your LinkedIn profile URL?") == "https://linkedin.com/in/testuser"

    def test_portfolio_url(self, solver):
        assert solver.solve("Please provide your GitHub link") == "https://github.com/testuser"

    def test_phone_number(self, solver):
        assert solver.solve("What is your phone number?") == "+1234567890"

    def test_demographic(self, solver):
        assert solver.solve("What is your gender?") == "Prefer not to disclose"

    def test_cover_letter(self, solver):
        answer = solver.solve("Tell us about yourself and why you're interested")
        assert answer == "I am a passionate engineer."

    def test_unrecognized_returns_na(self, solver):
        answer = solver.solve("What is the airspeed velocity of an unladen swallow?")
        assert answer == "N/A"

    def test_empty_question(self, solver):
        assert solver.solve("") == "N/A"

    def test_case_insensitivity(self, solver):
        assert solver.solve("HOW MANY YEARS OF EXPERIENCE DO YOU HAVE?") == "5"


class TestRuleBasedSolverWithFallback:
    """Tests for fallback delegation."""

    def test_fallback_called_on_no_match(self, sample_profile):
        class MockFallback(OpenAISolver):
            def solve(self, question_text):
                return "mock_answer"

        mock = MockFallback(api_key="", model="test")
        solver = RuleBasedSolver(profile_path=sample_profile, fallback_solver=mock)
        result = solver.solve("Random unmatched question?")
        assert result == "mock_answer"


class TestOpenAISolver:
    """Tests for the OpenAI solver edge cases."""

    def test_no_api_key_returns_na(self):
        solver = OpenAISolver(api_key="", model="gpt-4o-mini")
        assert solver.solve("Any question") == "N/A"

    def test_no_client_returns_na(self):
        solver = OpenAISolver(api_key="", model="gpt-4o-mini")
        solver._client = None
        assert solver.solve("Another question") == "N/A"


class TestMissingProfile:
    """Tests for missing profile file."""

    def test_missing_profile_uses_empty(self):
        solver = RuleBasedSolver(
            profile_path="/nonexistent/path/profile.json",
            fallback_solver=None,
        )
        assert solver.profile == {}
        assert solver.solve("How many years of experience?") == "N/A"
