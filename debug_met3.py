with open("met_filing_text.txt", "r") as f:
    text = f.read()

print("EPS table further:")
print(text[1389745+600:1389745+1200])
