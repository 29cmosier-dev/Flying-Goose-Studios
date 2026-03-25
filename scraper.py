import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

USERNAME = "ziggy"
PASSWORD = "ZIGGYADMIN"

def scrape():
    # URL from your HTML sample
    LOGIN_URL = "https://hub.flyinggoosestudios.com/?route=login"
    DASHBOARD_URL = "https://hub.flyinggoosestudios.com/?route=admin.dashboard"
    
    with requests.Session() as session:
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # 1. Login Logic
        login_page = session.get(LOGIN_URL)
        login_soup = BeautifulSoup(login_page.text, 'html.parser')
        csrf_token = login_soup.find('input', {'name': 'csrf'}).get('value')

        payload = {'csrf': csrf_token, 'email': USERNAME, 'password': PASSWORD}
        session.post(LOGIN_URL, data=payload)
        
        # 2. Scrape Dashboard
        response = session.get(DASHBOARD_URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        stats = soup.find_all(class_="display-6")
        
        if len(stats) >= 15:
            # Capturing "Active Now" (verify the index is correct based on your layout)
            active_now = stats[13].get_text(strip=True) 
            
            now = datetime.now()
            # File name updates monthly: stats_2026_03.csv
            filename = f"stats_{now.strftime('%Y_%m')}.csv"
            
            new_row = pd.DataFrame([[now.strftime("%Y-%m-%d %H:%M"), active_now]], 
                                   columns=['Timestamp', 'Active Now'])
            
            # Append to the monthly file
            file_exists = os.path.isfile(filename)
            new_row.to_csv(filename, mode='a', index=False, header=not file_exists)
            print(f"Logged {active_now} to {filename}")
        else:
            print(f"Error: Found {len(stats)} elements.")

if __name__ == "__main__":
    scrape()