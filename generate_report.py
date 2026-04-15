import json
from datetime import date

with open("aig_metrics.json", "r") as f:
    metrics = json.load(f)

with open("aig_segments.json", "r") as f:
    segments = json.load(f)

with open("aig_analysis.txt", "r") as f:
    analysis = f.read()

# Organize segments by name
segment_dict = {}
for s in segments["segments"]:
    name = s["name"]
    if name not in segment_dict:
        segment_dict[name] = []
    segment_dict[name].append(s)

# Build segment rows
def ratio_color(ratio):
    if ratio is None:
        return "#888"
    if ratio < 90:
        return "#2d6a4f"
    if ratio < 95:
        return "#b5630a"
    return "#a32d2d"

segment_rows = ""
for name, years in segment_dict.items():
    sorted_years = sorted(years, key=lambda x: x["year"])
    for i, y in enumerate(sorted_years):
        cr = y.get("combined_ratio")
        color = ratio_color(cr)
        rowspan = f' rowspan="{len(sorted_years)}"' if i == 0 else ""
        name_cell = f'<td rowspan="{len(sorted_years)}" style="font-weight:500;vertical-align:middle">{name}</td>' if i == 0 else ""
        segment_rows += f"""
        <tr>
            {name_cell}
            <td>{y['year']}</td>
            <td>{y.get('net_premiums_earned', 'N/A'):,}M</td>
            <td>{y.get('loss_ratio', 'N/A')}%</td>
            <td>{y.get('expense_ratio', 'N/A')}%</td>
            <td style="font-weight:500;color:{color}">{y.get('combined_ratio', 'N/A')}%</td>
        </tr>"""

# Convert markdown to basic HTML
def md_to_html(text):
    lines = text.split("\n")
    html = ""
    for line in lines:
        if line.startswith("## "):
            html += f"<h2>{line[3:]}</h2>\n"
        elif line.startswith("### "):
            html += f"<h3>{line[4:]}</h3>\n"
        elif line.startswith("# "):
            html += f"<h1>{line[2:]}</h1>\n"
        elif line.startswith("---"):
            html += "<hr>\n"
        elif line.startswith("**") and line.endswith("**"):
            html += f"<p><strong>{line[2:-2]}</strong></p>\n"
        elif line.strip() == "":
            html += "<br>\n"
        else:
            # Handle inline bold
            line = line.replace("**", "<strong>", 1)
            line = line.replace("**", "</strong>", 1)
            html += f"<p>{line}</p>\n"
    return html

analysis_html = md_to_html(analysis)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>AIG 2025 Financial Analysis</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         max-width: 960px; margin: 0 auto; padding: 40px 24px;
         color: #1a1a1a; line-height: 1.7; }}
  .header {{ border-bottom: 2px solid #1a1a1a; padding-bottom: 16px; margin-bottom: 32px; }}
  .header h1 {{ margin: 0 0 4px; font-size: 24px; }}
  .header p {{ margin: 0; color: #555; font-size: 14px; }}
  .badge {{ display: inline-block; background: #f0f0f0; border-radius: 4px;
            padding: 2px 8px; font-size: 12px; color: #444; margin-left: 8px; }}
  .metrics-grid {{ display: grid; grid-template-columns: repeat(3, 1fr);
                   gap: 16px; margin: 24px 0 32px; }}
  .metric-card {{ background: #f8f8f8; border-radius: 8px; padding: 16px; }}
  .metric-card .label {{ font-size: 12px; color: #666; margin-bottom: 4px; }}
  .metric-card .value {{ font-size: 22px; font-weight: 500; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0 32px; font-size: 14px; }}
  th {{ background: #1a1a1a; color: white; padding: 10px 12px; text-align: left; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
  tr:hover td {{ background: #f8f8f8; }}
  h2 {{ font-size: 18px; font-weight: 500; margin-top: 32px; border-left: 3px solid #1a1a1a;
        padding-left: 12px; }}
  h3 {{ font-size: 15px; font-weight: 500; margin-top: 20px; color: #333; }}
  hr {{ border: none; border-top: 1px solid #eee; margin: 24px 0; }}
  .footer {{ margin-top: 48px; padding-top: 16px; border-top: 1px solid #eee;
             font-size: 12px; color: #888; }}
  .generated {{ background: #f0f7ff; border-left: 3px solid #378add;
                padding: 10px 14px; font-size: 13px; margin-bottom: 24px;
                border-radius: 0 4px 4px 0; }}
</style>
</head>
<body>

<div class="header">
  <h1>AIG 2025 Financial Performance Report
    <span class="badge">AI Generated</span>
  </h1>
  <p>American International Group · Annual Report Analysis · Generated {date.today().strftime("%B %d, %Y")}</p>
</div>

<div class="generated">
  This report was generated automatically by an AI financial analysis agent that ingested 
  AIG's 2025 10-K filing directly from SEC EDGAR, extracted and verified key metrics, 
  and produced structured commentary using Claude.
</div>

<h2>Top-Level Financial Metrics</h2>
<div class="metrics-grid">
  <div class="metric-card">
    <div class="label">Total Revenue</div>
    <div class="value">${metrics['revenue']:,}M</div>
  </div>
  <div class="metric-card">
    <div class="label">Net Income</div>
    <div class="value">${metrics['net_income']:,}M</div>
  </div>
  <div class="metric-card">
    <div class="label">Total Assets</div>
    <div class="value">${metrics['total_assets']:,}M</div>
  </div>
  <div class="metric-card">
    <div class="label">Total Equity</div>
    <div class="value">${metrics['total_equity']:,}M</div>
  </div>
  <div class="metric-card">
    <div class="label">EPS (Basic)</div>
    <div class="value">${metrics['eps']}</div>
  </div>
  <div class="metric-card">
    <div class="label">Overall Loss Ratio</div>
    <div class="value">{metrics['loss_ratio']}%</div>
  </div>
</div>

<h2>Segment Underwriting Ratios (3-Year Trend)</h2>
<table>
  <thead>
    <tr>
      <th>Segment</th>
      <th>Year</th>
      <th>Net Premiums Earned</th>
      <th>Loss Ratio</th>
      <th>Expense Ratio</th>
      <th>Combined Ratio</th>
    </tr>
  </thead>
  <tbody>
    {segment_rows}
  </tbody>
</table>

<h2>Analyst Commentary</h2>
{analysis_html}

<div class="footer">
  Generated by AI Financial Analysis Agent · Source: SEC EDGAR 10-K Filing (2025) · 
  All figures in USD millions unless stated · For internal use only
</div>

</body>
</html>"""

with open("aig_report.html", "w") as f:
    f.write(html)

print("Report saved to aig_report.html")
print("Open it with: open aig_report.html")
