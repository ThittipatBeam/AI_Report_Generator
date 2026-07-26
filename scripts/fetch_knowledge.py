import urllib.request
import urllib.parse
import json
import re
import os
import time
from html.parser import HTMLParser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "knowledge", "knowledge_base.txt")

class HTMLParagraphExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.in_p = False
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'p':
            self.in_p = True
            self.current_text = []

    def handle_endtag(self, tag):
        if tag == 'p':
            self.in_p = False
            full_p = "".join(self.current_text).strip()
            # Remove citations like [1], [2], [citation needed]
            full_p = re.sub(r'\[\d+\]', '', full_p)
            full_p = re.sub(r'\[citation needed\]', '', full_p)
            if len(full_p) > 40:  # Keep substantial paragraphs
                self.paragraphs.append(full_p)

    def handle_data(self, data):
        if self.in_p:
            self.current_text.append(data)

def fetch_live_web_paragraphs(url, retries=3):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    })
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                html_content = response.read().decode('utf-8', errors='ignore')
                parser = HTMLParagraphExtractor()
                parser.feed(html_content)
                return parser.paragraphs[:10]  # Take top 10 substantial live paragraphs
        except Exception as e:
            print(f"  [!] Attempt {attempt}/{retries} failed for {url}: {e}")
            if attempt < retries:
                time.sleep(1)
    return []

def main():
    # Exactly 7 Diverse Topics (Live website URLs in both EN and TH)
    topics_config = [
        {
            "num": 1,
            "title": "Domestic Cat (แมวบ้าน)",
            "en_url": "https://en.wikipedia.org/wiki/Cat",
            "th_url": f"https://th.wikipedia.org/wiki/{urllib.parse.quote('แมว')}"
        },
        {
            "num": 2,
            "title": "Video Game - Minecraft (เกมไมน์คราฟต์)",
            "en_url": "https://en.wikipedia.org/wiki/Minecraft",
            "th_url": f"https://th.wikipedia.org/wiki/{urllib.parse.quote('ไมน์คราฟต์')}"
        },
        {
            "num": 3,
            "title": "Food & Culinary - Gelato Science & Culture (เจลาโต)",
            "en_url": "https://en.wikipedia.org/wiki/Gelato",
            "th_url": f"https://th.wikipedia.org/wiki/{urllib.parse.quote('เจลาโต')}"
        },
        {
            "num": 4,
            "title": "Banking & Finance - Bangkok Bank / BBL (ธนาคารกรุงเทพ)",
            "en_url": "https://en.wikipedia.org/wiki/Bangkok_Bank",
            "th_url": f"https://th.wikipedia.org/wiki/{urllib.parse.quote('ธนาคารกรุงเทพ')}"
        },
        {
            "num": 5,
            "title": "Space Astronomy - James Webb Space Telescope (กล้องเจมส์ เวบบ์)",
            "en_url": "https://en.wikipedia.org/wiki/James_Webb_Space_Telescope",
            "th_url": f"https://th.wikipedia.org/wiki/{urllib.parse.quote('กล้องโทรทรรศน์อวกาศเจมส์_เวบบ์')}"
        },
        {
            "num": 6,
            "title": "Culinary Science - Coffee Brewing Methods (การชงกาแฟ)",
            "en_url": "https://en.wikipedia.org/wiki/Coffee_brewing",
            "th_url": f"https://th.wikipedia.org/wiki/{urllib.parse.quote('กาแฟ')}"
        },
        {
            "num": 7,
            "title": "Finance & Economics - Index Funds & S&P 500 (กองทุนดัชนี และ S&P 500)",
            "en_url": "https://en.wikipedia.org/wiki/S%26P_500",
            "th_url": f"https://th.wikipedia.org/wiki/{urllib.parse.quote('กองทุนดัชนี')}"
        }
    ]

    all_blocks = []

    for item in topics_config:
        num = item["num"]
        title = item["title"]
        en_url = item["en_url"]
        th_url = item["th_url"]

        print(f"Fetching Topic {num}: {title}...")
        print(f"  -> Live EN: {en_url}")
        print(f"  -> Live TH: {th_url}")

        en_paras = fetch_live_web_paragraphs(en_url)
        th_paras = fetch_live_web_paragraphs(th_url)

        en_text = "\n\n".join(en_paras) if en_paras else "No live paragraphs extracted."
        th_text = "\n\n".join(th_paras) if th_paras else "No live paragraphs extracted."

        block = f"""=== TOPIC {num}: {title} ===
LIVE SOURCE URL (EN): {en_url}
LIVE SOURCE URL (TH): {th_url}

[ENGLISH LIVE WEB CONTENT]
{en_text}

[THAI LIVE WEB CONTENT / เนื้อหาจากเว็บภาษาไทย]
{th_text}"""

        all_blocks.append(block)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    full_output = "\n\n" + ("=" * 80) + "\n\n".join(all_blocks) + "\n\n" + ("=" * 80) + "\n"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_output)

    print(f"\nSUCCESS! Saved 7 topics of 100% live web content into {OUTPUT_FILE} ({len(full_output)} bytes)")

if __name__ == "__main__":
    main()
