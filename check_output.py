with open("filing_text.txt", "r") as f:
    text = f.read()

print(f"Total characters: {len(text):,}")
print(f"Total lines:      {text.count(chr(10)):,}")
print()

terms = ["Revenue", "Net income", "Total assets",
         "Cash and cash equivalents", "Earnings per share"]

print("Key terms found:")
for term in terms:
    found = term.lower() in text.lower()
    status = "YES" if found else "NO "
    print(f"  {status}  {term}")
