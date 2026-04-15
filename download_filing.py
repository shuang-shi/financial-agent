from sec_edgar_downloader import Downloader

dl = Downloader("YourName", "your@email.com")
dl.get("10-K", "AIG", limit=1)
print("Downloaded! Check: sec-edgar-filings/AIG/10-K/")
