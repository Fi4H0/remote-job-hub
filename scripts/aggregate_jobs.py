import os
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Constants & Filters
TARGET_KEYWORDS = [
    "agile delivery",
    "it project manager",
    "technical project manager",
    "project manager",
]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def matches_target_title(title):
    title_clean = title.lower()
    return any(kw in title_clean for kw in TARGET_KEYWORDS)


def classify_work_mode(text_context):
    text = text_context.lower()
    if "hybrid" in text:
        return "Hybrid"
    elif any(term in text for term in ["onsite", "on-site", "in-office", "office"]):
        return "Onsite"
    else:
        return "Remote"


# Source 1: We Work Remotely (RSS Parser)
def scrape_we_work_remotely():
    jobs = []
    rss_urls = [
        "https://weworkremotely.com/categories/remote-management-exec-jobs.rss",
        "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    ]
    for url in rss_urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                root = ET.fromstring(res.text)
                for item in root.findall(".//item"):
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""

                    if matches_target_title(title):
                        parts = title.split(":")
                        company = parts[0].strip() if len(parts) > 1 else "Unknown"
                        job_title = parts[1].strip() if len(parts) > 1 else title

                        jobs.append(
                            {
                                "title": job_title,
                                "company": company,
                                "source": "We Work Remotely",
                                "mode": "Remote",
                                "location": "Worldwide / Remote",
                                "link": link,
                                "date": datetime.today().strftime("%Y-%m-%d"),
                            }
                        )
        except Exception as e:
            print(f"WWR scrape error: {e}")
    return jobs


# Source 2: Remote OK (API)
def scrape_remote_ok():
    jobs = []
    try:
        res = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for item in data[1:]:  # First item is legal notice
                title = item.get("position", "")
                if matches_target_title(title):
                    jobs.append(
                        {
                            "title": title,
                            "company": item.get("company", "Unknown"),
                            "source": "Remote OK",
                            "mode": "Remote",
                            "location": item.get("location") or "Remote",
                            "link": item.get("url", ""),
                            "date": datetime.today().strftime("%Y-%m-%d"),
                        }
                    )
    except Exception as e:
        print(f"Remote OK scrape error: {e}")
    return jobs


# Source 3: Himalayas (API)
def scrape_himalayas():
    jobs = []
    try:
        res = requests.get("https://himalayas.app/jobs/api?limit=50", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json().get("jobs", [])
            for item in data:
                title = item.get("title", "")
                if matches_target_title(title):
                    location_restrictions = ", ".join(item.get("locationRestrictions", [])) or "Worldwide"
                    jobs.append(
                        {
                            "title": title,
                            "company": item.get("companyName", "Unknown"),
                            "source": "Himalayas",
                            "mode": "Remote",
                            "location": location_restrictions,
                            "link": item.get("applicationUrl") or item.get("url", ""),
                            "date": datetime.today().strftime("%Y-%m-%d"),
                        }
                    )
    except Exception as e:
        print(f"Himalayas scrape error: {e}")
    return jobs


# Source 4: Hiring Cafe (Search Endpoint Scraping)
def scrape_hiring_cafe():
    jobs = []
    try:
        for query in TARGET_KEYWORDS:
            encoded_q = urllib.parse.quote(query)
            res = requests.get(
                f"https://hiring.cafe/api/search?q={encoded_q}",
                headers=HEADERS,
                timeout=10,
            )
            if res.status_code == 200:
                results = res.json().get("results", [])
                for item in results:
                    title = item.get("title", "")
                    loc = item.get("location", "Remote")
                    mode = classify_work_mode(f"{title} {loc}")
                    jobs.append(
                        {
                            "title": title,
                            "company": item.get("company_name", "Unknown"),
                            "source": "Hiring Cafe",
                            "mode": mode,
                            "location": loc,
                            "link": item.get("apply_url", "https://hiring.cafe"),
                            "date": datetime.today().strftime("%Y-%m-%d"),
                        }
                    )
    except Exception as e:
        print(f"Hiring Cafe scrape error: {e}")
    return jobs


# Source 5: LinkedIn (Public Search endpoint)
def scrape_linkedin():
    jobs = []
    for query in TARGET_KEYWORDS:
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_query}&start=0"
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                postings = soup.find_all("li")
                for post in postings:
                    title_elem = post.find("h3", class_="base-search-card__title")
                    company_elem = post.find("h4", class_="base-search-card__subtitle")
                    location_elem = post.find("span", class_="job-search-card__location")
                    link_elem = post.find("a", class_="base-card__full-link")

                    if title_elem and company_elem:
                        title = title_elem.text.strip()
                        company = company_elem.text.strip()
                        location = location_elem.text.strip() if location_elem else "Not specified"
                        link = link_elem["href"] if link_elem else ""

                        mode = classify_work_mode(f"{title} {location}")

                        jobs.append(
                            {
                                "title": title,
                                "company": company,
                                "source": "LinkedIn",
                                "mode": mode,
                                "location": location,
                                "link": link,
                                "date": datetime.today().strftime("%Y-%m-%d"),
                            }
                        )
        except Exception as e:
            print(f"LinkedIn scrape error for {query}: {e}")
    return jobs


def deduplicate_jobs(jobs_list, threshold=0.85):
    """TF-IDF Cosine Similarity Deduplication engine"""
    if not jobs_list:
        return []

    df = pd.DataFrame(jobs_list)
    df["fingerprint"] = (
        df["title"].str.lower()
        + " "
        + df["company"].str.lower()
        + " "
        + df["location"].str.lower()
    )

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df["fingerprint"])
    cosine_sim = cosine_similarity(tfidf_matrix)

    indices_to_drop = set()
    for i in range(len(cosine_sim)):
        for j in range(i + 1, len(cosine_sim)):
            if cosine_sim[i, j] > threshold:
                indices_to_drop.add(j)

    df_clean = df.drop(index=list(indices_to_drop)).drop(columns=["fingerprint"])
    return df_clean.to_dict("records")


