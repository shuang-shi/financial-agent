with open("cb_filing_text.txt", "r") as f:
    text = f.read()

# Search for the actual number
markers = [
    "272,327",
    "272327",
    "Total assets\n$\n272",
    "Consolidated Balance Sheet",
    "CONSOLIDATED BALANCE SHEET",
]

print("Searching for actual balance sheet number:\n")
for marker in markers:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        print(f"'{marker}' at {idx:,}")
        print(f"  {text[idx:idx+300].strip()[:200]}")
        print()
    else:
        print(f"'{marker}' NOT FOUND\n")
