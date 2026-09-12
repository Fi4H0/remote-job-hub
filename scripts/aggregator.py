import os
import re
import json
import hashlib
from datetime import datetime, timedelta, timezone
import requests
import feedparser
from bs4 import BeautifulSoup

# Expanded regex covering Project, Delivery, Scrum, Agile, and Implementation management
KEYWORDS_REGEX = re.compile(
    r'\b(project manager|project lead|program manager|delivery manager|service delivery|service manager|scrum master|agile coach|pmo|implementation manager|operations manager|technical manager|it manager)\b',
    re.IGNORECASE
)

# 30-day lookback window
CUTOFF_DATE = datetime.now(timezone.utc) - timedelta(days=30)

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
        "https://weworkremotely.com/categories/remote-management-and-finance-jobs.rss",
        "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    for url in feeds:
        try:
            res = requests.get(url, headers=headers, timeout=12)
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
            print(f"[WWR Error] {e}")
    print(f"-> WeWorkRemotely matched: {len(jobs)} jobs")
    return jobs

def fetch_himalayas():
    jobs = []
    url = "https://himalayas.app/jobs/rss"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=12)
        parsed = feedparser.parse(res.content)
        for entry in parsed.entries:
            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if hasattr(entry, 'published_parsed') else None
            if pub_date and not is_recent(pub_date):
                continue

            title = entry.get('title', '')
            company = entry.get('author', 'Himalayas')

            if KEYWORDS_REGEX.search(title) or KEYWORDS_REGEX.search(entry.get('summary', '')):
                jobs.append({
                    "id": generate_job_id(title, company),
                    "title": title,
                    "company": company,
                    "location": "Remote",
                    "source": "Himalayas",
                    "url": entry.get('link', ''),
                    "posted_date": pub_date.strftime('%Y-%m-%d') if pub_date else "Recently",
                    "snippet": BeautifulSoup(entry.get('summary', ''), 'html.parser').text[:250] + '...'
                })
    except Exception as e:
        print(f"[Himalayas Error] {e}")
    print(f"-> Himalayas matched: {len(jobs)} jobs")
    return jobs

def fetch_remoteok():
    jobs = []
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 200:
            data = res.json()
            for item in data[1:]:
                if not isinstance(item, dict):
                    continue
                title = item.get('position', '')
                tags_str = " ".join(item.get('tags', []))
                full_search = f"{title} {tags_str}"
                
                date_str = item.get('date')
                pub_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')) if date_str else None

                if pub_date and not is_recent(pub_date):
                    continue

                if KEYWORDS_REGEX.search(full_search):
                    jobs.append({
                        "id": generate_job_id(title, item.get('company', 'RemoteOK')),
                        "title": title,
                        "company": item.get('company', 'RemoteOK'),
                        "location": f"Remote ({item.get('location', 'Global')})",
                        "source": "Remote OK",
                        "url": item.get('url', ''),
                        "posted_date": pub_date.strftime('%Y-%m-%d') if pub_date else "Recently",
                        "snippet": BeautifulSoup(item.get('description', ''), 'html.parser').text[:250] + '...'
                    })
    except Exception as e:
        print(f"[RemoteOK Error] {e}")
    print(f"-> RemoteOK matched: {len(jobs)} jobs")
    return jobs

def fetch_jobspresso():
    jobs = []
    url = "https://jobspresso.co/category/project-management/feed/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        res = requests.get(url, headers=headers, timeout=12)
        parsed = feedparser.parse(res.content)
        for entry in parsed.entries:
            pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc) if hasattr(entry, 'published_parsed') else None
            if pub_date and not is_recent(pub_date):
                continue

            title = entry.get('title', '')
            company = "Jobspresso Employer"

            if KEYWORDS_REGEX.search(title):
                jobs.append({
                    "id": generate_job_id(title, company),
                    "title": title,
                    "company": company,
                    "location": "Remote",
                    "source": "Jobspresso",
                    "url": entry.get('link', ''),
                    "posted_date": pub_date.strftime('%Y-%m-%d') if pub_date else "Recently",
                    "snippet": BeautifulSoup(entry.get('summary', ''), 'html.parser').text[:250] + '...'
                })
    except Exception as e:
        print(f"[Jobspresso Error] {e}")
    print(f"-> Jobspresso matched: {len(jobs)} jobs")
    return jobs

def send_discord_alerts(jobs):
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("CRITICAL: DISCORD_WEBHOOK_URL environment variable missing.")
        return

    if not jobs:
        requests.post(webhook_url, json={"content": "ℹ️ **Remote Job Hub**: No matching jobs found in the last 30 days."})
        return

    requests.post(webhook_url, json={
        "content": f"🚀 **Remote PM Alert**: Found **{len(jobs)}** matching positions in the last 30 days!"
    })

    chunk_size = 10
    top_jobs = jobs[:30] # Limit Discord output to top 30 to prevent payload limits
    
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
        
        requests.post(webhook_url, json={"embeds": embeds})

def main():
    print("Starting job collection across sources...")
    all_jobs = []
    
    all_jobs.extend(fetch_weworkremotely())
    all_jobs.extend(fetch_himalayas())
    all_jobs.extend(fetch_remoteok())
    all_jobs.extend(fetch_jobspresso())

    deduped = {}
    for j in all_jobs:
        if j["id"] not in deduped:
            deduped[j["id"]] = j

    final_jobs = list(deduped.values())
    print(f"Total Unique Matches: {len(final_jobs)}")

    os.makedirs('data', exist_ok=True)
    with open('data/jobs.json', 'w', encoding='utf-8') as f:
        json.dump(final_jobs, f, indent=2)

    send_discord_alerts(final_jobs)

if __name__ == "__main__":
    main()
