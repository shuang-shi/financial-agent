import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

with open("filing_text.txt", "r") as f:
    text = f.read()

def extract_chunk(chunk):
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": f"""You are a financial analyst reviewing AIG's 10-K filing.
Extract the following metrics and return ONLY a JSON object with these fields:

- revenue (total revenues in millions, most recent year)
- net_income (in millions, most recent year)
- total_assets (in millions, most recent year)
- total_equity (in millions, most recent year)
- eps (earnings per share, basic, most recent year)
- losses_and_lae (losses and loss adjustment expenses in millions, most recent year)
- loss_ratio_raw (losses_and_lae / revenue × 100, show your calculation as a string e.g. '14162 / 26775 × 100')
- loss_ratio (the result as a percentage, rounded to 2 decimal places)

If a value is not found, use null.

Filing excerpt:
{chunk}"""
            }
        ]
    )
    response_text = message.content[0].text
    clean = response_text.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
        clean = clean.strip()
    try:
        return json.loads(clean)
    except:
        return {}

print("Extracting from income statement...")
income_data = extract_chunk(text[428000:443000])

print("Extracting from balance sheet...")
balance_data = extract_chunk(text[580000:595000])

# Merge results
merged = {}
for key in ["revenue", "net_income", "total_assets", "total_equity", 
            "eps", "losses_and_lae", "loss_ratio_raw", "loss_ratio"]:
    merged[key] = income_data.get(key) or balance_data.get(key)

# Independently verify loss ratio
if merged.get("losses_and_lae") and merged.get("revenue"):
    verified = round(merged["losses_and_lae"] / merged["revenue"] * 100, 2)
else:
    verified = None

print("\n--- AIG 2025 Key Financial Metrics ---")
print(f"  Revenue:          ${merged['revenue']:,}M" if merged['revenue'] else "  Revenue:          not found")
print(f"  Net income:       ${merged['net_income']:,}M" if merged['net_income'] else "  Net income:       not found")
print(f"  Total assets:     ${merged['total_assets']:,}M" if merged['total_assets'] else "  Total assets:     not found")
print(f"  Total equity:     ${merged['total_equity']:,}M" if merged['total_equity'] else "  Total equity:     not found")
print(f"  EPS:              ${merged['eps']}" if merged['eps'] else "  EPS:              not found")

print(f"\n--- Loss Ratio Audit Trail ---")
print(f"  Losses and LAE:   ${merged['losses_and_lae']:,}M" if merged['losses_and_lae'] else "  Losses and LAE:   not found")
print(f"  Calculation:      {merged['loss_ratio_raw']}" if merged['loss_ratio_raw'] else "  Calculation:      not found")
print(f"  Claude's answer:  {merged['loss_ratio']}%" if merged['loss_ratio'] else "  Claude's answer:  not found")
print(f"  Python verified:  {verified}%" if verified else "  Python verified:  could not verify")

if verified and merged.get('loss_ratio'):
    diff = abs(verified - merged['loss_ratio'])
    if diff < 0.1:
        print(f"  Match:            YES (difference: {diff:.2f}%)")
    else:
        print(f"  Match:            NO  (difference: {diff:.2f}%) -- investigate!")

with open("aig_metrics.json", "w") as f:
    json.dump(merged, f, indent=2)
print("\nSaved to aig_metrics.json")
