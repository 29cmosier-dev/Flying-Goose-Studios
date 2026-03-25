import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os



def scrape():
    # 1. The PHP Dashboard URL
    URL = "https://hub.flyinggoosestudios.com/?route=admin.dashboard"
    
    # Make the request (using a header so it looks like a real browser)
    YOUR_COOKIE = "_ga=GA1.1.1983017726.1773850079; _ga_W5JW8H48BX=GS2.1.s1773850079$o1$g1$t1773850133$j6$l0$h0; _ga_00KXXS3RBH=GS2.1.s1773853947$o1$g1$t1773854055$j57$l0$h0; _ga_9WFJGF6YNK=GS2.1.s1773876243$o1$g0$t1773876262$j41$l0$h0; _ga=GA1.3.1983017726.1773850079; _ga_7FN7LEVWXD=GS2.1.s1773930711$o1$g0$t1773930721$j50$l0$h0; PHPSESSID=tdqptv0302s0aqd6qs9456k574"
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Cookie': YOUR_COOKIE
    }
    response = requests.get(URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 2. Find the 297 (it's the 7th 'display-6' element based on your screenshot)
    stats = soup.find_all(class_="display-6")
    if len(stats) > 9:
        # Change this line to specifically grab the text from the 7th item
        messages_today = stats[9].get_text(strip=True)
        print(f"Captured: {messages_today}")
    else:
        print(f"Error: Found only {len(stats)} stats. Check if Cookie expired.")
        return # Stop the script so it doesn't break the CSV

    # 3. Save to CSV
    new_data = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), messages_today]], 
                            columns=['Timestamp', 'Messages'])
    
    if os.path.exists('stats.csv'):
        df = pd.read_csv('stats.csv')
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data
        
    df.to_csv('stats.csv', index=False)

if __name__ == "__main__":
    scrape()
