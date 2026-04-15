import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}

# Get Prudential's latest 10-K
url = "https://data.sec.gov/submissions/CIK0001137774.json"
r = requests.get(url, headers=headers)
data = r.json()
filings = data["filings"]["recent"]

accession = None
for i, form in enumerate(filings["form"]):
    if form == "10-K":
        accession = filings["accessionNumber"][i]
        print(f"Found 10-K: {accession} filed {filings['filingDate'][i]}")
        break

accession_clean = accession.replace("-", "")
index_url = f"https://www.sec.gov/Archives/edgar/data/1137774/{accession_clean}/{accession}-index.htm"
r = requests.get(index_url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")

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
            print(f"Document: {doc_url}")
            break

print("\nDownloading and searching...")
r = requests.get(doc_url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")
for tag in soup(["script", "style"]):
    tag.decompose()
text = soup.get_text(separator="\n", strip=True)

markers = [
    "Total revenues",
    "Total assets",
    "Total equity",
    "per share",
    "combined ratio",
    "loss ratio",
    "Benefits and expenses",
    "Revenues"
]

print("\nKey term positions:\n")
for marker in markers:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        print(f"'{marker}' at {idx:,}")
        print(f"  {text[idx:idx+150].strip()[:120]}")
        print()
    else:
        print(f"'{marker}' NOT FOUND\n")

with open("pru_filing_text.txt", "w") as f:
    f.write(text)
print("Saved to pru_filing_text.txt")
