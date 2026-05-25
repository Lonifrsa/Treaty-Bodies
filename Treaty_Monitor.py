
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime

# ----------------------------------
# CONFIGURATION
# ----------------------------------

BASE_URLS = [
    "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/SessionsList.aspx?Treaty=CEDAW",
    "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/SessionsList.aspx?Treaty=CED",
    "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/SessionsList.aspx?Treaty=CCPR",
    "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/SessionsList.aspx?Treaty=CESCR",
    "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/SessionsList.aspx?Treaty=CAT",
    "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/SessionsList.aspx?Treaty=CRC",
    "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/SessionsList.aspx?Treaty=CMW",
    "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/SessionsList.aspx?Treaty=CRPD",
    "https://tbinternet.ohchr.org/_layouts/15/TreatyBodyExternal/SessionsList.aspx?Treaty=CERD"
]

COUNTRIES = [
    "China", "Japan", "Mongolia",
    "Democratic People's Republic of Korea",
    "Republic of Korea",
    "Bangladesh", "Bhutan", "India", "Maldives", "Nepal",
    "Pakistan", "Sri Lanka",
    "Brunei", "Cambodia", "Indonesia",
    "Lao People's Democratic Republic",
    "Malaysia", "Myanmar", "Philippines",
    "Singapore", "Thailand", "Timor-Leste", "Vietnam"
]

OUTPUT_FILE = "treaty_body_results.xlsx"
SEEN_FILE = "seen_sessions.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ----------------------------------
# LOAD PREVIOUSLY SEEN LINKS
# ----------------------------------
try:
    with open(SEEN_FILE, "r") as f:
        seen_links = set(json.load(f))
except:
    seen_links = set()

all_session_links = set()
results = []

# ----------------------------------
# PROCESS EACH TREATY BODY PAGE
# ----------------------------------
for base_url in BASE_URLS:
    print(f"\nChecking: {base_url}")

    try:
        response = requests.get(base_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract all links on the page
        for a in soup.find_all("a", href=True):
            href = a["href"]

            if "Session" in href or "session" in href:
                full_url = href if href.startswith("http") else "https://tbinternet.ohchr.org" + href
                all_session_links.add(full_url)

    except Exception as e:
        print(f"Error accessing {base_url}: {e}")

# ----------------------------------
# IDENTIFY NEW SESSIONS
# ----------------------------------
new_links = [link for link in all_session_links if link not in seen_links]

print(f"\nNew sessions found: {len(new_links)}")

# ----------------------------------
# PROCESS EACH NEW SESSION PAGE
# ----------------------------------
for link in new_links:
    try:
        print(f"Opening: {link}")
        page = requests.get(link, headers=HEADERS)
        soup = BeautifulSoup(page.text, "html.parser")

        full_text = soup.get_text().lower()

        for country in COUNTRIES:
            if country.lower() in full_text:
                print(f"  → Match: {country}")

                # Extract PDFs
                pdf_links = []
                for a in soup.find_all("a", href=True):
                    if ".pdf" in a["href"].lower():
                        pdf_links.append(a["href"])

                results.append({
                    "country": country,
                    "session_url": link,
                    "treaty_body_page": base_url,
                    "pdf_links": ", ".join(pdf_links),
                    "date_detected": datetime.today().strftime("%Y-%m-%d")
                })

    except Exception as e:
        print(f"Error processing {link}: {e}")

# ----------------------------------
# SAVE RESULTS
# ----------------------------------
if results:
    df_new = pd.DataFrame(results)

    try:
        df_existing = pd.read_excel(OUTPUT_FILE)
        df = pd.concat([df_existing, df_new], ignore_index=True)
    except:
        df = df_new

    df.to_excel(OUTPUT_FILE, index=False)
    print("\n✅ Results saved to Excel")
else:
    print("\nNo new matches found")

# ----------------------------------
# UPDATE SEEN LINKS
# ----------------------------------
with open(SEEN_FILE, "w") as f:
    json.dump(list(all_session_links), f)

print("✅ Session tracking updated")


