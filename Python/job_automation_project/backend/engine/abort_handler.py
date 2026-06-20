"""
Graceful application abort handler.

When the bot encounters an external redirect, unparseable form, or
any situation that prevents automatic completion, this module safely
closes the application modal and discards the draft.
"""

from playwright.sync_api import Page, expect, TimeoutError as PwTimeoutError


class AbortHandler:
    """
    Safely aborts an in-progress LinkedIn Easy Apply application.

    Locates the modal dismiss button, clicks it, confirms the discard
    dialog, and verifies the modal is fully closed.  Wrapped in
    try/except so a failed abort never crashes the main loop.
    """

    def abort_application(self, page: Page) -> bool:
        """
        Attempt to close the Easy Apply modal and discard the application.

        Parameters
        ----------
        page : Page
            The active Playwright page with an open Easy Apply modal.

        Returns
        -------
        bool
            True if the modal was successfully dismissed, False otherwise.
        """
        try:
            return self._perform_abort(page)
        except Exception as e:
            print(f"[Abort] Unexpected error during abort: {e}")
            # Last resort: try pressing Escape
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            except Exception:
                pass
            return False

    def _perform_abort(self, page: Page) -> bool:
        """Internal abort logic with full error propagation."""

        print("[Abort] Initiating application abort sequence...")

        # ----- Step 1: Find and click the modal dismiss button -----
        # LinkedIn uses several variants for the close/dismiss button
        dismiss_selectors = [
            'button[aria-label="Dismiss"]',
            'button[aria-label="Close"]',
            'button[data-test-modal-close-btn]',
            '.artdeco-modal__dismiss',
        ]

        dismiss_btn = None
        for selector in dismiss_selectors:
            candidate = page.locator(selector)
            if candidate.count() > 0 and candidate.first.is_visible():
                dismiss_btn = candidate.first
                break

        if dismiss_btn is None:
            print("[Abort] Could not locate dismiss button — abort failed.")
            return False

        dismiss_btn.click()
        print("[Abort] Clicked dismiss button.")

        # ----- Step 2: Handle the "Discard" confirmation dialog -----
        # LinkedIn shows a confirmation: "Discard" / "Save"
        try:
            discard_btn = page.get_by_role("button", name="Discard")
            expect(discard_btn).to_be_visible(timeout=5000)
            discard_btn.click()
            print("[Abort] Clicked 'Discard' confirmation.")
        except (PwTimeoutError, AssertionError):
            # Some modals close directly without a discard prompt
            print("[Abort] No discard dialog appeared — modal may have closed directly.")

        # ----- Step 3: Verify modal is fully closed -----
        try:
            modal = page.locator(".artdeco-modal, .jobs-easy-apply-modal")
            expect(modal).not_to_be_visible(timeout=5000)
            print("[Abort] Modal confirmed closed.")
            return True
        except (PwTimeoutError, AssertionError):
            print("[Abort] Warning: modal may still be visible after abort.")
            return False
