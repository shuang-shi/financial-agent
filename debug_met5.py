with open("met_filing_text.txt", "r") as f:
    text = f.read()

# Find total revenues and policyholder benefits positions
markers = [
    "Total revenues",
    "Policyholder benefits and claims",
    "Benefits and expenses",
]

for marker in markers:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        print(f"'{marker}' at {idx:,}")
        print(f"  {text[idx:idx+200].strip()[:150]}")
        print()
