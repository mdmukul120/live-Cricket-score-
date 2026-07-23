import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

# Cricbuzz Live Scores Mobile Page URL (এটি পার্স করা সহজ ও ব্লকিং কম হয়)
URL = "https://m.cricbuzz.com/cricket-match/live-scores"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def scrape_scores():
    matches = []
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return {"status": "error", "message": f"HTTP Status {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cricbuzz Mobile HTML Elements Parsing
        containers = soup.find_all('div', class_='ui-section') or soup.find_all('div', class_='cb-col-100')
        
        # Desktop & Mobile Fallback tags
        match_blocks = soup.select('.cb-mtch-lst') or soup.select('a[href*="/cricket-scores/"]') or soup.select('.cb-col-100.cb-col')

        for block in match_blocks:
            try:
                text_content = block.get_text(separator=' ', strip=True)
                if not text_content or len(text_content) < 10:
                    continue

                # Title extraction
                header = block.find('h3') or block.find('h2') or block.find('h4')
                title = header.text.strip() if header else "Cricket Match"

                # Status / Result
                status_elem = block.find('div', class_='cb-text-complete') or block.find('div', class_='cb-text-live') or block.find('div', class_='cb-text-preview')
                status = status_elem.text.strip() if status_elem else "In Progress"

                matches.append({
                    "title": title,
                    "details": text_content[:200],  # গুরুত্বপূর্ণ সামারি ডেটা
                    "status": status
                })
            except Exception:
                continue

        # যদি কোনো ব্লকে তথ্য না পাওয়া যায় তবে ব্যাকআপ স্ট্রাকচার ব্যবহার
        if not matches:
            all_links = soup.find_all('a')
            for link in all_links:
                href = link.get('href', '')
                if '/live-cricket-scores/' in href or '/cricket-scores/' in href:
                    text = link.get_text(strip=True)
                    if text and len(text) > 15:
                        matches.append({
                            "title": text,
                            "details": text,
                            "status": "Live/Scheduled"
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
        
    print(f"Scraping completed. Total matches found: {data.get('total_matches', 0)}")
