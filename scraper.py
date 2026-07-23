import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

URL = "https://m.cricbuzz.com/cricket-match/live-scores"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# টিমের কান্ট্রি কোড অনুযায়ী ফ্লাগ ইমেজের ডাইনামিক URL
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
    "WI": "jm", "WEST INDIES": "jm"
}

def get_flag(team_name):
    """টিমের নাম থেকে কান্ট্রি ফ্লাগ ইউআরএল বের করার ফাংশন"""
    name_clean = team_name.upper().strip()
    for key, code in COUNTRY_CODES.items():
        if key in name_clean:
            return f"{FLAG_CDN}/{code}.png"
    return "https://via.placeholder.com/80?text=FLAG"

def scrape_scores():
    matches = []
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return {"status": "error", "message": f"HTTP Status {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cricbuzz Mobile HTML Elements Parsing
        match_blocks = soup.select('.cb-mtch-lst') or soup.select('.ui-section') or soup.select('div[class*="cb-col-100"]')

        for block in match_blocks:
            try:
                # ১. টাইটেল এক্সট্র্যাক্ট করা
                header = block.find('h3') or block.find('h2') or block.find('h4')
                title = header.text.strip() if header else "Cricket Match"

                # ২. স্কোর এক্সট্র্যাক্ট করা (Cricbuzz Score Elements)
                score_nodes = block.select('.cb-scr-wgt-lh') or block.select('div[class*="cb-hm-scg"]') or block.find_all('div', class_='cb-ovr-flo')
                
                extracted_scores = []
                for s in score_nodes:
                    txt = s.get_text(separator=' ', strip=True)
                    if txt and len(txt) > 2:
                        extracted_scores.append(txt)

                full_score = " | ".join(extracted_scores) if extracted_scores else "Score Updating..."

                # ৩. টিমের নাম এবং ফ্লাগ আইকন এক্সট্র্যাক্ট করা
                teams = title.split('vs') if 'vs' in title else title.split('v/s')
                team1_name = teams[0].strip() if len(teams) > 0 else "Team 1"
                team2_name = teams[1].strip() if len(teams) > 1 else "Team 2"

                # ৪. স্ট্যাটাস / রেজাল্ট
                status_elem = block.find('div', class_='cb-text-complete') or block.find('div', class_='cb-text-live') or block.find('div', class_='cb-text-preview')
                status = status_elem.text.strip() if status_elem else "In Progress"

                matches.append({
                    "title": title,
                    "team1": {
                        "name": team1_name,
                        "flag": get_flag(team1_name)
                    },
                    "team2": {
                        "name": team2_name,
                        "flag": get_flag(team2_name)
                    },
                    "score": full_score,
                    "status": status
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
    
    with open('score.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Scraping completed. Total matches found: {data.get('total_matches', 0)}")
