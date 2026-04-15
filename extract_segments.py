import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

with open("filing_text.txt", "r") as f:
    text = f.read()

chunk = text[432000:448000]

print("Extracting segment ratios with full audit trail...")

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": f"""You are a financial analyst reviewing AIG's 10-K filing.

Extract segment underwriting ratios for 2025, 2024, and 2023.
For each ratio, show the exact source numbers and calculation.

Return ONLY a JSON object in this exact format:
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
      "loss_ratio_calculation": "13968 / 23678 × 100 = 59.0%",
      "acquisition_ratio": number or null,
      "acquisition_ratio_calculation": "4295 / 23678 × 100 = 18.1%",
      "general_operating_expense_ratio": number or null,
      "general_operating_expense_ratio_calculation": "3083 / 23678 × 100 = 13.0%",
      "expense_ratio": number or null,
      "expense_ratio_calculation": "18.1 + 13.0 = 31.1%",
      "combined_ratio": number or null,
      "combined_ratio_calculation": "59.0 + 31.1 = 90.1%"
    }}
  ]
}}

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
    data = json.loads(clean)
    segments = data["segments"]

    print("\n--- AIG Segment Underwriting Ratios with Audit Trail ---")

    current_segment = ""
    for s in segments:
        if s["name"] != current_segment:
            current_segment = s["name"]
            print(f"\n{'='*60}")
            print(f"  {current_segment}")
            print(f"{'='*60}")

        print(f"\n  Year: {s['year']}")
        print(f"  Source numbers:")
        print(f"    Net premiums earned:          ${s['net_premiums_earned']:,}M" if s.get('net_premiums_earned') else "    Net premiums earned:          not found")
        print(f"    Losses and LAE:               ${s['losses_and_lae']:,}M" if s.get('losses_and_lae') else "    Losses and LAE:               not found")
        print(f"    Total acquisition expenses:   ${s['total_acquisition_expenses']:,}M" if s.get('total_acquisition_expenses') else "    Total acquisition expenses:   not found")
        print(f"    General operating expenses:   ${s['general_operating_expenses']:,}M" if s.get('general_operating_expenses') else "    General operating expenses:   not found")

        print(f"  Calculations:")
        print(f"    Loss ratio:                   {s['loss_ratio_calculation']}" if s.get('loss_ratio_calculation') else "    Loss ratio:                   not found")
        print(f"    Acquisition ratio:            {s['acquisition_ratio_calculation']}" if s.get('acquisition_ratio_calculation') else "    Acquisition ratio:            not found")
        print(f"    General operating exp ratio:  {s['general_operating_expense_ratio_calculation']}" if s.get('general_operating_expense_ratio_calculation') else "    General operating exp ratio:  not found")
        print(f"    Expense ratio:                {s['expense_ratio_calculation']}" if s.get('expense_ratio_calculation') else "    Expense ratio:                not found")
        print(f"    Combined ratio:               {s['combined_ratio_calculation']}" if s.get('combined_ratio_calculation') else "    Combined ratio:               not found")

        if s.get('losses_and_lae') and s.get('net_premiums_earned'):
            verified_lr = round(s['losses_and_lae'] / s['net_premiums_earned'] * 100, 1)
            match = "YES" if verified_lr == s.get('loss_ratio') else "NO -- investigate!"
            print(f"  Python verified loss ratio:   {verified_lr}% -- Match: {match}")

    with open("aig_segments.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n{'='*60}")
    print("Saved to aig_segments.json")

except Exception as e:
    print(f"Error: {e}")
    print("Raw response:")
    print(response_text)
