with open("filing_text.txt", "r") as f:
    text = f.read()

# Look at the raw text around the General Insurance table
chunk = text[432000:436000]
print(chunk)
