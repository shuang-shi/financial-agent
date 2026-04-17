# AI Financial Statement Analysis Agent

An end-to-end AI agent that ingests annual 10-K filings from SEC EDGAR, extracts structured financial metrics, verifies every calculation, and generates institutional-quality analyst commentary — delivered as an executive-ready HTML report in under 60 seconds.

Built by Shuang Shi | April 2026

---

## What It Does

Most financial analysts spend 2–4 hours per company manually reading SEC filings, copying numbers into spreadsheets, calculating ratios, and writing commentary. This agent automates the entire workflow.

You type a ticker symbol. The agent:

1. Connects to SEC EDGAR and downloads the latest 10-K filing
2. Locates the financial statements within hundreds of thousands of characters of text
3. Extracts key metrics using Claude (Anthropic's AI)
4. Independently verifies every calculated ratio with Python
5. Assigns a confidence level (HIGH / MEDIUM / LOW) to every extracted field
6. Generates structured analyst commentary with management questions
7. Delivers a formatted executive briefing in your browser

**Tested on:** AIG, Prudential (PRU), Chubb (CB), MetLife (MET), Travelers (TRV)

---

## Project Structure

```
financial-agent/
├── app.py                  # Flask web app — main entry point
├── download_filing.py      # SEC EDGAR filing downloader
├── parse_html.py           # HTML filing parser
├── extract.py              # Top-level metric extraction
├── extract_segments.py     # Segment ratio extraction with audit trail
├── analyze.py              # AI analyst commentary generator
├── generate_report.py      # HTML report generator
├── failure_test.py         # Systematic accuracy testing across 5 companies
├── confidence_test.py      # Confidence scoring unit tests
├── templates/
│   ├── index.html          # Ticker input page
│   └── report.html         # Executive report page
├── .env                    # API keys (not committed)
├── requirements.txt        # Python dependencies
└── README.md
```

---

## How to Run

### Prerequisites
- Python 3.9+
- An Anthropic API key (get one at console.anthropic.com)

### Setup

```bash
# Clone the repo
git clone https://github.com/shuang-shi/financial-agent.git
cd financial-agent

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configure API Key

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=your_api_key_here
```

### Run the App

```bash
python app.py
```

Open your browser and go to `http://localhost:5000`

Enter any insurance company ticker (AIG, PRU, CB, MET, TRV) and click Generate Report.

### Cost

Each report costs approximately $0.05–0.15 in Anthropic API credits. A $5 credit covers 30–100 reports.

---

## Key Product Decisions

### 1. Audit trail over speed
Every calculated ratio shows its source numbers and formula. For example:

```
Loss ratio: 13,968 / 23,678 × 100 = 59.0%
```

An independent Python layer re-computes every ratio and flags discrepancies between the AI output and raw source numbers. This is non-negotiable in regulated financial environments where every number must be traceable.

### 2. Confidence scoring over silent outputs
Every extracted metric is tagged HIGH, MEDIUM, or LOW based on how it was found and whether the value is within the expected range for a major insurer. An AI that communicates its own uncertainty is more valuable than one that silently returns wrong numbers — because silent failures in financial analysis can lead to material decisions based on incorrect data.

### 3. Segment-level ratios over top-line only
A company's consolidated loss ratio can be misleading. This agent extracts segment-level underwriting ratios — breaking down performance by business line across 3 years — giving users a complete picture rather than a headline number that masks segment variation.

### 4. Domain-specific metrics for insurance
The agent extracts insurance-specific metrics: loss ratio, acquisition ratio, general operating expense ratio, combined ratio, and accident year adjusted ratios. These reflect how insurance underwriting performance is actually evaluated — not generic financial KPIs.

### 5. Smart position finding for large documents
10-K filings exceed 950,000 characters. Rather than sending the entire document to the AI, the agent locates the exact position of each financial statement section first, then sends targeted chunks. This reduces cost, improves accuracy, and avoids context window limitations.

---

## Pipeline Architecture

```
Ticker input
     │
     ▼
SEC EDGAR API ──► CIK lookup ──► Filing index ──► Document URL
     │
     ▼
HTML Parser (BeautifulSoup)
     │
     ▼
Position finder ──► Income statement chunk
                ──► Balance sheet chunk
                ──► Segment tables chunk
                ──► EPS chunk
     │
     ▼
Claude API (Anthropic) ──► Structured JSON extraction
     │
     ▼
Python verification layer ──► Ratio cross-check ──► Discrepancy flag
     │
     ▼
Confidence scorer ──► HIGH / MEDIUM / LOW per field
     │
     ▼
Claude API ──► Analyst commentary
     │
     ▼
Flask + HTML ──► Executive briefing with confidence badges
```

---

## Confidence Scoring System

Every extracted metric is assigned a confidence level displayed as a color-coded badge in the report:

| Confidence | Criteria | Display |
|------------|----------|---------|
| HIGH | Label matched exactly, number in expected range, Python verification passed | Green badge |
| MEDIUM | Label matched with fallback candidate, number in expected range | Amber badge |
| LOW | Label not found or number outside expected range | Red badge — requires human review |

**Expected magnitude ranges:**

| Metric | Expected Range |
|--------|---------------|
| Revenue | $1B — $500B |
| Net Income | -$10B — $50B |
| Total Assets | $10B — $2T |
| Total Equity | $1B — $200B |
| EPS | $0 — $100 |
| Loss Ratio | 30% — 120% |

**Core product principle:** In regulated financial environments, an AI that communicates its own uncertainty is more valuable than one that silently returns wrong numbers.

---

## Failure Analysis & Fixes

A systematic accuracy test was run across 5 major insurers to identify failure modes, fix them, and validate the fixes — demonstrating a complete product iteration cycle.

### Final results (after all fixes)

| Company | Type | Score | Revenue | Net Income | Total Assets | Total Equity | EPS | Loss Ratio |
|---------|------|-------|---------|------------|--------------|--------------|-----|------------|
| AIG | P&C | 100% | $26,775M | $3,096M | $161,254M | $41,139M | $5.48 | 52.89% |
| Prudential | Life | 100% | $60,774M | $3,576M | $773,740M | $32,438M | $10.05 | 57.96% |
| Chubb | P&C | 100% | $59,402M | $10,310M | $272,327M | $73,757M | $25.93 | 54.14% |
| MetLife | Life | 100% | $77,084M | $3,173M | $745,166M | $28,398M | $4.74 | 65.21% |
| Travelers | P&C | 100% | $48,828M | $6,288M | $143,708M | $32,894M | $27.83 | 55.74% |

**Overall accuracy: 100% (30/30 fields extracted correctly)**

### Confidence scoring results

| Company | Revenue | Net Income | Total Assets | Total Equity | EPS | Loss Ratio |
|---------|---------|------------|--------------|--------------|-----|------------|
| AIG | HIGH | HIGH | HIGH | HIGH | HIGH | HIGH |
| Prudential | HIGH | HIGH | HIGH | HIGH | HIGH | HIGH |
| Chubb | HIGH | HIGH | HIGH | HIGH | HIGH | HIGH |
| MetLife | HIGH | HIGH | HIGH | HIGH | HIGH | HIGH |
| Travelers | HIGH | HIGH | HIGH | HIGH | HIGH | HIGH |

**30 HIGH, 0 MEDIUM, 0 LOW across 30 fields**

### Key failures fixed

**MetLife — Label Collision (initial score: 50%)**

Root cause: "Total Assets Under Management" appeared before the balance sheet total assets. Fix: Implemented negative-value detection — any "Total assets" occurrence followed by a parenthesis within 50 characters is skipped, since accounting tables use parentheses for negative numbers.

**Travelers — Revenue Label Variation (initial score: 67%)**

Root cause: Improved EPS candidate list and position-finding logic also resolved Travelers' revenue extraction as a side effect.

**Travelers — Unicode Apostrophe (confidence MEDIUM → HIGH)**

Root cause: Travelers uses a Unicode right single quotation mark in "Total shareholders' equity" rather than a standard apostrophe. Fix: Added the Unicode variant to the exact candidates list.

**Key insight:** Domain knowledge directly improves AI reliability. Negative-value detection using parentheses is a financial accounting convention — a generic text parser would miss it, but an analyst familiar with financial statements recognizes it immediately.

---

## Sample Output

### Top-level metrics (AIG 2025)
| Metric | Value | Confidence |
|--------|-------|------------|
| Total Revenue | $26,775M | HIGH |
| Net Income | $3,096M | HIGH |
| Total Assets | $161,254M | HIGH |
| Total Equity | $41,139M | HIGH |
| EPS (Basic) | $5.48 | HIGH |
| Loss Ratio | 52.89% | HIGH |

### Segment underwriting ratios (AIG 2025)
| Segment | Year | Loss Ratio | Expense Ratio | Combined Ratio |
|---------|------|------------|---------------|----------------|
| General Insurance | 2025 | 59.0% | 31.1% | 90.1% |
| General Insurance | 2024 | 59.8% | 32.0% | 91.8% |
| North America Commercial | 2025 | 63.4% | 23.4% | 86.8% |
| North America Commercial | 2024 | 69.9% | 23.4% | 93.3% |
| International Commercial | 2025 | 55.7% | 31.2% | 86.9% |
| Global Personal | 2025 | 57.5% | 41.5% | 99.0% |

---

## Roadmap

### V2 — Scale
- Multi-company comparison dashboard — side-by-side benchmarking across peer insurers
- Automated quarterly monitoring — detect material changes vs. prior period
- Expand failure testing to 20 insurers — target 90%+ accuracy

### V3 — Intelligence
- Natural language Q&A — ask questions about the filing in plain English
- Anomaly detection — flag ratios that deviate significantly from 3-year averages or peer benchmarks
- Segment data support for Travelers and other non-standard P&C filers

---

## About

Built by **Shuang Shi**, a finance and advisory manager with 9+ years of experience at Ernst & Young and KPMG, specializing in financial reporting transformation for large insurance and asset management clients.

This project demonstrates hands-on AI product development capability — combining deep insurance domain expertise with practical LLM engineering skills and rigorous product evaluation methodology.

**Background:** Led cross-functional teams of 30+ on complex financial transformation projects at EY, contributed to S-1 filing and IPO readiness for a leading global insurer, and identified opportunities to automate accounting and reporting workflows — the direct inspiration for this agent.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.14 |
| AI Model | Claude (Anthropic API) |
| Web Framework | Flask |
| HTML Parsing | BeautifulSoup4 |
| Data Source | SEC EDGAR |
| Environment | python-dotenv |

---

## License

MIT License — free to use and modify.
