import re

with open("met_filing_text.txt", "r") as f:
    text = f.read()

def find_consolidated_total_assets(text):
    """Skip occurrences where the value is negative (has parentheses) or
    where the number doesn't appear within 50 chars of the label."""
    marker = "Total assets"
    start = 0
    while True:
        idx = text.lower().find(marker.lower(), start)
        if idx == -1:
            break
        # Get 50 chars after label
        snippet = text[idx:idx+50]
        # Skip if negative value (parentheses indicate negative in accounting)
        if "(" in snippet:
            start = idx + 1
            continue
        # Look for large number within 50 chars
        numbers = re.findall(r'[\d,]+', snippet)
        for n in numbers:
            cleaned = n.replace(",", "")
            if cleaned.isdigit() and len(cleaned) >= 6:
                val = int(cleaned)
                if val > 50000:
                    return idx
        start = idx + 1
    return -1

print("Testing improved assets finder:\n")
assets_pos = find_consolidated_total_assets(text)
print(f"Total assets position: {assets_pos:,}")
print(f"  Preview: {text[assets_pos:assets_pos+100].strip()[:80]}")
