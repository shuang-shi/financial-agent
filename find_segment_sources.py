with open("filing_text.txt", "r") as f:
    text = f.read()

markers = [
    "Net premiums earned",
    "Losses incurred",
    "North America Commercial",
    "Net premiums written",
    "Underwriting income"
]

print("Searching for segment source numbers...\n")
for marker in markers:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        print(f"Found '{marker}' at position {idx:,}")
        print(f"  Preview: ...{text[idx:idx+300].strip()}...")
        print()