def notify_discord(new_jobs_count, jobs_data):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("No DISCORD_WEBHOOK_URL variable configured. Skipping webhook execution.")
        return

    preview_items = jobs_data[:5]
    preview_text = "\n".join(
        [
            f"• **{j['title']}** at {j['company']} `[{j['mode']}]` — *{j['source']}*"
            for j in preview_items
        ]
    )

    payload = {
        "username": "PM Job Aggregator Agent",
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/3858/3858682.png",
        "content": f"🚀 **Job Aggregator Pipeline Executed**\nAggregated unique postings from WWR, Remote OK, Himalayas, Hiring Cafe, and LinkedIn.\nFound **{new_jobs_count}** targeted roles.\n\n**Recent Openings Preview:**\n{preview_text}\n\n👉 *View full table on your GitHub Pages deployment.*",
    }

    res = requests.post(webhook_url, json=payload)
    res.raise_for_status()


if __name__ == "__main__":
    print("Initiating multi-source scraping jobs...")

    raw_jobs = []
    raw_jobs.extend(scrape_we_work_remotely())
    raw_jobs.extend(scrape_remote_ok())
    raw_jobs.extend(scrape_himalayas())
    raw_jobs.extend(scrape_hiring_cafe())
    raw_jobs.extend(scrape_linkedin())

    print(f"Raw scraped postings: {len(raw_jobs)}")
    clean_jobs = deduplicate_jobs(raw_jobs)
    print(f"Post-deduplication unique count: {len(clean_jobs)}")

    output_data = {
        "metadata": {
            "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_jobs": len(clean_jobs),
        },
        "jobs": clean_jobs,
    }

    os.makedirs("dist", exist_ok=True)
    with open("dist/jobs.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4)

    print("Exported results to dist/jobs.json")
    notify_discord(len(clean_jobs), clean_jobs)
