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

def run_all():
    print("--- Starting Session ---")
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # 1. Login Process
        response = session.get(LOGIN_URL)
        login_soup = BeautifulSoup(response.text, 'html.parser')
        csrf_tag = login_soup.find('input', {'name': 'csrf'})
        
        if not csrf_tag:
            print("CRITICAL ERROR: CSRF token not found.")
            return
            
        csrf_token = csrf_tag.get('value')
        login_data = {'csrf': csrf_token, 'email': USERNAME, 'password': PASSWORD}
        login_post = session.post(LOGIN_URL, data=login_data)
        
        # 2. Suspension Check (The "Kill Switch")
        if "route=school_suspended" in login_post.url:
            print("NOTICE: School is currently suspended. Ending session early.")
            return # Stops EVERYTHING here
        
        print("Login Successful. Starting data collection...")

        # 3. Task 1: Scrape Dashboard Stats
        scrape_stats(session)
        
        # 4. Task 2: Scrape School Breakdown
        scrape_schools(session)

def scrape_stats(session):
    dash_response = session.get(DASHBOARD_URL)
    dash_soup = BeautifulSoup(dash_response.text, 'html.parser')
    stats = dash_soup.find_all(class_='display-6')
    
    if len(stats) >= 14:
        msg_today = stats[8].get_text(strip=True)
        active_now = stats[13].get_text(strip=True)
        total_users = stats[0].get_text(strip=True)
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_data = pd.DataFrame([[timestamp, msg_today, active_now, total_users]], 
                                columns=['Timestamp', 'Messages Today', 'Active Now', 'Total Users'])
        
        file_path = 'stats.csv'
        file_exists = os.path.isfile(file_path)
        new_data.to_csv(file_path, mode='a', index=False, header=not file_exists)
        print(f"SUCCESS: Dashboard stats updated ({total_users} users).")
    else:
        print("ERROR: Dashboard layout changed or data missing.")

def scrape_schools(session):
    soup = BeautifulSoup(session.get(USERS_URL).text, 'html.parser')
    cards = soup.find_all(class_="card-glass")
    
    user_list = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    for card in cards:
        role_badge = card.find(class_="badge")
        role = role_badge.get_text(strip=True) if role_badge else "User"

        school, grade = "Other/Staff", "N/A"
        details = card.find_all(class_="small text-muted")
        for d in details:
            text = d.get_text(strip=True)
            if "•" in text:
                parts = text.split("•")
                school, grade = parts[0].strip(), parts[1].strip()
                break
        
        user_list.append([timestamp, role, school, grade])

    df = pd.DataFrame(user_list, columns=['Timestamp', 'Role', 'School', 'Grade'])
    df.to_csv('user_breakdown.csv', mode='w', index=False, header=True)
    print(f"SUCCESS: School breakdown updated ({len(user_list)} entries).")

if __name__ == "__main__":
    run_all()