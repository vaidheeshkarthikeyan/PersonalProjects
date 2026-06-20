"""
LinkedIn authentication handler.

Manages login flow, session validation, and storage-state persistence.
Uses Playwright's native waiting — no time.sleep() calls.
"""

from playwright.sync_api import Page, expect, TimeoutError as PwTimeoutError


class AuthenticationError(Exception):
    """Raised when the login flow fails (bad credentials, CAPTCHA, 2FA)."""
    pass


class Authenticator:
    """
    Handles LinkedIn login and session validation.

    Parameters
    ----------
    page : Page
        The active Playwright page.
    email : str
        LinkedIn email (loaded from .env).
    password : str
        LinkedIn password (loaded from .env).
    """

    _LOGIN_URL = "https://www.linkedin.com/login"
    _FEED_URL = "https://www.linkedin.com/feed/"

    def __init__(self, page: Page, email: str, password: str):
        self.page = page
        self.email = email
        self.password = password

    def is_session_valid(self) -> bool:
        """
        Check whether the current browser session is authenticated.

        Navigates to the feed page and checks whether we stay there
        (logged in) or get redirected to login.
        """
        try:
            self.page.goto(self._FEED_URL, wait_until="domcontentloaded", timeout=15000)
            # If we land on the feed, the session is valid
            current_url = self.page.url
            is_valid = "/feed" in current_url and "/login" not in current_url
            print(f"[Auth] Session valid: {is_valid} (URL: {current_url})")
            return is_valid
        except PwTimeoutError:
            print("[Auth] Session check timed out — treating as invalid.")
            return False

    def login(self) -> None:
        """
        Execute the full LinkedIn login flow.

        Raises
        ------
        AuthenticationError
            If login fails for any reason (bad credentials, CAPTCHA, 2FA).
        """
        print("[Auth] Starting login flow...")

        # Navigate to login page
        self.page.goto(self._LOGIN_URL, wait_until="domcontentloaded", timeout=15000)

        # Fill email
        email_field = self.page.locator('input[id="username"]')
        expect(email_field).to_be_visible(timeout=10000)
        email_field.fill(self.email)

        # Fill password
        password_field = self.page.locator('input[id="password"]')
        expect(password_field).to_be_visible(timeout=5000)
        password_field.fill(self.password)

        # Click sign-in button
        sign_in_btn = self.page.locator('button[type="submit"]')
        expect(sign_in_btn).to_be_enabled(timeout=5000)
        sign_in_btn.click()

        # Wait for navigation — either success (feed) or failure (challenge/error)
        try:
            self.page.wait_for_url(
                "**/feed/**",
                timeout=30000,
                wait_until="domcontentloaded",
            )
            print("[Auth] Login successful — landed on feed.")
        except PwTimeoutError:
            current_url = self.page.url

            # Check for common failure modes
            if "checkpoint" in current_url or "challenge" in current_url:
                raise AuthenticationError(
                    "LinkedIn security challenge detected (CAPTCHA or 2FA). "
                    "Please log in manually in headed mode (HEADLESS=false), "
                    "then restart the bot to use the saved session."
                )

            if "login" in current_url:
                # Check for inline error messages
                error_msg = self.page.locator("#error-for-password, .alert-content")
                if error_msg.count() > 0:
                    error_text = error_msg.first.text_content() or "Unknown error"
                    raise AuthenticationError(
                        f"Login failed: {error_text.strip()}"
                    )

                raise AuthenticationError(
                    "Login failed — still on the login page after submission. "
                    "Check your credentials in .env."
                )

            # Unknown state
            raise AuthenticationError(
                f"Login failed — unexpected URL after submission: {current_url}"
            )

    def ensure_authenticated(self) -> None:
        """
        Validate the current session; if invalid, perform a fresh login.

        This is the main entry point — call this before starting automation.
        """
        if self.is_session_valid():
            print("[Auth] Using existing session.")
            return

        print("[Auth] Session expired or missing — performing fresh login.")
        self.login()
