"""
LinkedIn job search navigation and lazy-load scrolling.

Builds parameterised search URLs and scrolls the job list to
load all available cards before parsing.
"""

import random
import urllib.parse
from playwright.sync_api import Page, Locator, expect


class JobNavigator:
    """
    Navigates to LinkedIn job search results and scrolls to load all cards.

    Parameters
    ----------
    page : Page
        The active Playwright page (must be authenticated).
    keywords : list[str]
        Job title keywords to search for (e.g., ["AI Engineer"]).
    date_posted : str
        LinkedIn date filter code (e.g., "r86400" for past 24h).
    experience_level : str
        Comma-separated experience level codes (e.g., "2,3,4").
    """

    _BASE_URL = "https://www.linkedin.com/jobs/search/"

    def __init__(
        self,
        page: Page,
        keywords: list[str],
        date_posted: str = "r604800",
        experience_level: str = "2,3,4",
    ):
        self.page = page
        self.keywords = keywords
        self.date_posted = date_posted
        self.experience_level = experience_level

    def build_search_url(self, keyword: str) -> str:
        """
        Build a parameterised LinkedIn job search URL.

        Parameters
        ----------
        keyword : str
            The job title to search for.

        Returns
        -------
        str
            Fully-qualified search URL with Easy Apply filter enabled.
        """
        params = {
            "keywords": keyword,
            "f_AL": "true",  # Easy Apply filter
            "f_TPR": self.date_posted,
            "f_E": self.experience_level,
            "sortBy": "DD",  # Sort by date (most recent)
        }
        url = f"{self._BASE_URL}?{urllib.parse.urlencode(params)}"
        print(f"[Navigator] Built search URL: {url}")
        return url

    def navigate_to_search(self, keyword: str) -> str:
        """
        Navigate to the job search results page for a given keyword.

        Returns
        -------
        str
            The actual URL after navigation.
        """
        url = self.build_search_url(keyword)
        self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
        self.page.wait_for_load_state("networkidle", timeout=15000)
        print(f"[Navigator] Navigated to search results for '{keyword}'")
        return self.page.url

    def scroll_job_list(self, max_cards: int = 25) -> list[Locator]:
        """
        Scroll the left-hand job list container to trigger lazy-loading
        until all cards are rendered or the maximum is reached.

        Uses Playwright's native waiting — no time.sleep() calls.
        Randomised delays between scrolls mimic human behaviour.

        Parameters
        ----------
        max_cards : int
            Stop scrolling once this many cards are loaded (default 25,
            which is one full page on LinkedIn).

        Returns
        -------
        list[Locator]
            A list of Playwright Locator objects for each job card.
        """
        # Wait for the job list container to appear
        list_container = self.page.locator(
            ".jobs-search-results-list, "
            ".scaffold-layout__list, "
            '[class*="jobs-search-results"]'
        ).first

        expect(list_container).to_be_visible(timeout=10000)
        print("[Navigator] Job list container found — starting scroll.")

        # Selector for individual job cards
        card_selector = (
            ".job-card-container, "
            ".jobs-search-results__list-item, "
            '[class*="job-card-list"]'
        )

        previous_count = 0
        stale_scrolls = 0
        max_stale = 3  # Stop after N consecutive scrolls with no new cards

        while stale_scrolls < max_stale:
            # Scroll to bottom of the container
            list_container.evaluate("el => el.scrollTop = el.scrollHeight")

            # Wait for network requests triggered by the scroll
            self.page.wait_for_load_state("networkidle", timeout=10000)

            # Human-like random delay
            self.page.wait_for_timeout(random.randint(800, 1500))

            # Count current cards
            current_count = self.page.locator(card_selector).count()
            print(f"[Navigator] Scroll complete — {current_count} cards loaded.")

            if current_count >= max_cards:
                print(f"[Navigator] Reached max cards ({max_cards}). Stopping scroll.")
                break

            if current_count == previous_count:
                stale_scrolls += 1
                print(f"[Navigator] No new cards (stale scroll {stale_scrolls}/{max_stale}).")
            else:
                stale_scrolls = 0  # Reset on progress

            previous_count = current_count

        # Collect all card locators
        cards = self.page.locator(card_selector)
        total = cards.count()
        print(f"[Navigator] Scroll finished — {total} job cards ready for processing.")

        return [cards.nth(i) for i in range(total)]
