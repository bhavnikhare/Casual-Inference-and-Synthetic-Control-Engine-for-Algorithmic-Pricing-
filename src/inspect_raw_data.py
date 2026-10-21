from pathlib import Path
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / "data" / "raw"
REPORT = PROJECT / "docs" / "raw_data_inspection.txt"

FILES = [
    "calendar.csv",
    "sales_train_evaluation.csv",
    "sell_prices.csv",
]

lines = []

for filename in FILES:
    path = RAW / filename
    print(f"\nInspecting: {filename}")

    if not path.exists():
        print(f"ERROR: File not found: {path}")
        continue

    # Read only a small sample to inspect columns and data types.
    sample = pd.read_csv(path, nrows=1000)
    lines.append(f"\n{'=' * 70}\nFILE: {filename}\n{'=' * 70}")
    lines.append(f"Columns: {list(sample.columns)}")
    lines.append(f"Sample shape (first 1000 rows maximum): {sample.shape}")
    lines.append("\nSample data types:\n" + sample.dtypes.to_string())
    lines.append("\nSample missing values:\n" +
                 sample.isna().sum().to_string())
    lines.append("\nSample:\n" + sample.head(5).to_string(index=False))

    # Count rows without loading the full dataset into memory.
    with path.open("rb") as file:
        row_count = sum(1 for _ in file) - 1

    lines.append(f"\nTotal data rows: {row_count}")
    print(f"Total data rows: {row_count}")
    print(f"Columns: {len(sample.columns)}")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text("\n".join(lines), encoding="utf-8")

print(f"\nInspection completed. Report saved to:\n{REPORT}")
print("Raw CSV files were not modified.")
