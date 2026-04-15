with open("filing_text.txt", "r") as f:
    text = f.read()

# Look at the area around combined ratio and loss ratio mentions
markers = [
    "combined ratio",
    "loss ratio",
    "expense ratio"
]

print("Finding ALL occurrences with context...\n")
for marker in markers:
    start = 0
    count = 0
    while count < 5:  # find first 5 occurrences
        idx = text.lower().find(marker.lower(), start)
        if idx == -1:
            break
        preview = text[idx:idx+200].strip().replace("\n", " ")
        print(f"'{marker}' at {idx:,}: {preview[:150]}")
        start = idx + 1
        count += 1
    print()
