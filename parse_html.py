import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}

# Download the main 10-K document
url = "https://www.sec.gov/Archives/edgar/data/5272/000000527226000023/aig-20251231.htm"

print("Downloading AIG 10-K... (this may take 30 seconds, file is large)")
response = requests.get(url, headers=headers)

print("Parsing...")
soup = BeautifulSoup(response.text, "html.parser")

for tag in soup(["script", "style"]):
    tag.decompose()

full_text = soup.get_text(separator="\n", strip=True)

print(f"Total characters: {len(full_text):,}")
print(f"Total lines: {full_text.count(chr(10)):,}")
print("\nFirst 1000 characters preview:")
print(full_text[:1000])

with open("filing_text.txt", "w") as out:
    out.write(full_text)

print("\nSaved to filing_text.txt")
