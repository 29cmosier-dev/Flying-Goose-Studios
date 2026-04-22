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
        scrape_users(session)

def scrape_stats(session):
    dash_response = session.get(DASHBOARD_URL)
    dash_soup = BeautifulSoup(dash_response.text, 'html.parser')
    
    # This helper finds the number based on the heading text
    def get_val(label):
        header = dash_soup.find('h6', string=label)
        if header:
            # The number is in the div with class 'display-6' right after the <h6>
            return header.find_next(class_='display-6').get_text(strip=True)
        return "0"

    # Now it doesn't matter what order they are in!
    data = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Total Users": get_val("Users"),
        "Msgs Today": get_val("Chat Messages Today"),
        "Active Now": get_val("Active Now"),
        "Visitors Today": get_val("Visitors Today")
    }
    
    df = pd.DataFrame([data])
    print(df.to_string(index=False))
    return df


def scrape_users(session):
    response = session.get(USERS_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all user cards
    user_cards = soup.find_all(class_='admin-user-card')
    
    user_list = []
    
    for card in user_cards:
        # Extract data using the new specific classes
        name = card.find(class_='fw-semibold').get_text(strip=True)
        handle = card.find(class_='text-muted').get_text(strip=True)
        
        # 'admin-user-card-copy' is used for both Email and School/Grade
        details = card.find_all(class_='admin-user-card-copy')
        email = details[0].get_text(strip=True) if len(details) > 0 else "N/A"
        school_info = details[1].get_text(strip=True) if len(details) > 1 else "N/A"
        
        # Extract meta values (Birthday, Age, Last Login, etc.)
        meta_values = [v.get_text(strip=True) for v in card.find_all(class_='admin-user-mini-value')]
        
        user_list.append({
            "Name": name,
            "Handle": handle,
            "Email": email,
            "School": school_info,
            "Last Login": meta_values[2] if len(meta_values) > 2 else "N/A"
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(user_list)
    print(df.head())
    return df


if __name__ == "__main__":
    run_all()