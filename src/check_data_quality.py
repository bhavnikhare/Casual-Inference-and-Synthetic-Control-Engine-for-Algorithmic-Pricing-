from pathlib import Path
import pandas as pd

project = Path(__file__).resolve().parents[1]
raw = project / "data" / "raw"
report_path = project / "docs" / "full_data_quality_report.txt"

files = [
    "calendar.csv",
    "sales_train_evaluation.csv",
    "sell_prices.csv",
]

report = []

for filename in files:
    path = raw / filename
    print(f"\nChecking {filename}...")
    total_rows = 0
    missing = None
    duplicate_rows = 0

    for chunk in pd.read_csv(path, chunksize=100_000):
        total_rows += len(chunk)
        chunk_missing = chunk.isna().sum()

        if missing is None:
            missing = chunk_missing
        else:
            missing = missing.add(chunk_missing, fill_value=0)

        duplicate_rows += int(chunk.duplicated().sum())

    report.append(f"\n{'=' * 60}\n{filename}\n{'=' * 60}")
    report.append(f"Total rows: {total_rows}")
    report.append("Full-data missing values:\n" + missing.to_string())
    report.append(f"Duplicates found within individual chunks: {duplicate_rows}")

    print(f"Rows: {total_rows}")
    print("Missing values:")
    print(missing[missing > 0].to_string() or "None")
    print(f"Duplicates found within individual chunks: {duplicate_rows}")

report_path.write_text("\n".join(report), encoding="utf-8")
print(f"\nReport saved to: {report_path}")
print("Raw files were not modified.")
