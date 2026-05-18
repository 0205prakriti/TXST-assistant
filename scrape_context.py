# scrape_context.py
import requests
from bs4 import BeautifulSoup

def scrape_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}  # avoids basic bot blocks
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        # collapse excessive blank lines
        lines = [l for l in text.splitlines() if l.strip()]
        return "\n".join(lines)
    except Exception as e:
        print(f"  ⚠️  Failed to scrape {url}: {e}")
        return ""

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
    ]
}

for output_file, urls in pages.items():
    print(f"\n📄 Building {output_file}...")
    combined = ""
    for url in urls:
        print(f"  Scraping {url}")
        content = scrape_page(url)
        combined += f"\n\n--- SOURCE: {url} ---\n\n{content}"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(combined.strip())
    print(f"  ✅ Saved")

print("\n✅ Done. Check context/ folder.")