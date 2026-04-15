with open("filing_text.txt", "r") as f:
    text = f.read()

# Search for key financial statement markers
markers = [
    "Total revenues",
    "Net income",
    "Total assets",
    "CONSOLIDATED BALANCE",
    "CONSOLIDATED STATEMENTS OF INCOME",
    "CONSOLIDATED STATEMENTS OF OPERATIONS"
]

print("Searching for financial statement locations...\n")
for marker in markers:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        print(f"Found '{marker}' at position {idx:,}")
        print(f"  Preview: ...{text[idx:idx+200].strip()}...")
        print()
