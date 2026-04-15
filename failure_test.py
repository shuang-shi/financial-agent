import anthropic
import requests
import json
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import date

load_dotenv()
client = anthropic.Anthropic()

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

def find_position(text, marker):
    return text.lower().find(marker.lower())

def find_consolidated_total_assets(text):
    marker = "Total assets"
    start = 0
    while True:
        idx = text.lower().find(marker.lower(), start)
        if idx == -1:
            break
        snippet = text[idx:idx+100]
        numbers = re.findall(r'[\d,]+', snippet)
        for n in numbers:
            try:
                val = int(n.replace(",", ""))
                if val > 50000:
                    return idx
            except:
                pass
        start = idx + 1
    return -1

def call_claude(prompt, max_tokens=2048):
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return raw

def extract_all_metrics(text):
    # Income statement
    pos = find_position(text, "Total revenues")
    chunk = text[max(0, pos-1000):pos+13000]

    eps_candidates = [
        "Basic earnings per share attributable",
        "Basic earnings per share",
        "Basic:\nIncome from continuing",
        "Income from continuing operations",
        "Net income per share",
    ]
    eps_pos = -1
    for marker in eps_candidates:
        eps_pos = find_position(text, marker)
        if eps_pos != -1:
            break
    eps_chunk = text[max(0, eps_pos-500):eps_pos+2000] if eps_pos != -1 else ""

    loss_candidates = [
        "Losses and loss adjustment expenses",
        "Losses and loss expenses",
        "Policyholders' benefits",
        "Benefits and expenses",
        "Policyholder benefits",
    ]
    loss_pos = -1
    for marker in loss_candidates:
        loss_pos = find_position(text, marker)
        if loss_pos != -1:
            break
    loss_chunk = text[max(0, loss_pos-500):loss_pos+3000] if loss_pos != -1 else ""

    # Balance sheet
    assets_pos = find_consolidated_total_assets(text)
    equity_candidates = [
        "shareholders' equity\n$",
        "Total Prudential Financial, Inc. equity",
        "Total stockholders equity",
        "Total AIG shareholders equity",
        "Total equity\n$",
        "Total equity",
    ]
    eq_pos = -1
    for marker in equity_candidates:
        eq_pos = text.lower().find(marker.lower())
        if eq_pos != -1:
            preview = text[eq_pos:eq_pos+100].strip()
            digits = sum(c.isdigit() for c in preview[:50])
            if digits > 3:
                break

    assets_chunk = text[max(0, assets_pos-500):assets_pos+3000] if assets_pos != -1 else ""
    eq_chunk = text[max(0, eq_pos-500):eq_pos+2000] if eq_pos != -1 else ""

    prompt = f"""You are a financial analyst reviewing a 10-K filing from an insurance company.
Extract these metrics and return ONLY a JSON object:
- revenue (total revenues in millions, most recent year)
- net_income (net income attributable to common shareholders in millions, most recent year)
- total_assets (in millions, most recent year, single large consolidated number)
- total_equity (in millions, most recent year)
- eps (earnings per share basic, most recent year)
- losses_and_lae (losses and loss adjustment expenses OR policyholders benefits in millions)
- loss_ratio (losses_and_lae / revenue x 100, rounded to 2 decimals)
- loss_ratio_calculation (show the formula)

Use null if not found.

Income statement:
{chunk}

EPS:
{eps_chunk}

Loss metrics:
{loss_chunk}

Balance sheet:
{assets_chunk}

Equity:
{eq_chunk}"""
    raw = call_claude(prompt)
    try:
        return json.loads(raw)
    except:
        return {}

def score_result(metrics, ticker):
    """Score extraction quality and identify failures."""
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

    # Verify loss ratio calculation
    if metrics.get("losses_and_lae") and metrics.get("revenue"):
        verified = round(metrics["losses_and_lae"] / metrics["revenue"] * 100, 2)
        reported = metrics.get("loss_ratio")
        if reported and abs(verified - reported) > 0.5:
            issues.append(f"MISMATCH: loss_ratio reported {reported}% vs verified {verified}%")
        else:
            passed.append("loss_ratio_verified")

    # Score
    total = len(required_fields)
    score = len([f for f in passed if f in required_fields])
    pct = round(score / total * 100)

    return {
        "score": score,
        "total": total,
        "pct": pct,
        "passed": passed,
        "issues": issues
    }

# Run tests
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
        metrics = extract_all_metrics(text)
        score = score_result(metrics, ticker)

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

# Print summary report
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

# Save results
with open("failure_analysis.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nSaved to failure_analysis.json")
