with open("cb_filing_text.txt", "r") as f:
    text = f.read()

# Find ALL occurrences of Total assets and check which has the right number
marker = "Total assets"
start = 0
print("All 'Total assets' occurrences:\n")
count = 0
while count < 10:
    idx = text.lower().find(marker.lower(), start)
    if idx == -1:
        break
    preview = text[idx:idx+80].strip()
    print(f"Position {idx:,}: {preview[:70]}")
    start = idx + 1
    count += 1
