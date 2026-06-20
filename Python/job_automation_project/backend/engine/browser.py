"""
Playwright browser lifecycle manager.

Handles browser launch, stealth configuration, and clean teardown.
Supports both headless and headed modes via the HEADLESS env var.
"""

import random
from pathlib import Path
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


class BrowserManager:
    """
    Context manager that owns the Playwright browser lifecycle.

    Usage::

        with BrowserManager(headless=True, storage_state_path="state.json") as bm:
            page = bm.page
            page.goto("https://www.linkedin.com")
            # ... automation logic ...

    On exit, the browser context's storage state is saved and resources
    are released cleanly.
    """

    # Realistic desktop viewports to rotate through
    _VIEWPORTS = [
        {"width": 1280, "height": 800},
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
        {"width": 1536, "height": 864},
        {"width": 1920, "height": 1080},
    ]

    # Realistic user-agent strings (Chrome on Windows)
    _USER_AGENTS = [
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
    ]

    def __init__(self, headless: bool = True, storage_state_path: str | None = None):
        """
        Parameters
        ----------
        headless : bool
            Launch in headless mode if True.
        storage_state_path : str | None
            Path to a JSON file for persisting cookies / localStorage
            across runs.  If the file exists, it is loaded on launch.
        """
        self.headless = headless
        self.storage_state_path = storage_state_path

        # Will be initialised in __enter__
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    # ----- context manager protocol -----

    def __enter__(self) -> "BrowserManager":
        self._playwright = sync_playwright().start()

        # Choose random stealth parameters
        viewport = random.choice(self._VIEWPORTS)
        user_agent = random.choice(self._USER_AGENTS)

        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        # Build context kwargs
        ctx_kwargs = {
            "viewport": viewport,
            "user_agent": user_agent,
            "locale": "en-US",
            "timezone_id": "America/New_York",
            "permissions": [],  # deny all permission prompts
        }

        # Load existing session state if available
        if (
            self.storage_state_path
            and Path(self.storage_state_path).exists()
        ):
            ctx_kwargs["storage_state"] = self.storage_state_path
            print(f"[Browser] Loaded session state from {self.storage_state_path}")

        self._context = self._browser.new_context(**ctx_kwargs)

        # Mask the navigator.webdriver flag (basic anti-detection)
        self._context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            """
        )

        self._page = self._context.new_page()
        print(
            f"[Browser] Launched (headless={self.headless}, "
            f"viewport={viewport['width']}x{viewport['height']})"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Persist session state before closing
        if self._context and self.storage_state_path:
            try:
                self._context.storage_state(path=self.storage_state_path)
                print(f"[Browser] Saved session state to {self.storage_state_path}")
            except Exception as e:
                print(f"[Browser] Warning: could not save session state: {e}")

        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

        print("[Browser] Shutdown complete.")
        return False  # Do not suppress exceptions

    # ----- public accessors -----

    @property
    def page(self) -> Page:
        """The active Playwright page."""
        if self._page is None:
            raise RuntimeError("BrowserManager not initialised — use as a context manager.")
        return self._page

    @property
    def context(self) -> BrowserContext:
        """The active browser context."""
        if self._context is None:
            raise RuntimeError("BrowserManager not initialised — use as a context manager.")
        return self._context
