with open("cb_filing_text.txt", "r") as f:
    text = f.read()

markers = [
    "Total Chubb",
    "shareholders' equity\n$",
    "Total equity\n",
    "Net premiums earned\n$",
    "Net premiums earned\n5",
    "53,0",
    "Combined ratio\n",
    "P&C combined ratio\n",
]

print("Searching for equity and premiums:\n")
for marker in markers:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        print(f"'{marker}' at {idx:,}")
        print(f"  {text[idx:idx+250].strip()[:200]}")
        print()
    else:
        print(f"'{marker}' NOT FOUND\n")
