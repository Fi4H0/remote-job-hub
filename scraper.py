import os
import json
import requests
from jinja2 import Template

# Roles to target
TARGET_ROLES = [
    "project manager",
    "it project manager",
    "service delivery manager",
    "telecom project manager",
    "telecom",
    "telecommunications",
    "delivery manager",
    "program manager",
    "scrum master"
]

# Work from anywhere location keywords
ANYWHERE_KEYWORDS = ["worldwide", "anywhere", "global", "remote", "work from anywhere"]

def is_target_job(title, location=""):
    """Check if job title and location match our remote management criteria."""
    title_lower = title.lower()
    loc_lower = location.lower() if location else ""

    # Must match at least one target role
    matches_role = any(role in title_lower for role in TARGET_ROLES)
    
    # Check if location is non-restrictive/remote/worldwide (or defaults to remote)
    matches_location = any(k in loc_lower for k in ANYWHERE_KEYWORDS) if loc_lower else True

    return matches_role and matches_location

def fetch_remoteok_jobs():
    jobs = []
    try:
        url = "https://remoteok.com/api"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            # Scan top 200 recent postings (skipping index 0 legal notice)
            for item in data[1:200]:
                if isinstance(item, dict):
                    title = item.get("position", "N/A")
                    location = item.get("location") or "Worldwide / Remote"
                    
                    if is_target_job(title, location):
                        jobs.append({
                            "title": title,
                            "company": item.get("company", "N/A"),
                            "location": location,
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
        # Request up to 100 listings to capture target roles
        url = "https://himalayas.app/jobs/api?limit=100"
        res = requests.get(url, timeout=10)
        
        if res.status_code == 200:
            data = res.json()
            for item in data.get("jobs", []):
                title = item.get("title", "N/A")
                
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

    print(f"Scraped {len(all_jobs)} target remote PM / SDM / Telecom jobs.")

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
        print("Generated index.html successfully.")
    else:
        print("Warning: template.html not found.")

if __name__ == "__main__":
    main()
