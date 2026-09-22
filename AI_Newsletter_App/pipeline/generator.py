import os
import requests
import xml.etree.ElementTree as ET
import urllib.parse
from datetime import datetime
from typing import Dict, List

RESEARCH_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "research_data")

RESEARCH_FILES = [
    "newsletter_web_research_results.md",
    "newsletter_reliability_rbi.md",
    "newsletter_ai_products.md",
    "newsletter_github_repos.md",
    "newsletter_research_papers.md",
    "newsletter_twitter_highlights.md"
]

def ensure_research_dir():
    os.makedirs(RESEARCH_DIR, exist_ok=True)

def fetch_live_google_news(query: str, max_results: int = 3) -> List[Dict]:
    """
    Option 1: Fetches real-time live articles from Google News RSS Engine.
    Requires ZERO API keys, is 100% free, and always returns breaking, recent news.
    """
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-US&gl=US&ceid=US:en"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return []
        
        root = ET.fromstring(resp.text)
        items = root.findall('.//item')
        articles = []
        for it in items[:max_results]:
            raw_title = it.find('title').text if it.find('title') is not None else "Breaking Industry Dispatch"
            source = it.find('source').text if it.find('source') is not None else "News Source"
            link = it.find('link').text if it.find('link') is not None else ""
            pub_date = it.find('pubDate').text if it.find('pubDate') is not None else ""
            
            clean_title = raw_title.rsplit(' - ', 1)[0] if ' - ' in raw_title else raw_title
            
            articles.append({
                "title": clean_title.strip(),
                "source": source.strip(),
                "link": link.strip(),
                "pub_date": pub_date[:16] if len(pub_date) >= 16 else pub_date
            })
        return articles
    except Exception as e:
        print(f"Error querying Google News for '{query}':", e)
        return []

def fetch_live_arxiv_papers(query: str = 'cat:cs.AI OR cat:cs.LG OR all:"predictive maintenance"', max_results: int = 4) -> List[Dict]:
    """Fetches real, live papers from the official ArXiv API."""
    url = f"http://export.arxiv.org/api/query?search_query={requests.utils.quote(query)}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}"
    try:
        resp = requests.get(url, timeout=12)
        if resp.status_code != 200:
            return []
        
        root = ET.fromstring(resp.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)
        
        papers = []
        for e in entries:
            title = e.find('atom:title', ns).text.strip().replace('\n', ' ')
            abs_url = e.find('atom:id', ns).text.strip().replace("http://", "https://")
            summary = e.find('atom:summary', ns).text.strip().replace('\n', ' ')
            published = e.find('atom:published', ns).text.strip()[:10]
            authors = [a.find('atom:name', ns).text for a in e.findall('atom:author', ns)]
            
            short_summary = summary[:280] + "..." if len(summary) > 280 else summary
            
            papers.append({
                "title": title,
                "url": abs_url,
                "summary": short_summary,
                "published": published,
                "authors": ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
            })
        return papers
    except Exception as e:
        print("Error fetching from arXiv API:", e)
        return []

