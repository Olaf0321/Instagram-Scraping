from playwright.sync_api import sync_playwright
from config import SITE_URL
import random
import pandas as pd

# Load usernames from CSV
file_path = 'demo_data.csv'
try:
    data = pd.read_csv(file_path)
    usernames = data['username']
except Exception as e:
    print(f"Error loading CSV file: {e}")
    usernames = []

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        # context = browser.new_context(
        #     user_agent=USER_AGENT,
        #     viewport={"width": random.randint(1200, 1400), "height": random.randint(700, 900)}
        # )
        page = browser.new_page()
        
        try:
            page.goto(SITE_URL, timeout=60000)
        except Exception as e:
            print(f"Error navigating to {SITE_URL}: {e}")
        
        page.wait_for_timeout(5000)
        
        try:
            input_element = page.locator(".input-element")
            for username in usernames:
                try:
                    input_element.click()
                    for _ in range(20):
                        input_element.press("Backspace")
                        page.wait_for_timeout(random.randint(100, 200))
                    
                    for char in username:
                        input_element.press(char)
                        page.wait_for_timeout(random.randint(100, 200))
                    
                    input_element.press("Enter")
                    print("Correctly entered!")
                    page.wait_for_timeout(10000)
                except Exception as e:
                    print(f"Error entering username {username}: {e}")
        except Exception as e:
            print(f"Error finding input element: {e}")
        
        browser.close()
except Exception as e:
    print(f"Unexpected error: {e}")