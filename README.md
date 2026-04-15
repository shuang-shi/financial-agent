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
5. Generates structured analyst commentary with management questions
6. Delivers a formatted executive briefing in your browser

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

Open your browser and go to `http://127.0.0.1:5000`

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

### 2. Segment-level ratios over top-line only
A company's consolidated loss ratio can be misleading. This agent extracts segment-level underwriting ratios — breaking down performance by business line across 3 years — giving users a complete picture rather than a headline number that masks segment variation.

### 3. Domain-specific metrics for insurance
The agent extracts insurance-specific metrics: loss ratio, acquisition ratio, general operating expense ratio, combined ratio, and accident year adjusted ratios. These reflect how insurance underwriting performance is actually evaluated — not generic financial KPIs.

### 4. Graceful handling of filing format variation
Different insurers use different labels for the same metrics. AIG calls it "Losses and loss adjustment expenses." Chubb calls it "Losses and loss expenses." Prudential uses "Policyholders' benefits." The agent handles all variations and degrades gracefully when segment data is unavailable (e.g., life insurers that don't report combined ratios).

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
Claude API ──► Analyst commentary
     │
     ▼
Flask + HTML ──► Executive briefing in browser
```

---

## Failure Analysis

A systematic accuracy test was run across 5 major insurers to identify failure modes and inform the confidence scoring system design.

### Results

| Company | Type | Score | Revenue | Net Income | Total Assets | Total Equity | EPS | Loss Ratio |
|---------|------|-------|---------|------------|--------------|--------------|-----|------------|
| AIG | P&C | 100% | $26,775M | $3,096M | $161,254M | $41,162M | $5.48 | 52.89% |
| Prudential | Life | 100% | $60,774M | $3,576M | $773,740M | $32,787M | $10.05 | 57.96% |
| Chubb | P&C | 100% | $59,402M | $10,310M | $272,327M | $79,779M | $25.93 | 54.14% |
| MetLife | Life | 50% | $77,084M | $3,173M | MISSING | MISSING | MISSING | 65.21% |
| Travelers | P&C | 67% | MISSING | $6,242M | $143,708M | $32,894M | $27.83 | MISSING |

**Overall accuracy: 77% (23/30 fields extracted correctly)**

### Failure 1 — MetLife: Label Collision (50% score)

**Root cause:** MetLife uses common financial terms in non-standard contexts earlier in the document. "Total assets" first appears as "Total Assets Under Management (AUM)" — a completely different metric. "Total equity" first appears in an equity securities investment table, not the consolidated balance sheet. The agent takes the first occurrence of each label, which in MetLife's case points to the wrong section.

**Proposed fix:** Extend magnitude-check logic to equity and EPS fields. After finding a label, verify the surrounding number is within the expected range for a major insurer. If not, search for the next occurrence.

### Failure 2 — Travelers: Revenue Label Variation (67% score)

**Root cause:** Travelers does not use "Total revenues" as their primary income statement label. The agent's income statement chunk is anchored to this label — when it is absent, revenue and all revenue-derived metrics (loss ratio) fail together.

**Proposed fix:** Add fallback revenue label candidates: "Total revenue", "Revenues", "Net written premiums", "Net earned premiums". Implement revenue magnitude validation to catch implausibly small extractions.

### Key Insight

All failures stem from the same root cause: label variation across filers. This is not a model intelligence problem — it is a data standardization problem. The agent needs a broader label candidate library and magnitude validation for every field.

---

## Confidence Scoring System (Designed, In Progress)

Rather than displaying extracted metrics without qualification, the agent is being extended to assign a confidence level to each field:

| Confidence | Criteria | Display |
|------------|----------|---------|
| HIGH | Label matched exactly, number in expected range, Python verification passed | Green — safe to use |
| MEDIUM | Label matched with fallback candidate, number in expected range | Amber — use with awareness |
| LOW | Label not found or number outside expected range | Red — requires human review |

**Expected magnitude ranges:**

| Metric | Expected Range |
|--------|---------------|
| Revenue | $1B — $500B |
| Net Income | -$10B — $50B |
| Total Assets | $10B — $2T |
| Total Equity | $1B — $200B |
| EPS | $0 — $100 |
| Loss Ratio | 30% — 120% |

Any value outside these ranges automatically receives LOW confidence and is flagged before displaying to the user.

**Core product principle:** AI tools in regulated financial environments must communicate their own reliability explicitly. Silent failures — where the agent returns a wrong number without flagging it — are more damaging than flagged uncertainties that prompt human review.

---

## Sample Output

### Top-level metrics (AIG 2025)
| Metric | Value |
|--------|-------|
| Total Revenue | $26,775M |
| Net Income | $3,097M |
| Total Assets | $161,254M |
| Total Equity | $41,162M |
| EPS (Basic) | $5.48 |
| Loss Ratio | 52.89% |

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

### V2 — Reliability (next)
- Implement confidence scoring system across all extracted fields
- Fix MetLife label collision using magnitude-check extension
- Fix Travelers revenue label variation using fallback candidates
- Expand failure testing to 20 insurers — target 90%+ accuracy

### V3 — Scale
- Multi-company comparison dashboard — side-by-side benchmarking across peer insurers
- Automated quarterly monitoring — detect material changes vs. prior period

### V4 — Intelligence
- Natural language Q&A — ask questions about the filing in plain English
- Anomaly detection — flag ratios that deviate significantly from 3-year averages or peer benchmarks

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