def update_arxiv_file_with_live_data():
    """Queries live ArXiv and overwrites newsletter_research_papers.md with real papers."""
    ensure_research_dir()
    papers = fetch_live_arxiv_papers()
    if not papers:
        return
    today_str = datetime.now().strftime("%B %d, %Y")
    lines = [f"# Live arXiv Research Desk — Dispatched {today_str}\n"]
    lines.append("*Direct query results from export.arxiv.org API (cs.AI, cs.LG, Predictive Maintenance & Reliability)*\n")
    for i, p in enumerate(papers, start=1):
        lines.append(f"### {i}. [{p['title']}]({p['url']})")
        lines.append(f"- **Authors**: {p['authors']}")
        lines.append(f"- **Published Date**: {p['published']}")
        lines.append(f"- **Reference Link**: [{p['url']}]({p['url']})")
        lines.append(f"- **Abstract Core**: {p['summary']}\n")
    with open(os.path.join(RESEARCH_DIR, "newsletter_research_papers.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def update_all_live_intelligence():
    """
    Dynamically pulls breaking news via Google News RSS and ArXiv API,
    updating the raw markdown streams with real-time live data.
    """
    ensure_research_dir()
    today_str = datetime.now().strftime("%B %d, %Y")

    # 1. Update ArXiv Papers
    update_arxiv_file_with_live_data()

    # 2. Update AI & Oil/Gas with Google News
    ai_news = fetch_live_google_news('artificial intelligence compute OR "data center" energy OR "frontier model"', max_results=3)
    og_news = fetch_live_google_news('oil gas energy "digital twin" OR refinery OR pipeline', max_results=3)
    
    web_lines = [f"# Global Industry Intelligence: AI, Energy & Oil & Gas (Live Google News - {today_str})\n"]
    web_lines.append("*Real-time dispatches aggregated via Google News live RSS search*\n")
    
    if ai_news:
        web_lines.append("## ⚡ Frontier AI & Data Center Energy Infrastructure\n")
        for i, a in enumerate(ai_news, start=1):
            web_lines.append(f"### {i}. [{a['title']}]({a['link']})")
            web_lines.append(f"- **Publisher**: {a['source']} • **Published**: {a['pub_date']}")
            web_lines.append(f"- **Reference Link**: [{a['source']} Live Dispatch]({a['link']})\n")
            
    if og_news:
        web_lines.append("## 🛢️ Oil & Gas Operations, Pipelines & Refining\n")
        for i, a in enumerate(og_news, start=1):
            web_lines.append(f"### {i}. [{a['title']}]({a['link']})")
            web_lines.append(f"- **Publisher**: {a['source']} • **Published**: {a['pub_date']}")
            web_lines.append(f"- **Reference Link**: [{a['source']} Live Dispatch]({a['link']})\n")
            
    with open(os.path.join(RESEARCH_DIR, "newsletter_web_research_results.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(web_lines))

    # 3. Update Reliability & RBI with Google News
    rbi_news = fetch_live_google_news('"mechanical integrity" OR "risk based inspection" OR corrosion OR "nondestructive testing"', max_results=3)
    rbi_lines = [f"# Reliability Engineering, Asset Integrity & RBI (Live Dispatches - {today_str})\n"]
    rbi_lines.append("*Real-time mechanical integrity, NDE, and corrosion engineering dispatches from Google News*\n")
    if rbi_news:
        for i, a in enumerate(rbi_news, start=1):
            rbi_lines.append(f"### {i}. [{a['title']}]({a['link']})")
            rbi_lines.append(f"- **Publisher**: {a['source']} • **Published**: {a['pub_date']}")
            rbi_lines.append(f"- **Reference Link**: [{a['source']} Technical Dispatch]({a['link']})\n")
    else:
        rbi_lines.append("### 1. [Quantitative Risk-Based Inspection (RBI) Modeling per API 581](https://www.api.org/products-and-services/standards)")
        rbi_lines.append("- **Standard**: American Petroleum Institute (API) 580/581")
        rbi_lines.append("- **Focus**: Systematic POF/COF calculation and PCML inspection scheduling.\n")
        
    with open(os.path.join(RESEARCH_DIR, "newsletter_reliability_rbi.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(rbi_lines))

def fetch_live_x_highlights(max_results: int = 3) -> List[Dict]:
    """
    Fetches real-time coverage and dispatches on recent posts, statements, and debates
    from top AI engineering voices (Karpathy, Altman, LeCun, Amodei) from the past 24-48 hours.
    """
    query = '("Sam Altman" OR "Karpathy" OR "Yann LeCun" OR "Dario Amodei") (AI OR reasoning OR coding OR model)'
    return fetch_live_google_news(query, max_results=max_results)

def get_all_research_files() -> Dict[str, str]:
    ensure_research_dir()
    data = {}
    for fname in RESEARCH_FILES:
        fpath = os.path.join(RESEARCH_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                data[fname] = f.read()
        else:
            data[fname] = f"# {fname.replace('.md', '').replace('_', ' ').title()}\n\n*No data gathered yet.*"
    return data

def get_research_file(filename: str) -> str:
    ensure_research_dir()
    if filename not in RESEARCH_FILES:
        raise ValueError(f"Invalid research file: {filename}")
    fpath = os.path.join(RESEARCH_DIR, filename)
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def save_research_file(filename: str, content: str) -> bool:
    ensure_research_dir()
    if filename not in RESEARCH_FILES:
        raise ValueError(f"Invalid research file: {filename}")
    fpath = os.path.join(RESEARCH_DIR, filename)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    return True
