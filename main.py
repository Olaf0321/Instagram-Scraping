from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import pandas as pd
import os
import pytz
import datetime
import csv
from config import SITE_URL

# Define the CSV file name
csv_file = "demo_output_part.csv"

# Path to ChromeDriver
chromedriver_path = "C:/chromedriver-win64/chromedriver.exe"  # Replace with your ChromeDriver path

# Configure WebDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--ignore-ssl-errors")
chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

service = Service(chromedriver_path, port=9515)
driver = webdriver.Chrome(service=service, options=chrome_options)

# define HEADERS
HEADERS = [
    'ユーザー名',
    '経歴',
    'フォロワー数',
    'フォロー数',
    'メディア数'
]
arr = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
for item in arr:
    HEADERS.append(f'メディア-{item}-投稿ID')
    HEADERS.append(f'メディア-{item}-投稿日時')
    HEADERS.append(f'メディア-{item}-いいね数')
    HEADERS.append(f'メディア-{item}-コメント数')
    HEADERS.append(f'メディア-{item}-キャプション内容')

EXCEL_FILE = "demo_output_1.xlsx"

def create_excel_with_headers():
    """Creates an Excel file with only the predefined headers if it doesn't exist."""
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=HEADERS)  # Create empty DataFrame with fixed headers
        df.to_excel(EXCEL_FILE, index=False, engine="xlsxwriter")
        print(f"Excel file '{EXCEL_FILE}' created with headers: {HEADERS}")

def append_json_to_excel(json_data):
    """Appends JSON data to an Excel file, ensuring it matches predefined headers."""
    df_new = pd.DataFrame([json_data])  # Convert JSON to DataFrame

    # Ensure all missing columns are filled with NaN
    for col in HEADERS:
        if col not in df_new.columns:
            df_new[col] = None  # Fill missing columns with None

    # Reorder columns to match original headers
    df_new = df_new[HEADERS]

    # Read existing file
    df_existing = pd.read_excel(EXCEL_FILE, engine="openpyxl")

    # Append new data and save back to Excel
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined.to_excel(EXCEL_FILE, index=False, engine="xlsxwriter")

    print(f"Appended data: {json_data}")

def convert_to_japanese_time(unix_timestamp):
    japan_tz = pytz.timezone('Asia/Tokyo')
    utc_time = datetime.datetime.fromtimestamp(unix_timestamp, tz=pytz.utc)
    japan_time = utc_time.astimezone(japan_tz)
    japan_time_str = japan_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    return japan_time_str

# Step 1: Create Excel file with headers
create_excel_with_headers()

# Load usernames from CSV
file_path = 'demo_data.csv'
# file_path = 'demo_data.csv'
data = pd.read_csv(file_path)
usernames = data['username']

# Iterate through usernames
for username in usernames:
    # try:
        # Navigate to the target webpage
        driver.get(SITE_URL)

        time.sleep(10)

        # Input the username
        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".form-content .input-element"))
        )
        input_field.send_keys(username)

        # Click the "View Profile" button
        view_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".form-content button"))
        )
        view_button.click()

        # Wait for API call to complete
        time.sleep(10)  # Adjust based on observation

        # Retrieve performance logs
        logs = driver.get_log("performance")

        for log_entry in logs:
            message = json.loads(log_entry["message"])
            method = message["message"]["method"]

            # Filter for network responses
            if method == "Network.responseReceived":
                response = message["message"]["params"]["response"]
                if "downloader/api/viewer/profile" in response["url"]:
                    # Get the requestId to fetch the response body
                    request_id = message["message"]["params"]["requestId"]
                    
                    # Fetch the response body using Chrome DevTools Protocol
                    response_body = driver.execute_cdp_cmd(
                        "Network.getResponseBody", {"requestId": request_id}
                    )
                    result = json.loads(response_body["body"])
                    if 'data' in result:
                        profile = result['data']['profile']
                        profile_data = {
                            'ユーザー名': profile['username'],
                            '経歴': profile['biography'],
                            'フォロワー数': profile['edge_followed_by']['count'],
                            'フォロー数': profile['edge_follow']['count'],
                            'メディア数': profile['edge_owner_to_timeline_media']['count'],
                        }
                        current_number = 0
                        for edge in profile['edge_owner_to_timeline_media']['edges']:
                            if current_number == 10: break
                            subData = edge['node']
                            newdata = {
                                f'{"メディア"}-{current_number}-投稿ID': subData['post_id'],
                                f'{"メディア"}-{current_number}-投稿日時': convert_to_japanese_time(subData['created_at']),
                                f'{"メディア"}-{current_number}-いいね数': subData['like_count'],
                                f'{"メディア"}-{current_number}-コメント数': subData['comment_count']
                            }
                            if 'description' in subData:
                                newdata = {**newdata, **{f'{"メディア"}-{current_number}-キャプション内容': subData['description']}}
                            profile_data = {**profile_data, **newdata}
                            current_number = current_number + 1
                        print(profile_data)
                        append_json_to_excel(profile_data)
                        print(f"Data for {username} appended to excel.")
                    else:
                        print(f"Data for {username} didn't appended to excel")

    # except Exception as e:
    #     print(f"Request failed for {username}: {e}")
    #     continue

# Close the WebDriver
driver.quit()