# Test confidence scoring logic before adding to app.py

EXPECTED_RANGES = {
    "revenue":      (1000, 500000),
    "net_income":   (-10000, 50000),
    "total_assets": (10000, 2000000),
    "total_equity": (1000, 200000),
    "eps":          (0, 100),
    "loss_ratio":   (30, 120),
}

def score_confidence(field, value, label_match):
    """
    Returns: HIGH, MEDIUM, or LOW
    label_match: 'exact' | 'fallback' | 'not_found'
    """
    if value is None or label_match == "not_found":
        return "LOW"

    # Check magnitude
    min_val, max_val = EXPECTED_RANGES.get(field, (0, float('inf')))
    in_range = min_val <= abs(value) <= max_val

    if label_match == "exact" and in_range:
        return "HIGH"
    elif label_match == "fallback" and in_range:
        return "MEDIUM"
    else:
        return "LOW"

# Test cases
test_cases = [
    ("revenue", 26775, "exact"),
    ("revenue", 26775, "fallback"),
    ("revenue", None, "not_found"),
    ("revenue", 50, "exact"),        # too small — should be LOW
    ("total_assets", 745166, "exact"),
    ("eps", 4.74, "fallback"),
    ("loss_ratio", 150, "exact"),    # outside range — should be LOW
    ("loss_ratio", 65.21, "exact"),
]

print("Confidence scoring tests:\n")
for field, value, match in test_cases:
    result = score_confidence(field, value, match)
    val_str = str(value) if value is not None else "None"
    print(f"  {field:15} value={val_str:>10} match={match:10} → {result}")
