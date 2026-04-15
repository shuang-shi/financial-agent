from flask import Flask, render_template, request, jsonify
import anthropic
import requests
import json
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import date

load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic()

def get_cik(ticker):
    headers = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}
    # Use SEC EDGAR company search to find CIK from ticker
    search_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&forms=10-K"
    ticker_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK={ticker}&type=10-K&dateb=&owner=include&count=10&search_text=&action=getcompany&output=atom"
    r = requests.get(ticker_url, headers=headers)
    # Parse CIK from the atom feed
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "xml")
    company = soup.find("company-info")
    if company:
        cik = company.find("cik")
        name = company.find("conformed-name")
        if cik and name:
            return cik.text.strip().zfill(10), name.text.strip()
    # Fallback: try direct CIK lookup using ticker search
    search = requests.get(
        f"https://efts.sec.gov/LATEST/search-index?q={ticker}&forms=10-K&hits.hits.total.value=1",
        headers=headers
    )
    try:
        hits = search.json().get("hits", {}).get("hits", [])
        if hits:
            ciks = hits[0].get("_source", {}).get("ciks", [])
            if ciks:
                cik_num = ciks[0].zfill(10)
                detail = requests.get(
                    f"https://data.sec.gov/submissions/CIK{cik_num}.json",
                    headers=headers
                )
                data = detail.json()
                return cik_num, data.get("name", ticker)
    except:
        pass
    return None, None
def get_filing_url(cik_padded):
    headers = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    r = requests.get(url, headers=headers)
    data = r.json()
    filings = data["filings"]["recent"]
    for i, form in enumerate(filings["form"]):
        if form == "10-K":
            accession = filings["accessionNumber"][i]
            filing_date = filings["filingDate"][i]
            return accession, filing_date
    return None, None

def get_main_document(cik_padded, accession):
    headers = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}
    accession_clean = accession.replace("-", "")
    cik_num = str(int(cik_padded))
    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{accession_clean}/{accession}-index.htm"
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
                return f"https://www.sec.gov{href}"
    return None

def extract_text(doc_url):
    headers = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}
    r = requests.get(doc_url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)

def find_position(text, marker):
    return text.lower().find(marker.lower())

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

def extract_metrics(text):
    # Use known good positions for income statement
    pos = find_position(text, "Total revenues")
    chunk = text[max(0, pos-1000):pos+13000]
    
    # Separately grab EPS from balance sheet area
    eps_pos = find_position(text, "Basic:\nIncome from continuing")
    if eps_pos == -1:
        eps_pos = find_position(text, "Income from continuing operations")
    eps_chunk = text[max(0, eps_pos-500):eps_pos+2000]
    
    prompt = f"""You are a financial analyst reviewing a 10-K filing.
Extract these metrics and return ONLY a JSON object:
- revenue (total revenues in millions, most recent year)
- net_income (in millions, most recent year)
- total_assets (in millions, most recent year)
- total_equity (in millions, most recent year)
- eps (earnings per share basic, most recent year, look for "Basic: Income from continuing operations")
- losses_and_lae (losses and loss adjustment expenses in millions)
- loss_ratio (losses_and_lae / revenue × 100)
- loss_ratio_calculation (e.g. "13968 / 23678 × 100 = 59.0%")

Use null if not found.

Income statement excerpt:
{chunk}

EPS excerpt:
{eps_chunk}"""
    raw = call_claude(prompt)
    try:
        return json.loads(raw)
    except:
        return {}
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    ticker = request.json.get("ticker", "").strip().upper()
    if not ticker:
        return jsonify({"error": "Please enter a ticker symbol"}), 400

    try:
        # Step 1: Get CIK
        cik_padded, company_name = get_cik(ticker)
        if not cik_padded:
            return jsonify({"error": f"Could not find company for ticker {ticker}"}), 400

        # Step 2: Get filing
        accession, filing_date = get_filing_url(cik_padded)
        if not accession:
            return jsonify({"error": "Could not find 10-K filing"}), 400

        # Step 3: Get document URL
        doc_url = get_main_document(cik_padded, accession)
        if not doc_url:
            return jsonify({"error": "Could not locate main 10-K document"}), 400

        # Step 4: Extract text
        text = extract_text(doc_url)

        # Step 5: Extract metrics
        metrics = extract_metrics(text)
        balance = extract_balance_sheet(text)
        for k in ["total_assets", "total_equity"]:
            if not metrics.get(k):
                metrics[k] = balance.get(k)

        # Step 6: Extract segments
        segments = extract_segments(text)

        # Step 7: Verify loss ratio
        if metrics.get("losses_and_lae") and metrics.get("revenue"):
            metrics["loss_ratio_verified"] = round(
                metrics["losses_and_lae"] / metrics["revenue"] * 100, 2
            )

        # Step 8: Generate analysis
        analysis = generate_analysis(metrics, segments)

        return jsonify({
            "company_name": company_name,
            "ticker": ticker,
            "filing_date": filing_date,
            "metrics": metrics,
            "segments": segments,
            "analysis": analysis,
            "generated_date": date.today().strftime("%B %d, %Y")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
