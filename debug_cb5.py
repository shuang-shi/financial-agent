with open("cb_filing_text.txt", "r") as f:
    text = f.read()

# Test the exact same logic as extract_balance_sheet in app.py
asset_candidates = [
    "Total assets\n$\n",
    "Total assets\n$",
    "Total assets\n",
    "Total assets",
]

print("Testing asset candidates:\n")
for marker in asset_candidates:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        preview = text[idx:idx+100].strip()
        digits = sum(c.isdigit() for c in preview[:50])
        print(f"'{marker}' at {idx:,}")
        print(f"  Preview: {preview[:80]}")
        print(f"  Digits in first 50 chars: {digits}")
        print(f"  Would pass check (digits > 3): {digits > 3}")
        print()
    else:
        print(f"'{marker}' NOT FOUND\n")

print("\nTesting equity candidates:\n")
equity_candidates = [
    "shareholders' equity\n$",
    "Total Prudential Financial, Inc. equity",
    "Total stockholders equity",
    "Total AIG shareholders equity",
    "Total equity\n$",
    "Total equity",
]
for marker in equity_candidates:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        preview = text[idx:idx+100].strip()
        digits = sum(c.isdigit() for c in preview[:50])
        print(f"'{marker}' at {idx:,}")
        print(f"  Preview: {preview[:80]}")
        print(f"  Digits in first 50 chars: {digits}")
        print(f"  Would pass check (digits > 3): {digits > 3}")
        print()
    else:
        print(f"'{marker}' NOT FOUND\n")
