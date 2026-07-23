import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urljoin

BASE_URL = "https://bdcrictime.com"
TARGET_URL = "https://bdcrictime.com/live-scores"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def scrape_bdcrictime():
    matches = []
    try:
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return {"status": "error", "message": f"HTTP {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # BDcrictime এর ম্যাচ কন্টেইনার পার্সিং
        cards = soup.select('.match-card') or soup.select('.cb-mtch-lst') or soup.find_all('div', class_='match-box')

        for card in cards:
            try:
                # টুর্নামেন্ট/ম্যাচ টাইটেল
                title_elem = card.find('h3') or card.find('h4') or card.find('a')
                title = title_elem.text.strip() if title_elem else "Cricket Match"

                # টিমের ইমেজ / ফ্লাগ (Flag Images)
                img_tags = card.find_all('img')
                flags = []
                for img in img_tags:
                    src = img.get('src') or img.get('data-src') or ''
                    if src:
                        # রিলেটিভ ইউআরএল হলে ফুল ইউআরএলে রূপান্তর
                        full_img_url = urljoin(BASE_URL, src)
                        flags.append(full_img_url)

                # টিমের নাম এবং স্কোর
                scores = []
                score_elems = card.find_all('div', class_='team-score') or card.find_all('span', class_='score')
                
                if score_elems:
                    for s in score_elems:
                        scores.append(s.text.strip())
                else:
                    # ব্যাকআপ: পুরো কার্ডের টেক্সট থেকে স্কোর বের করা
                    card_text = card.get_text(separator=' ', strip=True)
                    scores.append(card_text)

                # ম্যাচের স্ট্যাটাস (Live / Result / Toss)
                status_elem = card.find('div', class_='status') or card.find('span', class_='match-status')
                status = status_elem.text.strip() if status_elem else "In Progress"

                matches.append({
                    "match_name": title,
                    "team_flags": flags,
                    "scores": scores,
                    "status": status
                })
            except Exception:
                continue

        # যদি কাস্টম সিলেক্টরে ম্যাচ না পাওয়া যায় তবে ব্রড স্ক্র্যাপার
        if not matches:
            all_cards = soup.find_all('div')
            for c in all_cards:
                text = c.get_text(strip=True)
                if ("vs" in text.lower() or "v/s" in text.lower()) and len(text) < 150:
                    imgs = [urljoin(BASE_URL, img['src']) for img in c.find_all('img') if img.get('src')]
                    matches.append({
                        "match_name": text,
                        "team_flags": imgs,
                        "scores": [text],
                        "status": "Live"
                    })
                    if len(matches) >= 5: # টপ ৫টি ক্যাচ
                        break

        return {
            "status": "success",
            "last_updated": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            "total_matches": len(matches),
            "matches": matches
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    data = scrape_bdcrictime()
    
    with open('score.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Scraped {data.get('total_matches', 0)} matches from bdcrictime.")
