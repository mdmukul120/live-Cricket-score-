import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Cricbuzz Live Scores URL
URL = "https://www.cricbuzz.com/live-cricket-scores"

# Cloudflare / Bot protection এড়াতে User-Agent
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def scrape_scores():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return {"status": "error", "message": f"HTTP Error {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        matches = []
        # Cricbuzz এর লিকুইড কার্ড বা ম্যাচের কন্টেইনারগুলো খুঁজে বের করা
        match_cards = soup.find_all('div', class_='cb-mtch-lst')

        for card in match_cards:
            try:
                # ম্যাচের শিরোনাম ও হেডার
                header = card.find('h2') or card.find('h3')
                title = header.text.strip() if header else "Cricket Match"

                # বর্তমান স্কোরের বিবরণ
                scores = card.find_all('div', class_='cb-scr-wgt-lh')
                score_text = " ".join([s.text.strip() for s in scores]) if scores else "Score not available"

                # ম্যাচের স্ট্যাটাস (যেমন: Live, Completed, Toss)
                status = card.find('div', class_='cb-text-complete') or card.find('div', class_='cb-text-live')
                status_text = status.text.strip() if status else "In Progress"

                matches.append({
                    "title": title,
                    "score": score_text,
                    "status": status_text
                })
            except Exception:
                continue

        return {
            "status": "success",
            "last_updated": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            "total_matches": len(matches),
            "matches": matches
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    data = scrape_scores()
    
    # JSON ফাইলে রাইট করা
    with open('score.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("Scraping completed and saved to score.json")
