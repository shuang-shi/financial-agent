from flask import Flask, render_template, request, jsonify
import anthropic
import requests
import json
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import date

load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic()

EXPECTED_RANGES = {
    "revenue":      (1000, 500000),
    "net_income":   (-10000, 50000),
    "total_assets": (10000, 2000000),
    "total_equity": (1000, 200000),
    "eps":          (0, 100),
    "loss_ratio":   (30, 120),
}

def score_confidence(field, value, label_match):
    if value is None or label_match == "not_found":
        return "LOW"
    min_val, max_val = EXPECTED_RANGES.get(field, (0, float('inf')))
    in_range = min_val <= abs(value) <= max_val
    if label_match == "exact" and in_range:
        return "HIGH"
    elif label_match == "fallback" and in_range:
        return "MEDIUM"
    else:
        return "LOW"

def get_cik(ticker):
    headers = {"User-Agent": "Shuang Shi shuangshi@sandiego.edu"}
    ticker_url = f"https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK={ticker}&type=10-K&dateb=&owner=include&count=10&search_text=&action=getcompany&output=atom"
    r = requests.get(ticker_url, headers=headers)
    soup = BeautifulSoup(r.text, "xml")
    company = soup.find("company-info")
    if company:
        cik = company.find("cik")
        name = company.find("conformed-name")
        if cik and name:
            return cik.text.strip().zfill(10), name.text.strip()
    search = requests.get(
        f"https://efts.sec.gov/LATEST/search-index?q={ticker}&forms=10-K",
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

def find_consolidated_total_assets(text):
    marker = "Total assets"
    start = 0
    while True:
        idx = text.lower().find(marker.lower(), start)
        if idx == -1:
            break
        snippet = text[idx:idx+50]
        if "(" in snippet:
            start = idx + 1
            continue
        numbers = re.findall(r'[\d,]+', snippet)
        for n in numbers:
            cleaned = n.replace(",", "")
            if cleaned.isdigit() and len(cleaned) >= 6:
                val = int(cleaned)
                if val > 50000:
                    return idx
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

def extract_metrics(text):
    # Income statement — exact label
    pos = find_position(text, "Total revenues")
    label_match_revenue = "exact" if pos != -1 else "not_found"
    chunk = text[max(0, pos-1000):pos+13000] if pos != -1 else ""

    # EPS — track which label matched
    eps_exact = ["Basic\n$", "Basic earnings per share attributable"]
    eps_fallback = ["Basic earnings per common share", "Basic:\nIncome from continuing",
                    "Income from continuing operations", "Net income per share"]
    eps_pos = -1
    label_match_eps = "not_found"
    for marker in eps_exact:
        eps_pos = find_position(text, marker)
        if eps_pos != -1:
            label_match_eps = "exact"
            break
    if eps_pos == -1:
        for marker in eps_fallback:
            eps_pos = find_position(text, marker)
            if eps_pos != -1:
                label_match_eps = "fallback"
                break
    eps_chunk = text[max(0, eps_pos-500):eps_pos+2000] if eps_pos != -1 else ""

    # Loss metrics
    loss_exact = ["Losses and loss adjustment expenses", "Losses and loss expenses"]
    loss_fallback = ["Policyholders' benefits", "Benefits and expenses", "Policyholder benefits"]
    loss_pos = -1
    label_match_loss = "not_found"
    for marker in loss_exact:
        loss_pos = find_position(text, marker)
        if loss_pos != -1:
            label_match_loss = "exact"
            break
    if loss_pos == -1:
        for marker in loss_fallback:
            loss_pos = find_position(text, marker)
            if loss_pos != -1:
                label_match_loss = "fallback"
                break
    loss_chunk = text[max(0, loss_pos-500):loss_pos+3000] if loss_pos != -1 else ""

    prompt = f"""You are a financial analyst reviewing a 10-K filing from an insurance company.
Extract these metrics and return ONLY a JSON object:
- revenue (total revenues in millions, most recent year)
- net_income (net income attributable to common shareholders in millions, most recent year)
- total_assets (in millions, most recent year)
- total_equity (in millions, most recent year)
- eps (earnings per share basic, most recent year)
- losses_and_lae (losses and loss adjustment expenses OR policyholders benefits in millions, most recent year)
- loss_ratio (losses_and_lae / revenue x 100, rounded to 2 decimals)
- loss_ratio_calculation (show the formula)

Note: This may be a life insurer (policyholders benefits) or P&C insurer (losses and LAE).
Use null if not found.

Income statement excerpt:
{chunk}

EPS excerpt:
{eps_chunk}

Loss metrics excerpt:
{loss_chunk}"""
    raw = call_claude(prompt)
    try:
        metrics = json.loads(raw)
    except:
        metrics = {}

    # Attach confidence scores
    metrics["_confidence"] = {
        "revenue":      score_confidence("revenue", metrics.get("revenue"), label_match_revenue),
        "net_income":   score_confidence("net_income", metrics.get("net_income"), label_match_revenue),
        "eps":          score_confidence("eps", metrics.get("eps"), label_match_eps),
        "loss_ratio":   score_confidence("loss_ratio", metrics.get("loss_ratio"), label_match_loss),
    }
    return metrics

def extract_balance_sheet(text):
    # Total assets
    pos = find_consolidated_total_assets(text)
    label_match_assets = "exact" if pos != -1 else "not_found"

    # Equity
    equity_exact = ["Total equity\n", "Total shareholders\u2019 equity\n", "Total shareholders' equity\n", "shareholders' equity\n$"]
    equity_fallback = ["Total Prudential Financial, Inc. equity", "Total stockholders equity",
                       "Total AIG shareholders equity", "Total equity\n$", "Total equity"]
    eq_pos = -1
    label_match_equity = "not_found"
    for marker in equity_exact:
        eq_pos = text.lower().find(marker.lower())
        if eq_pos != -1:
            preview = text[eq_pos:eq_pos+150].strip()
            numbers = re.findall(r'[\d,]+', preview)
            for n in numbers:
                cleaned = n.replace(",", "")
                if cleaned.isdigit() and len(cleaned) >= 4 and int(cleaned) > 1000:
                    label_match_equity = "exact"
                    break
            if label_match_equity == "exact":
                break
    if eq_pos == -1 or label_match_equity == "not_found":
        for marker in equity_fallback:
            eq_pos = text.lower().find(marker.lower())
            if eq_pos != -1:
                preview = text[eq_pos:eq_pos+150].strip()
                numbers = re.findall(r'[\d,]+', preview)
                for n in numbers:
                    cleaned = n.replace(",", "")
                    if cleaned.isdigit() and len(cleaned) >= 4 and int(cleaned) > 1000:
                        label_match_equity = "fallback"
                        break
                if label_match_equity == "fallback":
                    break

    chunk = text[max(0, pos-500):pos+3000] if pos != -1 else ""
    eq_chunk = text[max(0, eq_pos-500):eq_pos+2000] if eq_pos != -1 else ""

    prompt = f"""Extract from this 10-K filing and return ONLY a JSON object:
- total_assets (in millions, most recent year, single large consolidated number)
- total_equity (in millions, most recent year, equity attributable to common shareholders)

Use null if not found.

Assets excerpt:
{chunk}

Equity excerpt:
{eq_chunk}"""
    raw = call_claude(prompt)
    try:
        result = json.loads(raw)
    except:
        result = {}

    result["_confidence"] = {
        "total_assets": score_confidence("total_assets", result.get("total_assets"), label_match_assets),
        "total_equity": score_confidence("total_equity", result.get("total_equity"), label_match_equity),
    }
    return result

def extract_segments(text):
    combined_candidates = [
        "P&C combined ratio", "P&C Combined Ratio",
        "combined ratio", "Combined ratio",
    ]
    pos = -1
    for marker in combined_candidates:
        idx = text.lower().find(marker.lower())
        if idx != -1:
            idx2 = text.lower().find(marker.lower(), idx + 500)
            pos = idx2 if idx2 != -1 else idx
            break

    if pos == -1:
        pos = find_position(text, "segment income")
        if pos == -1:
            pos = find_position(text, "adjusted operating income")
        if pos == -1:
            return {"segments": []}

    npm_candidates = [
        "Net premiums earned\n5", "Net premiums earned\n4",
        "Net premiums earned\n3", "Net premiums earned\n2",
        "Net premiums earned\n$", "Net premiums earned",
    ]
    npm_pos = -1
    for marker in npm_candidates:
        npm_pos = find_position(text, marker)
        if npm_pos != -1:
            preview = text[npm_pos:npm_pos+50].strip()
            digits = sum(c.isdigit() for c in preview[:30])
            if digits > 3:
                break

    start = npm_pos if npm_pos != -1 else pos
    chunk = text[start:start+18000]

    prompt = f"""You are a financial analyst reviewing a 10-K filing.
Extract segment underwriting ratios for all available years.
Look carefully for tables showing loss ratio, expense ratio, and combined ratio
broken down by segment with columns for multiple years (2025, 2024, 2023).
Also extract net premiums earned per segment per year where available.
For the consolidated P&C segment, net premiums earned appears at the very start
of this excerpt as a standalone line showing three years of data.
Use these numbers for the consolidated P&C row net_premiums_earned field.

Return ONLY a JSON object:
{{
  "segments": [
    {{
      "name": "segment name",
      "year": 2025,
      "net_premiums_earned": number or null,
      "losses_and_lae": number or null,
      "total_acquisition_expenses": number or null,
      "general_operating_expenses": number or null,
      "loss_ratio": number or null,
      "loss_ratio_calculation": "X / Y x 100 = Z%",
      "acquisition_ratio": number or null,
      "expense_ratio": number or null,
      "expense_ratio_calculation": "A + B = C%",
      "combined_ratio": number or null,
      "combined_ratio_calculation": "X + Y = Z%"
    }}
  ]
}}

If no segment ratio data found return segments as empty array.

Filing excerpt:
{chunk}"""
    raw = call_claude(prompt, max_tokens=4096)
    try:
        return json.loads(raw)
    except:
        return {"segments": []}

def generate_analysis(metrics, segments):
    segment_summary = ""
    seg_dict = {}
    for s in segments.get("segments", []):
        name = s["name"]
        if name not in seg_dict:
            seg_dict[name] = []
        seg_dict[name].append(s)
    for name, years in seg_dict.items():
        segment_summary += f"\n{name}:\n"
        for y in sorted(years, key=lambda x: x["year"]):
            segment_summary += f"  {y['year']}: Loss ratio {y.get('loss_ratio','N/A')}% | Expense ratio {y.get('expense_ratio','N/A')}% | Combined ratio {y.get('combined_ratio','N/A')}%\n"

    prompt = f"""You are a senior insurance industry analyst writing a briefing for an investment committee.

Based on this data, write a structured analysis with these sections:
1. EXECUTIVE SUMMARY (3-4 sentences)
2. UNDERWRITING PERFORMANCE (analyze each segment trend, flag anomalies)
3. KEY RISKS (2-3 concerns)
4. POSITIVE INDICATORS (2-3 strengths)
5. QUESTIONS FOR MANAGEMENT (3 questions)

Be specific - reference actual numbers. Flag anything warranting investigation.
If this is a life insurer, focus on policyholder benefits ratio and segment profitability
instead of combined ratios.

TOP-LEVEL METRICS:
- Revenue: ${metrics.get('revenue','N/A')}M
- Net Income: ${metrics.get('net_income','N/A')}M
- Total Assets: ${metrics.get('total_assets','N/A')}M
- Total Equity: ${metrics.get('total_equity','N/A')}M
- EPS: ${metrics.get('eps','N/A')}
- Loss Ratio: {metrics.get('loss_ratio','N/A')}%

SEGMENT RATIOS:
{segment_summary if segment_summary else 'Segment data not available'}"""

    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text

@app.route("/report")
def report():
    return render_template("report.html")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    ticker = request.json.get("ticker", "").strip().upper()
    if not ticker:
        return jsonify({"error": "Please enter a ticker symbol"}), 400
    try:
        cik_padded, company_name = get_cik(ticker)
        if not cik_padded:
            return jsonify({"error": f"Could not find company for ticker {ticker}"}), 400
        accession, filing_date = get_filing_url(cik_padded)
        if not accession:
            return jsonify({"error": "Could not find 10-K filing"}), 400
        doc_url = get_main_document(cik_padded, accession)
        if not doc_url:
            return jsonify({"error": "Could not locate main 10-K document"}), 400
        text = extract_text(doc_url)
        metrics = extract_metrics(text)
        balance = extract_balance_sheet(text)
        for k in ["total_assets", "total_equity"]:
            if not metrics.get(k):
                metrics[k] = balance.get(k)
        # Merge confidence scores
        if "_confidence" not in metrics:
            metrics["_confidence"] = {}
        metrics["_confidence"].update(balance.get("_confidence", {}))
        segments = extract_segments(text)
        if metrics.get("losses_and_lae") and metrics.get("revenue"):
            metrics["loss_ratio_verified"] = round(
                metrics["losses_and_lae"] / metrics["revenue"] * 100, 2
            )
            # Upgrade loss ratio confidence if Python verification passes
            reported = metrics.get("loss_ratio")
            if reported and abs(metrics["loss_ratio_verified"] - reported) < 0.1:
                if metrics["_confidence"].get("loss_ratio") != "LOW":
                    metrics["_confidence"]["loss_ratio"] = "HIGH"
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
