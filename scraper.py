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
        
        # 1. Login Logic
        login_page = session.get(LOGIN_URL)
        login_soup = BeautifulSoup(login_page.text, 'html.parser')
        
        csrf_tag = login_soup.find('input', {'name': 'csrf'})
        if not csrf_tag:
            print("Error: CSRF token not found.")
            return
            
        csrf_token = csrf_tag.get('value')

        payload = {'csrf': csrf_token, 'email': USERNAME, 'password': PASSWORD}
        session.post(LOGIN_URL, data=payload)
        
        # 2. Scrape Dashboard
        response = session.get(DASHBOARD_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        stats = soup.find_all(class_="display-6")
        
        # Ensure we have enough elements to reach index 13
        if len(stats) >= 14:
            messages_today = stats[8].get_text(strip=True)
            active_now = stats[13].get_text(strip=True) 
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # 3. Save to the single 'stats.csv' file
            new_row = pd.DataFrame([[timestamp, messages_today, active_now]], 
                                   columns=['Timestamp', 'Messages Today', 'Active Now'])
            
            file_exists = os.path.isfile('stats.csv')
            # mode='a' appends to the file; header=not file_exists only adds the header once
            new_row.to_csv('stats.csv', mode='a', index=False, header=not file_exists)
            
            print(f"Success! Logged at {timestamp} -> Messages: {messages_today}, Active: {active_now}")
        else:
            print(f"Error: Found only {len(stats)} elements. Check if dashboard changed.")

if __name__ == "__main__":
    scrape()