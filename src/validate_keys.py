from pathlib import Path
import pandas as pd

project = Path(__file__).resolve().parents[1]
raw = project / "data" / "raw"
out = project / "docs" / "key_validation_report.txt"
report = []

# 1. Calendar date checks
calendar = pd.read_csv(raw / "calendar.csv")
calendar["date"] = pd.to_datetime(calendar["date"], errors="coerce")
report.append("CALENDAR")
report.append(f"Invalid dates: {calendar['date'].isna().sum()}")
report.append(f"Duplicate dates: {calendar['date'].duplicated().sum()}")
report.append(f"Date range: {calendar['date'].min()} to {calendar['date'].max()}")

# 2. Sales identifier and negative-value checks
sales = pd.read_csv(raw / "sales_train_evaluation.csv")
id_cols = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
report.append("\nSALES")
report.append(f"Duplicate full rows: {sales.duplicated().sum()}")
report.append(f"Duplicate id values: {sales['id'].duplicated().sum()}")
report.append(f"Missing identifiers:\n{sales[id_cols].isna().sum().to_string()}")

day_cols = [c for c in sales.columns if c.startswith("d_")]
negative_count = 0
for col in day_cols:
    negative_count += int((sales[col] < 0).sum())
report.append(f"Negative daily sales values: {negative_count}")
report.append(f"Daily columns checked: {len(day_cols)}")

# 3. Price checks and duplicate business keys, in chunks
report.append("\nSELLING PRICES")
price_rows = 0
invalid_prices = 0
zero_prices = 0
duplicate_keys = 0
seen_keys = set()

for chunk in pd.read_csv(raw / "sell_prices.csv", chunksize=100_000):
    price_rows += len(chunk)
    invalid_prices += int((chunk["sell_price"] < 0).sum())
    zero_prices += int((chunk["sell_price"] == 0).sum())

    keys = chunk[["store_id", "item_id", "wm_yr_wk"]]
    duplicate_keys += int(keys.duplicated().sum())

    # Check keys against previous chunks as well.
    for key in keys.itertuples(index=False, name=None):
        if key in seen_keys:
            duplicate_keys += 1
        else:
            seen_keys.add(key)

report.append(f"Rows checked: {price_rows}")
report.append(f"Negative prices: {invalid_prices}")
report.append(f"Zero prices: {zero_prices}")
report.append(f"Duplicate store-item-week keys: {duplicate_keys}")

out.write_text("\n".join(report), encoding="utf-8")
print("\n".join(report))
print(f"\nReport saved to: {out}")
print("Raw files were not modified.")
