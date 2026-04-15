import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}

accession = "0000086312-26-000065"
accession_clean = accession.replace("-", "")
cik_num = "86312"

index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{accession_clean}/{accession}-index.htm"
print(f"Index URL: {index_url}\n")

r = requests.get(index_url, headers=HEADERS)
soup = BeautifulSoup(r.text, "html.parser")

print("All documents in filing:\n")
for row in soup.find_all("tr"):
    cells = row.find_all("td")
    if len(cells) >= 3:
        desc = cells[1].text.strip()
        link = cells[2].find("a")
        if link:
            print(f"  Desc: '{desc}' — {link['href']}")
