"""Refresh official campus sources without replacing good data after a failed fetch."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent


def extract_content(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else "Texas State University"
    content = soup.find("main") or soup
    for tag in content.select("script, style, nav, footer, header, aside, .sr-only"):
        tag.decompose()
    # Keep accordion answers (often visually hidden until expanded).
    text = "\n".join(line.strip() for line in content.get_text("\n", strip=True).splitlines() if line.strip())
    if len(text) < 200:
        raise ValueError("Page contains too little content to index")
    return title, text


def scrape_page(url: str) -> dict:
    response = requests.get(url, headers={"User-Agent": "TXST-Student-Assistant/1.0"}, timeout=25)
    response.raise_for_status()
    title, text = extract_content(response.text)
    return {"url": response.url, "title": title, "text": text,
            "retrieved_at": datetime.now(timezone.utc).isoformat()}

pages = {
    "context/academics.txt": [
        "https://mycatalog.txstate.edu/undergraduate/general-information/academic-policies/regulations/",
        "https://mycatalog.txstate.edu/undergraduate/general-information/academic-policies/registration/",
        "https://onestop.txst.edu/important-dates.html",
        "https://www.registrar.txst.edu/registration/ac/academic-calendar.html",
    ],
    "context/campus.txt": [
        "https://www.lbjsc.txst.edu/about/maps-and-hours.html",
        "https://www.studentsuccess.txst.edu/departments/support-services/dining.html",
        "https://parking.txst.edu/regulations",
        "https://www.library.txst.edu/about/directions-parking.html",
    ],
    "context/financial_aid.txt": [
        "https://onestop.txst.edu/financial-aid/how.html",
        "https://onestop.txst.edu/financial-aid/scholarships.html",
        "https://onestop.txst.edu/financial-aid/scholarships/boss.html",
        "https://onestop.txst.edu/financial-aid/learn-more/eligibility.html",
        "https://onestop.txst.edu/financial-aid/learn-more/verification.html",
        "https://onestop.txst.edu/financial-aid/learn-more/understanding-my-aid.html",
        "https://onestop.txst.edu/financial-aid/learn-more/maintain.html",
        "https://onestop.txst.edu/financial-aid/learn-more/recfa.html",
        "https://onestop.txst.edu/financial-aid/learn-more/types.html",
        "https://onestop.txst.edu/financial-aid/learn-more/types/grants.html",
        "https://onestop.txst.edu/financial-aid/learn-more/types/loans.html",
        "https://onestop.txst.edu/financial-aid/learn-more/types/workstudy.html",
        "https://onestop.txst.edu/financial-aid/learn-more/icons/bobcatpromise.html",
        "https://onestop.txst.edu/financial-aid/how/summer-finaid.html",
    ]
}


def refresh(output_file: str, urls: list[str]):
    records = []
    for url in urls:
        print(f"  Scraping {url}")
        records.append(scrape_page(url))
    # Fetch every page before writing: errors preserve the existing domain snapshot.
    path = ROOT / output_file
    path.parent.mkdir(parents=True, exist_ok=True)
    combined = "\n\n".join(f"--- SOURCE: {r['url']} ---\n\n{r['title']}\n\n{r['text']}" for r in records)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(combined, encoding="utf-8")
    temporary.replace(path)
    metadata = [{k: v for k, v in r.items() if k != "text"} for r in records]
    path.with_suffix(".sources.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(records)} sources to {output_file}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", choices=["academics", "campus", "financial_aid"])
    args = parser.parse_args()
    for output_file, urls in pages.items():
        if args.domain is None or Path(output_file).stem == args.domain:
            refresh(output_file, urls)


if __name__ == "__main__":
    main()
