import os
import re
import json
import hashlib
import urllib.parse
from datetime import datetime, timedelta, timezone
import requests
import feedparser
from bs4 import BeautifulSoup

KEYWORDS_REGEX = re.compile(
    r'\b(project manager|service delivery|delivery manager|scrum master|technical project manager)\b',
    re.IGNORECASE
)

CUTOFF_DATE = datetime.now(timezone.utc) - timedelta(days=10)

def generate_job_id(title, company):
    clean = re.sub(r'[^a-zA-Z0-9]', '', f"{title.lower()}_{company.lower()}")
    return hashlib.md5(clean.encode('utf-8')).hexdigest()

def is_recent(dt):
    if not dt:
        return True
    return dt >= CUTOFF_DATE

def fetch_weworkremotely():
    jobs = []
    feeds = [
        "https://weworkremotely.com/categories/remote-product-jobs.rss",
        "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for url in feeds:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            parsed = feedparser.parse(res.content)
            for entry in parsed.entries:
                pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if hasattr(entry, 'published_parsed') else None
                if pub_date and not is_recent(pub_date):
                    continue
                
                title = entry.get('title', '')
                company = "WeWorkRemotely Employer"
                if " is hiring a " in title:
                    parts = title.split(" is hiring a ")
                    company = parts[0].strip()
                    title = parts[1].strip()

                if KEYWORDS_REGEX.search(title):
                    jobs.append({
                        "id": generate_job_id(title, company),
                        "title": title,
                        "company": company,
                        "location": "Remote",
                        "source": "We Work Remotely",
                        "url": entry.get('link', ''),
                        "posted_date": pub_date.strftime('%Y-%m-%d') if pub_date else "Recently",
                        "snippet": BeautifulSoup(entry.get('summary', ''), 'html.parser').text[:250] + '...'
                    })
        except Exception as e:
            print(f"Error fetching WWR: {e}")
    return jobs

def fetch_himalayas():
    jobs = []
    url = "https://himalayas.app/jobs/api?limit=100"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json().get('jobs', [])
            for item in data:
                title = item.get('title', '')
                pub_timestamp = item.get('pubDate')
                pub_date = datetime.fromtimestamp(pub_timestamp, tz=timezone.utc) if pub_timestamp else None

                if pub_date and not is_recent(pub_date):
                    continue

                if KEYWORDS_REGEX.search(title):
                    jobs.append({
                        "id": generate_job_id(title, item.get('companyName', 'Himalayas')),
                        "title": title,
                        "company": item.get('companyName', 'Himalayas'),
                        "location": f"Remote ({', '.join(item.get('parentCategories', ['Global']))})",
                        "source": "Himalayas",
                        "url": item.get('applicationUrl') or f"https://himalayas.app/jobs/{item.get('slug', '')}",
                        "posted_date": pub_date.strftime('%Y-%m-%d') if pub_date else "Recently",
                        "snippet": item.get('excerpt', '')[:250] + '...'
                    })
    except Exception as e:
        print(f"Error fetching Himalayas: {e}")
    return jobs

def fetch_remoteok():
    jobs = []
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for item in data[1:]:
                if not isinstance(item, dict):
                    continue
                title = item.get('position', '')
                date_str = item.get('date')
                pub_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')) if date_str else None

                if pub_date and not is_recent(pub_date):
                    continue

                if KEYWORDS_REGEX.search(title):
                    jobs.append({
                        "id": generate_job_id(title, item.get('company', 'RemoteOK')),
                        "title": title,
                        "company": item.get('company', 'RemoteOK'),
                        "location": f"Remote ({item.get('location', 'Global')})",
                        "source": "Remote OK",
                        "url": item.get('url', ''),
                        "posted_date": pub_date.strftime('%Y-%m-%d') if pub_date else "Recently",
                        "snippet": item.get('description', '')[:250] + '...'
                    })
    except Exception as e:
        print(f"Error fetching Remote OK: {e}")
    return jobs

def send_discord_alerts(jobs):
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("CRITICAL: DISCORD_WEBHOOK_URL is missing from environment secrets.")
        return

    print(f"Sending alerts to Discord webhook (Found {len(jobs)} jobs)...")

    if not jobs:
        res = requests.post(webhook_url, json={"content": "ℹ️ **Remote Job Hub**: Scraper ran successfully, but no matching PM/Service Delivery jobs were found in the last 7 days."})
        print(f"Discord response: {res.status_code}")
        return

    requests.post(webhook_url, json={
        "content": f"🚀 **Weekly Remote PM Alert**: Found **{len(jobs)}** positions posted in the last 10 days!"
    })

    chunk_size = 10
    top_jobs = jobs[:20]
    
    for i in range(0, len(top_jobs), chunk_size):
        chunk = top_jobs[i:i + chunk_size]
        embeds = []
        for j in chunk:
            embeds.append({
                "title": f"💼 {j['title']}",
                "url": j['url'],
                "color": 5814783,
                "fields": [
                    {"name": "Company", "value": j['company'] or "N/A", "inline": True},
                    {"name": "Source", "value": j['source'], "inline": True},
                    {"name": "Location", "value": j['location'], "inline": True}
                ],
                "footer": {"text": f"Posted: {j['posted_date']}"}
            })
        
        res = requests.post(webhook_url, json={"embeds": embeds})
        print(f"Batch {i//chunk_size + 1} sent to Discord. Status: {res.status_code}")

def main():
    print("Starting job collection...")
    all_jobs = []
    
    all_jobs.extend(fetch_weworkremotely())
    all_jobs.extend(fetch_himalayas())
    all_jobs.extend(fetch_remoteok())

    deduped = {}
    for j in all_jobs:
        if j["id"] not in deduped:
            deduped[j["id"]] = j

    final_jobs = list(deduped.values())
    print(f"Collected {len(final_jobs)} jobs.")

    os.makedirs('data', exist_ok=True)
    with open('data/jobs.json', 'w', encoding='utf-8') as f:
        json.dump(final_jobs, f, indent=2)

    send_discord_alerts(final_jobs)

if __name__ == "__main__":
    main()
