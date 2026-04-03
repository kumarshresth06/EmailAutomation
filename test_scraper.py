import requests
from bs4 import BeautifulSoup
import re

def google_search_email(query, domain):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # Look for ANY email associated with the domain
        pattern = r'[a-zA-Z0-9._%+-]+@' + re.escape(domain)
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        if matches:
            # Return most frequent match
            from collections import Counter
            return Counter(matches).most_common(1)[0][0]
        return None
    except Exception as e:
        print("Scrape failed:", e)
        return None

if __name__ == "__main__":
    print(google_search_email('Tim Cook Apple email', 'apple.com'))
