import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}

def get_text(ticker, cik_num, accession):
    accession_clean = accession.replace("-", "")
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{accession_clean}/{accession}-index.htm"
    r = requests.get(index_url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    doc_url = None
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 3:
            desc = cells[1].text.strip()
            link = cells[2].find("a")
            if link and "10-K" in desc and ".htm" in link["href"]:
                href = link["href"]
                if "/ix?doc=" in href:
                    href = href.split("/ix?doc=")[1]
                doc_url = f"https://www.sec.gov{href}"
                break
    print(f"{ticker} document: {doc_url}")
    r = requests.get(doc_url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

# MetLife
print("Fetching MET...")
met_text = get_text("MET", "1099219", "0001099219-26-000013")
with open("met_filing_text.txt", "w") as f:
    f.write(met_text)

# Search MET for missing fields
print("\nMET — searching for missing fields:")
markers = [
    "Total assets",
    "Total equity",
    "Earnings per share",
    "per share",
    "Basic earnings",
    "Total revenues",
    "Net revenues",
]
for marker in markers:
    idx = met_text.lower().find(marker.lower())
    if idx != -1:
        print(f"  '{marker}' at {idx:,}: {met_text[idx:idx+120].strip()[:100]}")
    else:
        print(f"  '{marker}' NOT FOUND")

# Travelers
print("\n\nFetching TRV...")
trv_text = get_text("TRV", "86312", "0000086312-26-000010")
with open("trv_filing_text.txt", "w") as f:
    f.write(trv_text)

print("\nTRV — searching for missing fields:")
markers = [
    "Total revenues",
    "Net written premiums",
    "Earned premiums",
    "Total revenue",
    "Revenues",
    "Loss ratio",
]
for marker in markers:
    idx = trv_text.lower().find(marker.lower())
    if idx != -1:
        print(f"  '{marker}' at {idx:,}: {trv_text[idx:idx+120].strip()[:100]}")
    else:
        print(f"  '{marker}' NOT FOUND")
