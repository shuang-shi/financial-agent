import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

# Load extracted data
with open("aig_metrics.json", "r") as f:
    metrics = json.load(f)

with open("aig_segments.json", "r") as f:
    segments = json.load(f)

# Build a clean summary to send to Claude
data_summary = f"""
AIG 2025 ANNUAL REPORT - KEY FINANCIAL DATA

TOP-LEVEL METRICS (2025):
- Total Revenue: ${metrics['revenue']:,}M
- Net Income: ${metrics['net_income']:,}M
- Total Assets: ${metrics['total_assets']:,}M
- Total Equity: ${metrics['total_equity']:,}M
- EPS (basic): ${metrics['eps']}
- Overall Loss Ratio: {metrics['loss_ratio']}%

SEGMENT UNDERWRITING RATIOS (3-YEAR TREND):
"""

# Organize segments by name
segment_dict = {}
for s in segments["segments"]:
    name = s["name"]
    if name not in segment_dict:
        segment_dict[name] = []
    segment_dict[name].append(s)

for name, years in segment_dict.items():
    data_summary += f"\n{name}:\n"
    for y in sorted(years, key=lambda x: x["year"]):
        data_summary += f"  {y['year']}: Loss ratio {y['loss_ratio']}% | Expense ratio {y['expense_ratio']}% | Combined ratio {y['combined_ratio']}%\n"

print("Sending to Claude for analysis...")
print(data_summary)

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=2048,
    messages=[
        {
            "role": "user",
            "content": f"""You are a senior insurance industry analyst writing a briefing 
for an investment committee reviewing AIG's 2025 annual performance.

Based on the data below, write a structured analysis covering:

1. EXECUTIVE SUMMARY (3-4 sentences, overall financial health)
2. UNDERWRITING PERFORMANCE (analyze each segment's trend, flag any anomalies)
3. KEY RISKS (identify 2-3 concerns from the data)
4. POSITIVE INDICATORS (identify 2-3 strengths)
5. QUESTIONS FOR MANAGEMENT (3 questions an analyst would ask on an earnings call)

Be specific — reference actual numbers. Write for a financially sophisticated audience.
Flag anything that warrants further investigation.

{data_summary}"""
        }
    ]
)

analysis = message.content[0].text

print("\n" + "="*60)
print("AIG 2025 ANALYST COMMENTARY")
print("="*60)
print(analysis)

with open("aig_analysis.txt", "w") as f:
    f.write("AIG 2025 ANALYST COMMENTARY\n")
    f.write("="*60 + "\n")
    f.write(analysis)

print("\n" + "="*60)
print("Saved to aig_analysis.txt")
