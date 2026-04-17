with open("met_filing_text.txt", "r") as f:
    text = f.read()

import re

# Find ALL occurrences of Total assets and check which has the real balance sheet number
print("All 'Total assets' occurrences:\n")
marker = "Total assets"
start = 0
count = 0
while count < 10:
    idx = text.lower().find(marker.lower(), start)
    if idx == -1:
        break
    preview = text[idx:idx+100].strip()
    numbers = re.findall(r'[\d,]+', preview)
    large = [n for n in numbers if len(n.replace(',','')) >= 6]
    print(f"Position {idx:,}: {preview[:80]}")
    print(f"  Large numbers found: {large[:3]}")
    print()
    start = idx + 1
    count += 1

# Find ALL occurrences of Total equity
print("\nAll 'Total equity' occurrences:\n")
marker = "Total equity"
start = 0
count = 0
while count < 10:
    idx = text.lower().find(marker.lower(), start)
    if idx == -1:
        break
    preview = text[idx:idx+100].strip()
    numbers = re.findall(r'[\d,]+', preview)
    large = [n for n in numbers if len(n.replace(',','')) >= 5]
    print(f"Position {idx:,}: {preview[:80]}")
    print(f"  Large numbers found: {large[:3]}")
    print()
    start = idx + 1
    count += 1

# Find EPS
print("\nAll 'Basic earnings' occurrences:\n")
marker = "Basic earnings"
start = 0
count = 0
while count < 5:
    idx = text.lower().find(marker.lower(), start)
    if idx == -1:
        break
    preview = text[idx:idx+150].strip()
    print(f"Position {idx:,}: {preview[:100]}")
    print()
    start = idx + 1
    count += 1
