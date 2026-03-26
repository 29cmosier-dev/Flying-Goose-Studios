import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime


USERNAME = "ziggy"
PASSWORD = os.getenv('STUDIO_PASS')
LOGIN_URL = "https://hub.flyinggoosestudios.com/?route=login"
DASHBOARD_URL = "https://hub.flyinggoosestudios.com/?route=admin.dashboard"
USERS_URL = "https://hub.flyinggoosestudios.com/?route=admin.users"

def scrape():
    print("--- Starting Scrape ---")
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # 1. Login Debugging
        print(f"Attempting login to: {LOGIN_URL}")
        response = session.get(LOGIN_URL)
        print(f"Login Page Load: {response.status_code}") # Should be 200
        
        login_soup = BeautifulSoup(response.text, 'html.parser')
        csrf_tag = login_soup.find('input', {'name': 'csrf'})
        
        if not csrf_tag:
            print("CRITICAL ERROR: CSRF token not found. The login page structure might have changed.")
            return
            
        csrf_token = csrf_tag.get('value')
        print(f"CSRF Token acquired: {csrf_token[:5]}...") # Log start of token for safety
        
        login_data = {'csrf': csrf_token, 'email': USERNAME, 'password': PASSWORD}
        login_post = session.post(LOGIN_URL, data=login_data)
        print(f"Login Post Status: {login_post.status_code}")
        
        # 2. Dashboard Debugging
        print(f"Fetching Dashboard: {DASHBOARD_URL}")
        dash_response = session.get(DASHBOARD_URL)
        dash_soup = BeautifulSoup(dash_response.text, 'html.parser')
        
        # Find all stats and log how many were found
        stats = dash_soup.find_all(class_='display-6')
        print(f"DEBUG: Found {len(stats)} elements with class 'display-6'")
        
        if len(stats) >= 14:
            msg_today = stats[8].get_text(strip=True)
            active_now = stats[13].get_text(strip=True)
            total_users = stats[0].get_text(strip=True)
            print(f"SUCCESS: Data captured -> Messages: {msg_today}, Active: {active_now}, Total Users: {total_users}")
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            new_data = pd.DataFrame([[timestamp, msg_today, active_now, total_users]], 
                                    columns=['Timestamp', 'Messages Today', 'Active Now', 'Total Users'])
            
            # 3. File System Debugging
            file_path = 'stats.csv'
            file_exists = os.path.isfile(file_path)
            print(f"File '{file_path}' exists in runner: {file_exists}")
            
            new_data.to_csv(file_path, mode='a', index=False, header=not file_exists)
            print(f"File '{file_path}' updated successfully.")
        else:
            print("ERROR: Not enough 'display-6' elements found. Did the dashboard layout change?")
            # Optional: Print the first 500 characters of the page to see what we actually got
            print(dash_response.text[:500]) 


def scrape_schools():
    
    with requests.Session() as session:
        # 1. Login (same as your current code)
        login_soup = BeautifulSoup(session.get(LOGIN_URL).text, 'html.parser')
        csrf_token = login_soup.find('input', {'name': 'csrf'}).get('value')
        session.post(LOGIN_URL, data={'csrf': csrf_token, 'email': USERNAME, 'password': PASSWORD})

        # 2. Scrape Users
        soup = BeautifulSoup(session.get(USERS_URL).text, 'html.parser')
        cards = soup.find_all(class_="card-glass")
        
        user_list = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        for card in cards:
            # A. Get Role (Student, Staff, etc.)
            role_badge = card.find(class_="badge")
            role = role_badge.get_text(strip=True) if role_badge else "User"

            # B. Get School and Grade
            school = "Other/Staff"
            grade = "N/A"
            
            details = card.find_all(class_="small text-muted")
            for d in details:
                text = d.get_text(strip=True)
                if "•" in text:
                    parts = text.split("•")
                    school = parts[0].strip()
                    grade = parts[1].strip()
                    break
            
            user_list.append([timestamp, role, school, grade])

        # 3. Save to a NEW file: user_breakdown.csv
        df = pd.DataFrame(user_list, columns=['Timestamp', 'Role', 'School', 'Grade'])
        
        # This will create a row for EVERY user (81 rows total each hour)
        file_name = 'user_breakdown.csv'
        file_exists = os.path.isfile(file_name)
        # Always write the header since we are overwriting the file every hour
        df.to_csv(file_name, mode='w', index=False, header=True)

        
        print(f"Success! Tracked breakdown for {len(user_list)} users.")


if __name__ == "__main__":
    scrape() 
    scrape_schools()
