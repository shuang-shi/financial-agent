import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Shuang Shi shuangshi@sandiego.edum"}

# Build the filing index URL
accession = "0000005272-26-000023"
accession_clean = accession.replace("-", "")
index_url = f"https://www.sec.gov/Archives/edgar/data/5272/{accession_clean}/{accession}-index.htm"

print("Fetching filing index...")
response = requests.get(index_url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Find the main 10-K document link
print("\nDocuments in this filing:")
for row in soup.find_all("tr"):
    cells = row.find_all("td")
    if len(cells) >= 3:
        desc = cells[1].text.strip()
        link = cells[2].find("a")
        if link:
            print(f"  {desc}: {link['href']}")
