import anthropic
import json
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

with open("cb_filing_text.txt", "r") as f:
    text = f.read()

npm_pos = text.lower().find("net premiums earned\n5")
chunk = text[npm_pos:npm_pos+18000]

message = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": f"""You are a financial analyst reviewing a 10-K filing.
Extract segment underwriting ratios for all available years.
Look carefully for tables showing loss ratio, expense ratio, and combined ratio
broken down by segment with columns for multiple years (2025, 2024, 2023).

Important: For the consolidated P&C segment, net premiums earned appears at the
very start of this excerpt as a standalone line showing three years of data
(e.g. Net premiums earned 53014 49846 45712). Use these numbers for the
consolidated P&C row net_premiums_earned field.

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
    }]
)

raw = message.content[0].text
print("Claude raw response:")
print(raw[:3000])
