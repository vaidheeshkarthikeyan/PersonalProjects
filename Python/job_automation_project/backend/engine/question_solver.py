"""
Intelligent question solver for LinkedIn Easy Apply custom questions.

Architecture
------------
1. **RuleBasedSolver** (primary): Fast, deterministic keyword matching
   against a structured developer profile JSON.
2. **OpenAISolver** (fallback): Sends unrecognised questions to GPT for
   contextual answers.  Gracefully degrades if API key is missing.

Both implement the ``QuestionSolver`` abstract interface.
"""

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path


class QuestionSolver(ABC):
    """Abstract interface for question-answering strategies."""

    @abstractmethod
    def solve(self, question_text: str) -> str:
        """
        Given the text of a custom question, return an appropriate answer.

        Parameters
        ----------
        question_text : str
            The full text of the question as displayed on the form.

        Returns
        -------
        str
            The answer to fill into the form field.
        """
        ...


# ===================================================================
# Rule-Based Solver (Primary)
# ===================================================================

class RuleBasedSolver(QuestionSolver):
    """
    Matches questions to profile values using regex keyword patterns.

    Loads the developer's structured profile and maps common question
    categories (experience, authorisation, start date, etc.) to the
    correct profile field.

    Parameters
    ----------
    profile_path : str
        Absolute path to the ``developer_profile.json`` file.
    fallback_solver : QuestionSolver | None
        Optional secondary solver for questions that don't match any rule.
    """

    # Each rule: (compiled regex pattern, profile field key, optional transform)
    _RULES: list[tuple[str, str]] = [
        # Years of experience
        (r"(?:how many|number of)\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)", "years_experience"),
        (r"years?\s*(?:of)?\s*(?:work|professional|relevant)?\s*experience", "years_experience"),

        # Work authorisation
        (r"(?:authorized?|authorised?|eligible|legally)\s*(?:to)?\s*work", "work_authorization"),
        (r"work\s*(?:authorization|authorisation|permit|visa)", "work_authorization"),
        (r"require\s*(?:visa|sponsorship)", "requires_sponsorship"),
        (r"(?:visa|sponsorship)\s*(?:required|needed|necessary)", "requires_sponsorship"),

        # Start date / availability
        (r"(?:start|begin|join)\s*(?:date|when|earliest)", "start_date"),
        (r"(?:when|how soon)\s*(?:can you|could you)\s*(?:start|begin|join)", "start_date"),
        (r"(?:notice period|availability)", "start_date"),

        # Salary expectation
        (r"(?:salary|compensation|pay)\s*(?:expectation|requirement|range|desired)", "salary_expectation"),
        (r"(?:expected|desired|minimum)\s*(?:salary|compensation|pay|ctc)", "salary_expectation"),

        # Education / degree
        (r"(?:highest|latest|most recent)\s*(?:degree|education|qualification)", "education"),
        (r"(?:degree|diploma|certification|educational)\s*(?:level|background)", "education"),

        # Location / relocation
        (r"(?:current|present)\s*(?:location|city|address)", "location"),
        (r"(?:willing|open)\s*(?:to)?\s*(?:relocate|relocation)", "willing_to_relocate"),

        # LinkedIn / portfolio URLs
        (r"(?:linkedin|linked\s*in)\s*(?:url|profile|link)", "linkedin_url"),
        (r"(?:portfolio|website|github|personal)\s*(?:url|link|site)", "portfolio_url"),

        # Phone / contact
        (r"(?:phone|mobile|cell|contact)\s*(?:number)?", "phone"),

        # Gender / demographic (answer "Prefer not to say" by default)
        (r"(?:gender|sex|race|ethnicity|veteran|disability)", "demographic_response"),

        # Cover letter / additional info
        (r"(?:cover letter|why (?:are you|do you)|tell us about|describe)", "cover_letter_short"),

        # Proficiency / skill level
        (r"(?:proficiency|proficient|experience)\s*(?:with|in|using)\s*(?:python|java|sql|tensorflow|pytorch)", "skill_proficiency"),
    ]

    def __init__(self, profile_path: str, fallback_solver: "QuestionSolver | None" = None):
        self.profile = self._load_profile(profile_path)
        self.fallback = fallback_solver

        # Pre-compile regex patterns
        self._compiled_rules = [
            (re.compile(pattern, re.IGNORECASE), field)
            for pattern, field in self._RULES
        ]

        print(f"[QuestionSolver] Loaded profile with {len(self.profile)} fields.")

    @staticmethod
    def _load_profile(path: str) -> dict:
        """Load and parse the developer profile JSON."""
        profile_path = Path(path)
        if not profile_path.exists():
            print(f"[QuestionSolver] WARNING: Profile not found at {path} — using empty profile.")
            return {}
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def solve(self, question_text: str) -> str:
        """
        Match the question against known patterns and return the profile value.

        Falls back to the secondary solver (OpenAI) if no rule matches.
        """
        question_clean = question_text.strip().lower()

        for pattern, field_key in self._compiled_rules:
            if pattern.search(question_clean):
                value = self.profile.get(field_key)
                if value is not None:
                    answer = str(value)
                    print(f"[QuestionSolver] Rule match: '{field_key}' → '{answer}'")
                    return answer

        # No rule matched — try fallback
        if self.fallback:
            print(f"[QuestionSolver] No rule matched. Delegating to fallback solver.")
            return self.fallback.solve(question_text)

        print(f"[QuestionSolver] No rule matched and no fallback. Question: '{question_text[:80]}...'")
        return "N/A"


# ===================================================================
# OpenAI Solver (Fallback)
# ===================================================================

class OpenAISolver(QuestionSolver):
    """
    Uses OpenAI GPT to answer questions that the rule-based solver can't handle.

    Gracefully degrades: if the API key is missing or the call fails,
    returns "N/A" and logs the question for manual review.

    Parameters
    ----------
    api_key : str
        OpenAI API key.  If empty, all calls return "N/A".
    model : str
        Model to use (default: "gpt-4o-mini" for cost efficiency).
    profile : dict
        The developer profile for context injection.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", profile: dict | None = None):
        self.api_key = api_key
        self.model = model
        self.profile = profile or {}
        self._client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
                print("[OpenAISolver] Initialised with model: " + self.model)
            except ImportError:
                print("[OpenAISolver] WARNING: openai package not installed. Fallback disabled.")
            except Exception as e:
                print(f"[OpenAISolver] WARNING: Failed to initialise: {e}")
        else:
            print("[OpenAISolver] No API key provided — fallback disabled (will return 'N/A').")

    def solve(self, question_text: str) -> str:
        """Send the question to OpenAI GPT with profile context."""
        if not self._client:
            print(f"[OpenAISolver] Skipped (no client). Question: '{question_text[:80]}...'")
            return "N/A"

        try:
            profile_context = json.dumps(self.profile, indent=2)
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a job application assistant. Answer the following "
                            "employer question concisely (≤50 words) and factually, "
                            "based ONLY on the candidate's profile below. "
                            "If the profile doesn't contain relevant info, respond "
                            "with a professional, generic answer.\n\n"
                            f"CANDIDATE PROFILE:\n{profile_context}"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Employer question: {question_text}",
                    },
                ],
                max_tokens=100,
                temperature=0.3,
            )
            answer = response.choices[0].message.content.strip()
            print(f"[OpenAISolver] Answer: '{answer[:80]}...'")
            return answer

        except Exception as e:
            print(f"[OpenAISolver] API call failed: {e}")
            return "N/A"
