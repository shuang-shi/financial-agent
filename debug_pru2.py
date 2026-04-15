with open("pru_filing_text.txt", "r") as f:
    text = f.read()

markers = [
    "Total Prudential Financial",
    "Total liabilities and equity",
    "Total stockholders",
    "Basic earnings per share",
    "Income per share",
    "Net income per",
    "Diluted earnings",
    "Total assets\n$",
    "Total assets\n"
]

print("Searching for balance sheet and EPS terms:\n")
for marker in markers:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        print(f"'{marker}' at {idx:,}")
        print(f"  {text[idx:idx+200].strip()[:150]}")
        print()
    else:
        print(f"'{marker}' NOT FOUND\n")
