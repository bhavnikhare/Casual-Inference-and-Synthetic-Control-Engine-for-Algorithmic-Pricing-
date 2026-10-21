import pandas as pd
from pathlib import Path

path = Path("data/processed/cleaned_pricing_data.csv")
out_dir = Path("docs")
out_dir.mkdir(exist_ok=True)

df = pd.read_csv(path)

columns = [
    "units_sold",
    "revenue_estimate",
    "avg_listed_unit_price",
]

results = []

for col in columns:
    values = pd.to_numeric(df[col], errors="coerce").dropna()

    if values.empty:
        continue

    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    flagged = values[(values < lower) | (values > upper)]

    results.append({
        "column": col,
        "records_checked": len(values),
        "Q1": q1,
        "Q3": q3,
        "IQR": iqr,
        "lower_fence": lower,
        "upper_fence": upper,
        "flagged_records": len(flagged),
        "flagged_percentage": round(100 * len(flagged) / len(values), 2),
        "minimum": values.min(),
        "maximum": values.max(),
    })

report = pd.DataFrame(results)
report.to_csv(out_dir / "outlier_inspection_report.csv", index=False)

print(report.to_string(index=False))
print("\nReport saved to docs/outlier_inspection_report.csv")
print("No records were removed or modified.")
