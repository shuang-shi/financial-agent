import requests

url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000005272&type=10-K&dateb=&owner=include&count=1&search_text="

headers = {"User-Agent": "YourName your@email.com"}

response = requests.get(url, headers=headers)

with open("aig_index.html", "w") as f:
    f.write(response.text)

print("Done — saved to aig_index.html")
print(response.text[:500])
