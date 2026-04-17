with open("trv_filing_text.txt", "r") as f:
    text = f.read()

import re

# Search for actual revenue numbers — Travelers revenue should be ~45-50B
markers = [
    "Total revenues",
    "Earned premiums",
    "Net earned premiums",
    "Total revenue",
]

print("Searching for income statement numbers:\n")
for marker in markers:
    start = 0
    count = 0
    while count < 5:
        idx = text.lower().find(marker.lower(), start)
        if idx == -1:
            break
        snippet = text[idx:idx+100]
        numbers = re.findall(r'[\d,]+', snippet)
        large = [n for n in numbers if len(n.replace(',','')) >= 4]
        if large:
            print(f"'{marker}' at {idx:,}: {snippet[:80].strip()}")
            print(f"  Numbers: {large[:5]}")
            print()
        start = idx + 1
        count += 1
