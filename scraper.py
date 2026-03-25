import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

USERNAME = "ziggy"
PASSWORD = "ZIGGYADMIN"

def scrape():
    LOGIN_URL = "https://hub.flyinggoosestudios.com/?route=login"
    DASHBOARD_URL = "https://hub.flyinggoosestudios.com/?route=admin.dashboard"
    
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
    LOGIN_URL = "https://hub.flyinggoosestudios.com/?route=login"
    USERS_URL = "https://hub.flyinggoosestudios.com/?route=admin.users"
    
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # 1. Login
        login_soup = BeautifulSoup(session.get(LOGIN_URL).text, 'html.parser')
        csrf_token = login_soup.find('input', {'name': 'csrf'}).get('value')
        session.post(LOGIN_URL, data={'csrf': csrf_token, 'email': USERNAME, 'password': PASSWORD})

        # 2. Get Users
        soup = BeautifulSoup(session.get(USERS_URL).text, 'html.parser')
        cards = soup.find_all(class_="card-glass")
        school_counts = {}

        for card in cards:
            # We look for the div that actually contains the " • " symbol
            details = card.find_all(class_="small text-muted")
            for d in details:
                text = d.get_text(strip=True)
                if "•" in text:
                    school_name = text.split('•')[0].strip()
                    school_counts[school_name] = school_counts.get(school_name, 0) + 1
                    break # Stop looking at this card once we find the school

        # 3. Save
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        if school_counts:
            data = [[timestamp, school, count] for school, count in school_counts.items()]
            df = pd.DataFrame(data, columns=['Timestamp', 'School', 'Count'])
            
            file_exists = os.path.isfile('schools.csv')
            df.to_csv('schools.csv', mode='a', index=False, header=not file_exists)
            print(f"Successfully tracked {len(school_counts)} schools.")

if __name__ == "__main__":
    scrape() 
    scrape_schools()
