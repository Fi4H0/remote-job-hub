import os
import json
import requests
from jinja2 import Template

# Broad set of PM, IT PM, SDM, Telecom, and Agile keywords
TARGET_KEYWORDS = [
    "project manager", "project lead", "program manager",
    "delivery manager", "service delivery", "sdm",
    "telecom", "telecommunications", "it manager",
    "scrum master", "agile", "technical project", "pmo"
]

def is_target_job(title):
    """Returns True if the job title matches any management/telecom target keyword."""
    if not title:
        return False
    title_lower = title.lower()
    return any(kw in title_lower for kw in TARGET_KEYWORDS)

def fetch_remoteok_jobs():
    jobs = []
    try:
        url = "https://remoteok.com/api"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            # Scan top 300 postings
            for item in data[1:300]:
                if isinstance(item, dict):
                    title = item.get("position", "")
                    # Match target roles or include generic project/product/tech leads if list is small
                    if is_target_job(title):
                        jobs.append({
                            "title": title,
                            "company": item.get("company", "N/A"),
                            "location": item.get("location") or "Worldwide / Remote",
                            "source": "RemoteOK",
                            "source_class": "remoteok",
                            "url": item.get("url", "#"),
                            "date": "Recent"
                        })
    except Exception as e:
        print(f"Error fetching RemoteOK: {e}")
    return jobs

def fetch_himalayas_jobs():
    jobs = []
    try:
        # Search API directly for project/delivery management
        url = "https://himalayas.app/jobs/api?limit=150"
        res = requests.get(url, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            for item in data.get("jobs", []):
                title = item.get("title", "")
                if is_target_job(title):
                    jobs.append({
                        "title": title,
                        "company": item.get("companyName", "N/A"),
                        "location": "Worldwide / Remote",
                        "source": "Himalayas",
                        "source_class": "himalayas",
                        "url": item.get("applicationLink") or item.get("excerpt", "#"),
                        "date": "Recent"
                    })
    except Exception as e:
        print(f"Error fetching Himalayas: {e}")
    return jobs

def main():
    all_jobs = []
    all_jobs.extend(fetch_remoteok_jobs())
    all_jobs.extend(fetch_himalayas_jobs())

    print(f"Filtered {len(all_jobs)} matching PM/SDM/Telecom jobs.")

    # FALLBACK: If API feeds had zero strict matches today, fetch raw top recent jobs so dashboard is never empty
    if len(all_jobs) == 0:
        print("Notice: Zero strict keyword matches found in current feed batch. Applying fallback fetch...")
        try:
            res = requests.get("https://himalayas.app/jobs/api?limit=20", timeout=10)
            if res.status_code == 200:
                for item in res.json().get("jobs", [])[:15]:
                    all_jobs.append({
                        "title": item.get("title", "Project Manager / Lead"),
                        "company": item.get("companyName", "N/A"),
                        "location": "Worldwide / Remote",
                        "source": "Himalayas",
                        "source_class": "himalayas",
                        "url": item.get("applicationLink") or "#",
                        "date": "Recent"
                    })
        except Exception as e:
            print(f"Fallback fetch failed: {e}")

    # Save aggregated raw data
    with open("jobs.json", "w", encoding="utf-8") as f:
        json.dump(all_jobs, f, indent=2)

    # Render HTML from template
    if os.path.exists("template.html"):
        with open("template.html", "r", encoding="utf-8") as f:
            template_str = f.read()
            
        template = Template(template_str)
        rendered_html = template.render(jobs=all_jobs)

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(rendered_html)
        print("Successfully generated index.html!")
    else:
        print("Error: template.html not found.")

if __name__ == "__main__":
    main())
