import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

USERNAME = "ziggy"
PASSWORD = os.getenv('STUDIO_PASS')
LOGIN_URL = "https://hub.flyinggoosestudios.com/?route=login"
DASHBOARD_URL = "https://hub.flyinggoosestudios.com/?route=admin.dashboard"
USERS_URL = "https://hub.flyinggoosestudios.com/?route=admin.users"

def run_all():
    print("--- Starting Session ---")
    if not PASSWORD:
        print("CRITICAL ERROR: STUDIO_PASS environment variable is empty!")
        return

    with requests.Session() as session:
        # 1. Setup Browser Headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': LOGIN_URL
        })

        # 2. Fetch login page & grab ALL hidden inputs (CSRF, etc.)
        print(f"Fetching login page: {LOGIN_URL}")
        response = session.get(LOGIN_URL)
        login_soup = BeautifulSoup(response.text, 'html.parser')
        
        login_form = login_soup.find('form')
        if not login_form:
            print("CRITICAL ERROR: Login form not found.")
            return

        # Dynamically build the payload from the form's hidden fields
        login_data = {tag.get('name'): tag.get('value') for tag in login_form.find_all('input', type='hidden')}
        login_data['email'] = USERNAME
        login_data['password'] = PASSWORD

        # 3. Perform the Login
        print("Attempting login...")
        login_post = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        
        # 4. THE FIX: Force navigate to the Dashboard to "activate" the session
        print("Kicking session to Admin Dashboard...")
        dash_response = session.get(DASHBOARD_URL)
        
        # 5. Verify Success by checking the content of the dashboard
        if "Dashboard" not in dash_response.text and "Ziggy" not in dash_response.text:
            print(f"LOGIN FAILED: Still can't see admin data. URL: {dash_response.url}")
            return

        print("Login Successful! Starting data collection...")
        
        # 6. Pass the "kicked" session into your scrapers
        df_stats = scrape_stats(session)
        df_users = scrape_users(session)

        # SAVE THE FILES TO DISK (This is what was missing)
        if df_stats is not None and not df_stats.empty:
            df_stats.to_csv("stats.csv", index=False)
            print("Saved stats.csv")
            
        if df_users is not None and not df_users.empty:
            df_users.to_csv("user_breakdown.csv", index=False)
            print("Saved user_breakdown.csv")


def scrape_stats(session):
    print(f"\n--- Scraping Dashboard: {DASHBOARD_URL} ---")
    dash_response = session.get(DASHBOARD_URL)
    dash_soup = BeautifulSoup(dash_response.text, 'html.parser')
    
    print(f"Current URL: {dash_response.url}")
    print(f"Page Title: {dash_soup.title.string if dash_soup.title else 'No Title'}")

    def get_val(label_text):
        # Improved regex to be very loose with spacing
        header = dash_soup.find('h6', string=re.compile(rf'.*{label_text}.*', re.I))
        if header:
            val_tag = header.find_next(class_='display-6')
            return val_tag.get_text(strip=True) if val_tag else "0"
        return "N/A"

    data = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Total Users": get_val("Users"),
        "Msgs Today": get_val("Chat Messages Today"),
        "Active Now": get_val("Active Now"),
        "Visitors Today": get_val("Visitors Today")
    }
    
    df = pd.DataFrame([data])
    print("\nCaptured Stats:")
    print(df.to_string(index=False))
    return df

def scrape_users(session):
    print(f"\n--- Scraping Users: {USERS_URL} ---")
    response = session.get(USERS_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    user_cards = soup.find_all(class_='admin-user-card')
    print(f"Found {len(user_cards)} user cards.")
    
    user_list = []
    for card in user_cards:
        try:
            # 1. Role - Get the text of the FIRST badge
            role_tag = card.find('span', class_='badge')
            role = role_tag.get_text(strip=True) if role_tag else "N/A"

            # 2. School and Grade
            school, grade = "N/A", "N/A"
            
            # Find the specific div that contains the "•"
            location_div = card.find(lambda tag: tag.name == "div" and "•" in tag.text)
            
            if location_div:
                raw_text = location_div.get_text(strip=True)
                parts = raw_text.split("•")
                school = parts[0].strip()
                # Ensure we don't accidentally grab "Teacher" as a grade
                if len(parts) > 1:
                    potential_grade = parts[1].strip()
                    grade = potential_grade if "Grade" in potential_grade else "Staff/Other"
            
            user_list.append({
                "Role": role,
                "School": school,
                "Grade": grade
            })
        except Exception as e:
            print(f"Error parsing a card: {e}")

    df = pd.DataFrame(user_list)
    return df


if __name__ == "__main__":
    run_all()
