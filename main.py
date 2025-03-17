from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from config import USER_AGENT, SITE_URL
import random

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": random.randint(1200, 1400), "height": random.randint(700, 900)}
    )
    page = context.new_page()
    stealth_sync(page)
    page.goto(SITE_URL)


    browser.close()