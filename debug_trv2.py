import requests

HEADERS = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}

url = "https://data.sec.gov/submissions/CIK0000086312.json"
r = requests.get(url, headers=HEADERS)
data = r.json()

filings = data["filings"]["recent"]
print("Searching for 10-K filing:\n")
for i, form in enumerate(filings["form"]):
    if "10-K" in form:
        print(f"  {form} — {filings['filingDate'][i]} — {filings['accessionNumber'][i]}")
        if i > 20:
            break
