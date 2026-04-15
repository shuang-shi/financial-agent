import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}

# Get Chubb's CIK and latest 10-K
url = "https://data.sec.gov/submissions/CIK0000896159.json"
r = requests.get(url, headers=headers)
data = r.json()
print(f"Company: {data['name']}")

filings = data["filings"]["recent"]
accession = None
for i, form in enumerate(filings["form"]):
    if form == "10-K":
        accession = filings["accessionNumber"][i]
        print(f"10-K: {accession} filed {filings['filingDate'][i]}")
        break

accession_clean = accession.replace("-", "")
cik_num = "896159"
index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{accession_clean}/{accession}-index.htm"
r = requests.get(index_url, headers=headers)
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
            print(f"Document: {doc_url}")
            break

print("\nDownloading...")
r = requests.get(doc_url, headers=headers)
soup = BeautifulSoup(r.text, "html.parser")
for tag in soup(["script", "style"]):
    tag.decompose()
text = soup.get_text(separator="\n", strip=True)

markers = [
    "Total assets",
    "Total shareholders",
    "Net premiums earned",
    "combined ratio",
    "loss ratio",
    "Total revenues",
    "per share",
    "Basic earnings"
]

print("\nKey term positions:\n")
for marker in markers:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        print(f"'{marker}' at {idx:,}")
        print(f"  {text[idx:idx+200].strip()[:150]}")
        print()
    else:
        print(f"'{marker}' NOT FOUND\n")

with open("cb_filing_text.txt", "w") as f:
    f.write(text)
print("Saved to cb_filing_text.txt")
