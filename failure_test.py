import requests
import json
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import date
import sys
sys.path.insert(0, '.')
from app import extract_metrics, extract_balance_sheet, extract_segments

load_dotenv()

HEADERS = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}
TICKERS = ["AIG", "PRU", "CB", "MET", "TRV"]

def get_cik(ticker):
    url = f"https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK={ticker}&type=10-K&dateb=&owner=include&count=10&search_text=&action=getcompany&output=atom"
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "xml")
    company = soup.find("company-info")
    if company:
        cik = company.find("cik")
        name = company.find("conformed-name")
        if cik and name:
            return cik.text.strip().zfill(10), name.text.strip()
    return None, None

def get_filing_url(cik_padded):
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    r = requests.get(url, headers=HEADERS)
    data = r.json()
    filings = data["filings"]["recent"]
    for i, form in enumerate(filings["form"]):
        if form == "10-K":
            return filings["accessionNumber"][i], filings["filingDate"][i]
    return None, None

def get_main_document(cik_padded, accession):
    accession_clean = accession.replace("-", "")
    cik_num = str(int(cik_padded))
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{accession_clean}/{accession}-index.htm"
    r = requests.get(index_url, headers=HEADERS)
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
                return f"https://www.sec.gov{href}"
    return None

def extract_text(doc_url):
    r = requests.get(doc_url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

def score_result(metrics):
    required_fields = [
        "revenue", "net_income", "total_assets",
        "total_equity", "eps", "loss_ratio"
    ]
    issues = []
    passed = []
    for field in required_fields:
        val = metrics.get(field)
        if val is None:
            issues.append(f"MISSING: {field}")
        else:
            passed.append(field)
    if metrics.get("losses_and_lae") and metrics.get("revenue"):
        verified = round(metrics["losses_and_lae"] / metrics["revenue"] * 100, 2)
        reported = metrics.get("loss_ratio")
        if reported and abs(verified - reported) > 0.5:
            issues.append(f"MISMATCH: loss_ratio reported {reported}% vs verified {verified}%")
        else:
            passed.append("loss_ratio_verified")
    total = len(required_fields)
    score = len([f for f in passed if f in required_fields])
    pct = round(score / total * 100)
    return {"score": score, "total": total, "pct": pct, "passed": passed, "issues": issues}

print("=" * 60)
print("AI FINANCIAL AGENT — FAILURE ANALYSIS")
print(f"Date: {date.today()}")
print("=" * 60)

results = {}

for ticker in TICKERS:
    print(f"\nTesting {ticker}...")
    try:
        cik, name = get_cik(ticker)
        if not cik:
            results[ticker] = {"error": "CIK not found", "name": ticker}
            continue
        accession, filing_date = get_filing_url(cik)
        if not accession:
            results[ticker] = {"error": "10-K not found", "name": name}
            continue
        doc_url = get_main_document(cik, accession)
        if not doc_url:
            results[ticker] = {"error": "Document not found", "name": name}
            continue
        text = extract_text(doc_url)
        metrics = extract_metrics(text)
        balance = extract_balance_sheet(text)
        for k in ["total_assets", "total_equity"]:
            if not metrics.get(k):
                metrics[k] = balance.get(k)
        score = score_result(metrics)
        results[ticker] = {
            "name": name,
            "filing_date": filing_date,
            "metrics": metrics,
            "score": score
        }
        print(f"  Done: {score['pct']}% ({score['score']}/{score['total']} fields)")
    except Exception as e:
        results[ticker] = {"error": str(e), "name": ticker}
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("RESULTS SUMMARY")
print("=" * 60)

for ticker, result in results.items():
    print(f"\n{ticker} — {result.get('name', 'Unknown')}")
    if "error" in result:
        print(f"  ERROR: {result['error']}")
        continue
    score = result["score"]
    print(f"  Score: {score['pct']}% ({score['score']}/{score['total']} fields)")
    print(f"  Filed: {result['filing_date']}")
    m = result["metrics"]
    print(f"  Revenue:      {m.get('revenue', 'N/A')}")
    print(f"  Net income:   {m.get('net_income', 'N/A')}")
    print(f"  Total assets: {m.get('total_assets', 'N/A')}")
    print(f"  Total equity: {m.get('total_equity', 'N/A')}")
    print(f"  EPS:          {m.get('eps', 'N/A')}")
    print(f"  Loss ratio:   {m.get('loss_ratio', 'N/A')}")
    if score["issues"]:
        print(f"  Issues:")
        for issue in score["issues"]:
            print(f"    - {issue}")

with open("failure_analysis.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved to failure_analysis.json")
