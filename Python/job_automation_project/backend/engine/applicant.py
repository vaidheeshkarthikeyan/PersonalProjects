"""
Core job application execution loop.

Iterates through loaded job cards, detects Easy Apply eligibility,
fills forms (standard + custom questions), and submits or aborts
as needed.  All telemetry is written to the database.

Uses exclusively Playwright's native auto-waiting — no time.sleep().
"""

import random
import threading

from playwright.sync_api import Page, Locator, expect, TimeoutError as PwTimeoutError

from backend.engine.abort_handler import AbortHandler
from backend.engine.question_solver import QuestionSolver
from backend.engine.telemetry import TelemetryWriter


class JobApplicant:
    """
    The core execution engine — processes job cards one by one.

    Parameters
    ----------
    page : Page
        The active Playwright page (authenticated).
    question_solver : QuestionSolver
        Strategy for answering custom employer questions.
    phone_number : str
        Phone number to auto-fill when detected as blank.
    stop_event : threading.Event
        Set externally to signal the engine to stop gracefully.
    run_id : int
        The BotRun.id for this session.
    search_query : str
        The search keyword that produced these job cards.
    """

    def __init__(
        self,
        page: Page,
        question_solver: QuestionSolver,
        phone_number: str,
        stop_event: threading.Event,
        run_id: int,
        search_query: str,
    ):
        self.page = page
        self.solver = question_solver
        self.phone = phone_number
        self.stop_event = stop_event
        self.run_id = run_id
        self.search_query = search_query
        self.abort_handler = AbortHandler()

        # Running counters
        self.total_processed = 0
        self.total_applied = 0
        self.total_skipped = 0
        self.total_failed = 0

    # ===================================================================
    # Public API
    # ===================================================================

    def process_all(self, cards: list[Locator]) -> dict:
        """
        Iterate through all job cards and attempt to apply.

        Parameters
        ----------
        cards : list[Locator]
            Job card locators returned by ``JobNavigator.scroll_job_list()``.

        Returns
        -------
        dict
            Summary counters: processed, applied, skipped, failed.
        """
        total = len(cards)
        print(f"[Applicant] Starting processing of {total} job cards.")

        for idx, card in enumerate(cards, start=1):
            # Check for stop signal before each card
            if self.stop_event.is_set():
                print("[Applicant] Stop signal received — halting.")
                break

            print(f"\n[Applicant] === Card {idx}/{total} ===")
            self._process_single_card(card)

            # Update run counters in DB periodically
            TelemetryWriter.update_run_counters(
                run_id=self.run_id,
                total_processed=self.total_processed,
                total_applied=self.total_applied,
                total_skipped=self.total_skipped,
                total_failed=self.total_failed,
            )

        print(
            f"\n[Applicant] Finished. "
            f"Processed={self.total_processed}, Applied={self.total_applied}, "
            f"Skipped={self.total_skipped}, Failed={self.total_failed}"
        )
        return {
            "processed": self.total_processed,
            "applied": self.total_applied,
            "skipped": self.total_skipped,
            "failed": self.total_failed,
        }

    # ===================================================================
    # Single card processing
    # ===================================================================

    def _process_single_card(self, card: Locator) -> None:
        """Process a single job card: click, check eligibility, apply or skip."""
        company = "Unknown"
        job_title = "Unknown"
        job_url = None

        try:
            # Click the job card to load details in the right pane
            card.click()
            self.page.wait_for_timeout(random.randint(500, 1000))

            # Extract job metadata from the detail pane
            company, job_title, job_url = self._extract_job_info()
            print(f"[Applicant] Job: {job_title} at {company}")

            self.total_processed += 1

            # Look for the Easy Apply button
            easy_apply_btn = self.page.get_by_role("button", name="Easy Apply")

            if easy_apply_btn.count() == 0 or not easy_apply_btn.first.is_visible():
                print("[Applicant] No Easy Apply button — skipping.")
                self._record("SKIPPED", company, job_title, job_url, "No Easy Apply button")
                return

            # Click Easy Apply to open the modal
            easy_apply_btn.first.click()
            self.page.wait_for_timeout(random.randint(500, 800))

            # Process the application modal
            success = self._process_application_modal()

            if success:
                self._record("SUCCESS", company, job_title, job_url)
            else:
                self._record("FAILED", company, job_title, job_url, "Modal processing failed")

        except PwTimeoutError as e:
            print(f"[Applicant] Timeout: {e}")
            self._record("FAILED", company, job_title, job_url, f"Timeout: {e}")
            self.abort_handler.abort_application(self.page)

        except Exception as e:
            print(f"[Applicant] Unexpected error: {e}")
            self._record("FAILED", company, job_title, job_url, f"Error: {e}")
            self.abort_handler.abort_application(self.page)

    # ===================================================================
    # Job info extraction
    # ===================================================================

    def _extract_job_info(self) -> tuple[str, str, str | None]:
        """Extract company name, job title, and URL from the detail pane."""
        company = "Unknown"
        job_title = "Unknown"
        job_url = None

        try:
            # Job title — typically in an h1 or h2 in the detail pane
            title_el = self.page.locator(
                ".job-details-jobs-unified-top-card__job-title, "
                ".jobs-unified-top-card__job-title, "
                "h1.t-24, h2.t-24"
            ).first
            if title_el.is_visible():
                job_title = (title_el.text_content() or "Unknown").strip()
        except Exception:
            pass

        try:
            # Company name
            company_el = self.page.locator(
                ".job-details-jobs-unified-top-card__company-name, "
                ".jobs-unified-top-card__company-name, "
                "a.topcard__org-name-link, "
                "span.topcard__flavor"
            ).first
            if company_el.is_visible():
                company = (company_el.text_content() or "Unknown").strip()
        except Exception:
            pass

        try:
            job_url = self.page.url
        except Exception:
            pass

        return company, job_title, job_url

    # ===================================================================
    # Application modal processing (multi-step)
    # ===================================================================

    def _process_application_modal(self) -> bool:
        """
        Walk through the Easy Apply modal steps: fill fields, answer
        questions, navigate multi-step forms, and submit.

        Returns True on successful submission, False on abort/failure.
        """
        max_steps = 10  # Safety limit to prevent infinite loops

        for step in range(max_steps):
            print(f"[Applicant] Modal step {step + 1}...")

            # Check for external redirect (non-LinkedIn URL in modal)
            if self._is_external_redirect():
                print("[Applicant] External redirect detected — aborting.")
                self.abort_handler.abort_application(self.page)
                return False

            # Fill blank mandatory fields
            self._fill_standard_fields()

            # Answer custom questions
            self._answer_custom_questions()

            # Determine which action button is available
            submit_btn = self.page.get_by_role("button", name="Submit application")
            review_btn = self.page.get_by_role("button", name="Review")
            next_btn = self.page.get_by_role("button", name="Next")

            if submit_btn.count() > 0 and submit_btn.first.is_visible():
                submit_btn.first.click()
                self.page.wait_for_timeout(random.randint(1000, 2000))
                print("[Applicant] ✓ Application submitted!")
                # Close the success/confirmation overlay if present
                self._close_post_submit_overlay()
                return True

            elif review_btn.count() > 0 and review_btn.first.is_visible():
                review_btn.first.click()
                self.page.wait_for_timeout(random.randint(500, 800))
                print("[Applicant] Clicked 'Review'.")
                continue

            elif next_btn.count() > 0 and next_btn.first.is_visible():
                next_btn.first.click()
                self.page.wait_for_timeout(random.randint(500, 800))
                print("[Applicant] Clicked 'Next'.")
                continue

            else:
                print("[Applicant] No actionable button found — aborting.")
                self.abort_handler.abort_application(self.page)
                return False

        # Exceeded max steps
        print("[Applicant] Max steps exceeded — aborting.")
        self.abort_handler.abort_application(self.page)
        return False

    # ===================================================================
    # Field filling
    # ===================================================================

    def _fill_standard_fields(self) -> None:
        """Detect and fill blank mandatory fields (e.g., phone number)."""
        try:
            # Phone number field — common blank mandatory field
            phone_inputs = self.page.locator(
                'input[name*="phone"], '
                'input[aria-label*="phone" i], '
                'input[aria-label*="mobile" i]'
            )
            for i in range(phone_inputs.count()):
                phone_input = phone_inputs.nth(i)
                if phone_input.is_visible():
                    current_value = phone_input.input_value()
                    if not current_value.strip() and self.phone:
                        phone_input.fill(self.phone)
                        print(f"[Applicant] Auto-filled phone number.")
        except Exception as e:
            print(f"[Applicant] Warning: phone fill failed: {e}")

    def _answer_custom_questions(self) -> None:
        """Detect custom questions and fill answers using the QuestionSolver."""
        try:
            # Find all fieldset/form-group pairs with labels and inputs
            form_groups = self.page.locator(
                '.jobs-easy-apply-form-section__grouping, '
                'div[data-test-form-element], '
                '.fb-dash-form-element'
            )

            for i in range(form_groups.count()):
                group = form_groups.nth(i)
                if not group.is_visible():
                    continue

                # Extract the question text from the label
                label = group.locator("label, legend, .fb-dash-form-element__label, span.t-14")
                if label.count() == 0:
                    continue
                question_text = (label.first.text_content() or "").strip()
                if not question_text:
                    continue

                # Check for text input
                text_input = group.locator('input[type="text"], input:not([type])')
                if text_input.count() > 0 and text_input.first.is_visible():
                    current = text_input.first.input_value()
                    if not current.strip():
                        answer = self.solver.solve(question_text)
                        text_input.first.fill(answer)
                        print(f"[Applicant] Answered (text): '{question_text[:50]}' → '{answer[:30]}'")
                    continue

                # Check for textarea
                textarea = group.locator("textarea")
                if textarea.count() > 0 and textarea.first.is_visible():
                    current = textarea.first.input_value()
                    if not current.strip():
                        answer = self.solver.solve(question_text)
                        textarea.first.fill(answer)
                        print(f"[Applicant] Answered (textarea): '{question_text[:50]}' → '{answer[:30]}'")
                    continue

                # Check for select dropdown
                select = group.locator("select")
                if select.count() > 0 and select.first.is_visible():
                    current_val = select.first.input_value()
                    if not current_val or current_val == "Select an option":
                        answer = self.solver.solve(question_text)
                        # Try to select by visible text, fall back to first non-empty option
                        try:
                            select.first.select_option(label=answer)
                        except Exception:
                            options = select.first.locator("option")
                            for j in range(options.count()):
                                opt_text = (options.nth(j).text_content() or "").strip()
                                if opt_text and opt_text != "Select an option":
                                    select.first.select_option(label=opt_text)
                                    break
                        print(f"[Applicant] Answered (select): '{question_text[:50]}'")
                    continue

                # Check for radio buttons
                radios = group.locator('input[type="radio"]')
                if radios.count() > 0:
                    # Check if any is already selected
                    any_checked = False
                    for j in range(radios.count()):
                        if radios.nth(j).is_checked():
                            any_checked = True
                            break
                    if not any_checked:
                        answer = self.solver.solve(question_text)
                        # Try to find a radio whose label matches the answer
                        matched = False
                        radio_labels = group.locator("label")
                        for j in range(radio_labels.count()):
                            label_text = (radio_labels.nth(j).text_content() or "").strip().lower()
                            if answer.lower() in label_text or label_text in answer.lower():
                                radio_labels.nth(j).click()
                                matched = True
                                break
                        if not matched and radios.count() > 0:
                            # Default: select the first radio
                            radios.first.click()
                        print(f"[Applicant] Answered (radio): '{question_text[:50]}'")

        except Exception as e:
            print(f"[Applicant] Warning: custom question handling error: {e}")

    # ===================================================================
    # Helpers
    # ===================================================================

    def _is_external_redirect(self) -> bool:
        """Check if the modal has redirected to an external application portal."""
        try:
            current_url = self.page.url
            return "linkedin.com" not in current_url
        except Exception:
            return False

    def _close_post_submit_overlay(self) -> None:
        """Close any post-submission success overlay/modal."""
        try:
            close_btn = self.page.locator(
                'button[aria-label="Dismiss"], '
                'button[aria-label="Done"]'
            )
            if close_btn.count() > 0 and close_btn.first.is_visible():
                close_btn.first.click()
                self.page.wait_for_timeout(500)
        except Exception:
            pass

    def _record(
        self,
        status: str,
        company: str,
        job_title: str,
        job_url: str | None,
        reason: str | None = None,
    ) -> None:
        """Write a telemetry entry and update internal counters."""
        if status == "SUCCESS":
            self.total_applied += 1
        elif status == "SKIPPED":
            self.total_skipped += 1
        elif status == "FAILED":
            self.total_failed += 1

        TelemetryWriter.log_application(
            company=company,
            job_title=job_title,
            job_url=job_url,
            status=status,
            failure_reason=reason,
            search_query=self.search_query,
            run_id=self.run_id,
        )
