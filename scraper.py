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
        login_page = session.get(LOGIN_URL)
        login_soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_token = login_soup.find('input', {'name': 'csrf'}).get('value')

        payload = {'csrf': csrf_token, 'email': USERNAME, 'password': PASSWORD}
        session.post(LOGIN_URL, data=payload)
        
        # 2. Scrape Dashboard
        response = session.get(DASHBOARD_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        stats = soup.find_all(class_="display-6")
        
        if len(stats) >= 14:
            # Grab both stats
            messages_today = stats[8].get_text(strip=True)
            active_now     = stats[13].get_text(strip=True) 
            
            now = datetime.now()
            filename = f"stats_{now.strftime('%Y_%m')}.csv"
            
            # Create a row with both values
            new_row = pd.DataFrame([[
                now.strftime("%Y-%m-%d %H:%M"), 
                messages_today, 
                active_now
            ]], columns=['Timestamp', 'Messages Today', 'Active Now'])
            
            # Append to file
            file_exists = os.path.isfile(filename)
            new_row.to_csv(filename, mode='a', index=False, header=not file_exists)
            print(f"Logged: Messages({messages_today}), Active({active_now}) to {filename}")
        else:
            print(f"Error: Found only {len(stats)} elements.")

if __name__ == "__main__":
    scrape()
