with open("cb_filing_text.txt", "r") as f:
    text = f.read()

import re

# Replicate exact logic from extract_segments in app.py
combined_candidates = [
    "P&C combined ratio",
    "P&C Combined Ratio",
    "combined ratio",
    "Combined ratio",
]
pos = -1
for marker in combined_candidates:
    idx = text.lower().find(marker.lower())
    if idx != -1:
        idx2 = text.lower().find(marker.lower(), idx + 500)
        pos = idx2 if idx2 != -1 else idx
        print(f"Combined ratio found at: {pos:,}")
        break

npm_candidates = [
    "Net premiums earned\n5",
    "Net premiums earned\n4",
    "Net premiums earned\n3",
    "Net premiums earned\n2",
    "Net premiums earned\n$",
    "Net premiums earned",
]
npm_pos = -1
for marker in npm_candidates:
    npm_pos = text.lower().find(marker.lower())
    if npm_pos != -1:
        preview = text[npm_pos:npm_pos+50].strip()
        digits = sum(c.isdigit() for c in preview[:30])
        print(f"NPE marker '{marker}' at {npm_pos:,}")
        print(f"  Preview: {preview[:60]}")
        print(f"  Digits: {digits}, passes check: {digits > 3}")
        if digits > 3:
            break

start = min(pos, npm_pos) if npm_pos != -1 else pos
print(f"\nChunk starts at: {start:,}")
print(f"Chunk ends at: {start+18000:,}")
print(f"\nFirst 500 chars of chunk:")
print(text[max(0, start-2000):start+500])
