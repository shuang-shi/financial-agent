with open("filing_text.txt", "r") as f:
    text = f.read()

markers = [
    "per share",
    "diluted",
    "basic",
    "combined ratio",
]

print("Positions found:\n")
for marker in markers:
    start = 0
    count = 0
    while count < 3:
        idx = text.lower().find(marker.lower(), start)
        if idx == -1:
            break
        print(f"'{marker}' at {idx:,}: {text[idx:idx+120].strip()[:100]}")
        start = idx + 1
        count += 1
    print()
