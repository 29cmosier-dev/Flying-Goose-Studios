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
    
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # 1. Login
        login_soup = BeautifulSoup(session.get(LOGIN_URL).text, 'html.parser')
        csrf_tag = login_soup.find('input', {'name': 'csrf'})
        if not csrf_tag: return
        csrf_token = csrf_tag.get('value')

        session.post(LOGIN_URL, data={'csrf': csrf_token, 'email': USERNAME, 'password': PASSWORD})
        
        # 2. Scrape Dashboard
        stats = BeautifulSoup(session.get(DASHBOARD_URL).text, 'html.parser').find_all(class_="display-6")
        
        if len(stats) >= 14:
            msg_today = stats[8].get_text(strip=True)
            active_now = stats[13].get_text(strip=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            new_data = pd.DataFrame([[timestamp, msg_today, active_now]], 
                                   columns=['Timestamp', 'Messages Today', 'Active Now'])
            
            file_exists = os.path.isfile('stats.csv')
            new_data.to_csv('stats.csv', mode='a', index=False, header=not file_exists)
            print(f"Logged Dashboard: {msg_today} | {active_now}")

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
