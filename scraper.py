import os
import json
import requests
from jinja2 import Template

def fetch_remoteok_jobs():
    jobs = []
    try:
        url = "https://remoteok.com/api"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for item in data[1:15]:  # Take top 15 non-header records
                if isinstance(item, dict):
                    jobs.append({
                        "title": item.get("position", "N/A"),
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
        url = "https://himalayas.app/jobs/api?limit=15"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("jobs", []):
                jobs.append({
                    "title": item.get("title", "N/A"),
                    "company": item.get("companyName", "N/A"),
                    "location": "Remote",
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

if __name__ == "__main__":
    main()
