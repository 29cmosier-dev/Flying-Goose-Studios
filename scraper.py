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
    
    # Check if Secret is actually loaded
    if not PASSWORD:
        print("CRITICAL ERROR: STUDIO_PASS environment variable is empty!")
        return

    with requests.Session() as session:
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': LOGIN_URL  # Add this line
        })

        
        # 1. Login Process
        print(f"Fetching login page: {LOGIN_URL}")
        response = session.get(LOGIN_URL)
        login_soup = BeautifulSoup(response.text, 'html.parser')

        # Find the login form - this ensures we get all hidden security fields
        login_form = login_soup.find('form')
        if not login_form:
            print("CRITICAL ERROR: Login form not found.")
            return

        # Extract all hidden inputs automatically
        login_data = {tag.get('name'): tag.get('value') for tag in login_form.find_all('input', type='hidden')}
        
        # Manually add the credentials
        login_data['email'] = USERNAME
        login_data['password'] = PASSWORD

        print(f"Submitting payload with keys: {list(login_data.keys())}")

        # Crucial: The site likely checks if you're coming from the login page
        session.headers.update({'Referer': LOGIN_URL})

        login_post = session.post(LOGIN_URL, data=login_data)
        print(f"Post-Login URL: {login_post.url}")

        response = session.get(LOGIN_URL)
        login_soup = BeautifulSoup(response.text, 'html.parser')
        csrf_tag = login_soup.find('input', {'name': 'csrf'})
        csrf_token = csrf_tag.get('value')


        # 2. Setup the headers and data
        # Explicitly set the Referer to let the site know where the request came from
        session.headers.update({'Referer': LOGIN_URL})

        login_data = {
            'csrf': csrf_token,
            'email': USERNAME, 
            'password': PASSWORD
        }

        # 3. Perform the login
        login_post = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        print(f"Final URL after login attempt: {login_post.url}")


        
        print(f"Post-Login URL: {login_post.url}")

        # 3. Suspension Check
        if "route=school_suspended" in login_post.url:
            print("NOTICE: School is currently suspended. Ending session early.")
            return

        # 4. Verify Login Success
        if "login" in login_post.url:
            print("LOGIN FAILED: Still on login page. Check username/password.")
            print("--- Login Response Snippet ---")
            print(login_post.text[:2000]) # This will print the HTML of the failure page
            return
            
        print("Login Successful. Starting data collection...")

        # 5. Scrape
        scrape_stats(session)
        scrape_users(session)

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
            name = card.find(class_='fw-semibold').get_text(strip=True)
            details = card.find_all(class_='admin-user-card-copy')
            email = details[0].get_text(strip=True) if len(details) > 0 else "N/A"
            school = details[1].get_text(strip=True) if len(details) > 1 else "N/A"
            
            meta = [v.get_text(strip=True) for v in card.find_all(class_='admin-user-mini-value')]
            
            user_list.append({
                "Name": name,
                "Email": email,
                "School": school,
                "Last Login": meta[2] if len(meta) > 2 else "N/A"
            })
        except Exception as e:
            print(f"Error parsing a card: {e}")

    df = pd.DataFrame(user_list)
    if not df.empty:
        print(df.head())
    else:
        print("User DataFrame is empty.")
    return df

if __name__ == "__main__":
    run_all()
