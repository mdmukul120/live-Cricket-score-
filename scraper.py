import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import re

URL = "https://m.cricbuzz.com/cricket-match/live-scores"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

FLAG_CDN = "https://flagcdn.com/w80"
COUNTRY_CODES = {
    "BAN": "bd", "BANGLADESH": "bd",
    "IND": "in", "INDIA": "in",
    "PAK": "pk", "PAKISTAN": "pk",
    "AUS": "au", "AUSTRALIA": "au",
    "ENG": "gb", "ENGLAND": "gb",
    "SA": "za", "SOUTH AFRICA": "za",
    "NZ": "nz", "NEW ZEALAND": "nz",
    "SL": "lk", "SRI LANKA": "lk",
    "AFG": "af", "AFGHANISTAN": "af",
    "WI": "jm", "WEST INDIES": "jm",
    "ZIM": "zw", "ZIMBABWE": "zw",
    "IRE": "ie", "IRELAND": "ie"
}

def get_flag(team_text):
    """টিমের নাম থেকে কান্ট্রি ফ্লাগ খুঁজে বের করার ফাংশন"""
    text_upper = team_text.upper()
    for key, code in COUNTRY_CODES.items():
        if key in text_upper:
            return f"{FLAG_CDN}/{code}.png"
    return "https://via.placeholder.com/80?text=FLAG"

def parse_teams_and_flags(title_text):
    """টাইটেল বা টেক্সট থেকে টিম ও তাদের ফ্লাগ আলাদা করা"""
    teams = re.split(r'vs|v/s|-', title_text, flags=re.IGNORECASE)
    t1 = teams[0].strip() if len(teams) > 0 else "Team 1"
    t2 = teams[1].strip() if len(teams) > 1 else "Team 2"
    
    return {
        "team1": {"name": t1, "flag": get_flag(t1)},
        "team2": {"name": t2, "flag": get_flag(t2)}
    }

def scrape_scores():
    matches = []
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return {"status": "error", "message": f"HTTP Status {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cricbuzz Mobile HTML Elements Parsing (Multiple fallbacks)
        match_blocks = soup.find_all('div', class_=re.compile(r'cb-mtch-lst|ui-section|cb-col-100'))

        for block in match_blocks:
            try:
                header = block.find(['h3', 'h2', 'h4'])
                title = header.text.strip() if header else ""
                
                if not title:
                    continue

                # স্কোর এক্সট্র্যাক্ট করার চেষ্টা
                score_elements = block.find_all('div', class_=re.compile(r'cb-scr-wgt|cb-ovr-flo|cb-text-vms'))
                score_text = " ".join([s.text.strip() for s in score_elements if s.text.strip()])
                
                if not score_text:
                    score_text = block.get_text(separator=' ', strip=True)

                # স্ট্যাটাস
                status_elem = block.find('div', class_=re.compile(r'cb-text-complete|cb-text-live|cb-text-preview'))
                status = status_elem.text.strip() if status_elem else "In Progress"

                teams_data = parse_teams_and_flags(title)

                matches.append({
                    "title": title,
                    "team1": teams_data["team1"],
                    "team2": teams_data["team2"],
                    "score": score_text if score_text else "Score Updating...",
                    "status": status
                })
            except Exception:
                continue

        # যদি কন্টেইনার দিয়ে কোনো ব্লক না পায় (যেমন আপনার ক্ষেত্রে হয়েছিল)
        if not matches:
            all_links = soup.find_all('a')
            for link in all_links:
                href = link.get('href', '')
                if '/live-cricket-scores/' in href or '/cricket-scores/' in href:
                    text = link.get_text(separator=' ', strip=True)
                    if text and len(text) > 5 and ("vs" in text.lower() or "won" in text.lower() or "preview" in text.lower()):
                        
                        teams_data = parse_teams_and_flags(text)
                        
                        matches.append({
                            "title": text,
                            "team1": teams_data["team1"],
                            "team2": teams_data["team2"],
                            "score": text, # লিঙ্ক থেকে পাওয়া সম্পূর্ণ স্কোর সামারি
                            "status": "Match Details"
                        })

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
    
    with open('score.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Scraping completed. Total matches found: {data.get('total_matches', import
