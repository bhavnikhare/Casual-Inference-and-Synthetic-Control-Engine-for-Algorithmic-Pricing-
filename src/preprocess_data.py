from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

SALES_FILE = RAW / "sales_train_evaluation.csv"
CALENDAR_FILE = RAW / "calendar.csv"
PRICE_FILE = RAW / "sell_prices.csv"

OUTPUT_FILE = OUT / "cleaned_pricing_data.csv"
DICTIONARY_FILE = OUT / "data_dictionary.xlsx"

# Proposed demonstration design only; this is NOT a real M5 experiment.
TREATMENT_STORE = "CA_1"
INTERVENTION_DATE = pd.Timestamp("2016-04-01")
PRE_START = pd.Timestamp("2016-01-01")
POST_END = pd.Timestamp("2016-06-19")

print("Loading calendar and price lookup tables...")

calendar = pd.read_csv(CALENDAR_FILE)
prices = pd.read_csv(PRICE_FILE)

required_calendar = {"d", "date", "wm_yr_wk"}
required_prices = {"store_id", "item_id", "wm_yr_wk", "sell_price"}

if not required_calendar.issubset(calendar.columns):
    raise ValueError(f"Calendar missing columns: {required_calendar - set(calendar.columns)}")
if not required_prices.issubset(prices.columns):
    raise ValueError(f"Prices missing columns: {required_prices - set(prices.columns)}")

calendar = calendar[["d", "date", "wm_yr_wk"]].copy()
calendar["date"] = pd.to_datetime(calendar["date"], errors="raise")

if calendar["d"].duplicated().any():
    raise ValueError("Calendar contains duplicate day keys.")
if prices.duplicated(["store_id", "item_id", "wm_yr_wk"]).any():
    raise ValueError("Prices contain duplicate store/item/week keys.")

# Read only the sales identifiers to identify the daily columns.
sales_header = pd.read_csv(SALES_FILE, nrows=0).columns.tolist()
id_cols = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
missing_ids = set(id_cols) - set(sales_header)

if missing_ids:
    raise ValueError(f"Sales file missing columns: {missing_ids}")

day_cols = [c for c in sales_header if c.startswith("d_")]
if not day_cols:
    raise ValueError("No daily sales columns (d_*) found.")

calendar_days = set(calendar["d"])
if not set(day_cols).issubset(calendar_days):
    raise ValueError("Some sales day columns are missing from the calendar.")

print(f"Daily columns found: {len(day_cols)}")
print("Aggregating item-level data into store/category/day records...")
print("This may take some time because the source dataset is large.")

keys = ["store_id", "state_id", "cat_id", "date", "wm_yr_wk"]
parts = []
total_input_rows = 0
missing_price_rows = 0
negative_units_rows = 0
chunksize = 250

reader = pd.read_csv(SALES_FILE, chunksize=chunksize)

for number, chunk in enumerate(reader, start=1):
    total_input_rows += len(chunk)

    long_df = chunk.melt(
        id_vars=id_cols,
        value_vars=day_cols,
        var_name="d",
        value_name="units_sold"
    )

    long_df["units_sold"] = pd.to_numeric(
        long_df["units_sold"], errors="coerce"
    )

    if long_df["units_sold"].isna().any():
        raise ValueError("Missing or nonnumeric sales values found.")

    negative_units_rows += int((long_df["units_sold"] < 0).sum())

    long_df = long_df.merge(
        calendar, on="d", how="left", validate="many_to_one"
    )

    long_df = long_df.merge(
        prices,
        on=["store_id", "item_id", "wm_yr_wk"],
        how="left",
        validate="many_to_one"
    )

    missing_price_rows += int(long_df["sell_price"].isna().sum())

    long_df["priced_units"] = long_df["units_sold"].where(
        long_df["sell_price"].notna(), 0
    )
    long_df["revenue_estimate"] = (
        long_df["units_sold"] * long_df["sell_price"]
    ).fillna(0)
    long_df["price_sum"] = long_df["sell_price"].fillna(0)
    long_df["price_count"] = long_df["sell_price"].notna().astype("int64")
    long_df["item_count"] = 1

    part = long_df.groupby(keys, as_index=False, observed=True).agg(
        units_sold=("units_sold", "sum"),
        priced_units=("priced_units", "sum"),
        revenue_estimate=("revenue_estimate", "sum"),
        price_sum=("price_sum", "sum"),
        price_count=("price_count", "sum"),
        item_count=("item_count", "sum")
    )

    parts.append(part)

    if number % 10 == 0:
        print(f"Processed {total_input_rows:,} item/store rows...")

aggregate = pd.concat(parts, ignore_index=True).groupby(
    keys, as_index=False, observed=True
).agg(
    units_sold=("units_sold", "sum"),
    priced_units=("priced_units", "sum"),
    revenue_estimate=("revenue_estimate", "sum"),
    price_sum=("price_sum", "sum"),
    price_count=("price_count", "sum"),
    item_count=("item_count", "sum")
)

if aggregate.empty:
    raise ValueError("No records were generated.")

aggregate["avg_listed_unit_price"] = (
    aggregate["price_sum"] / aggregate["price_count"].replace(0, np.nan)
)
aggregate["price_coverage"] = (
    aggregate["price_count"] / aggregate["item_count"]
)

aggregate["month"] = aggregate["date"].dt.month
aggregate["year"] = aggregate["date"].dt.year
aggregate["quarter"] = aggregate["date"].dt.quarter
aggregate["day_of_week"] = aggregate["date"].dt.day_name()

month = aggregate["date"].dt.month
aggregate["season"] = np.select(
    [
        month.isin([12, 1, 2]),
        month.isin([3, 4, 5]),
        month.isin([6, 7, 8]),
        month.isin([9, 10, 11])
    ],
    ["Winter", "Spring", "Summer", "Autumn"],
    default="Unknown"
)

# Clearly label this as a hypothetical intervention for analysis practice.
aggregate["treatment_group"] = np.where(
    aggregate["store_id"].eq(TREATMENT_STORE),
    "Treatment (simulated)",
    "Control (proposed)"
)

in_window = aggregate["date"].between(PRE_START, POST_END)
aggregate["period"] = np.select(
    [
        in_window & (aggregate["date"] < INTERVENTION_DATE),
        in_window & (aggregate["date"] >= INTERVENTION_DATE)
    ],
    ["Pre", "Post"],
    default="Outside analysis window"
)

aggregate["post_period"] = (
    aggregate["date"].ge(INTERVENTION_DATE)
    & aggregate["date"].le(POST_END)
).astype("int8")

aggregate = aggregate.drop(
    columns=["price_sum", "price_count", "item_count"]
).sort_values(["store_id", "cat_id", "date"])

aggregate.to_csv(OUTPUT_FILE, index=False, date_format="%Y-%m-%d")

# Generate a data dictionary and reproducibility notes.
dictionary_rows = [
    ("store_id", "Store identifier", "Identifier"),
    ("state_id", "State identifier in the US M5 dataset", "Identifier"),
    ("cat_id", "Product category identifier", "Category"),
    ("date", "Calendar date of the observation", "Date"),
    ("wm_yr_wk", "Walmart year-week key", "Calendar"),
    ("units_sold", "Sum of recorded unit sales, including negative returns", "Outcome"),
    ("priced_units", "Units with a matching weekly selling price", "Quality metric"),
    ("revenue_estimate", "Sum of units multiplied by matched weekly selling prices; not audited transaction revenue", "Estimated outcome"),
    ("avg_listed_unit_price", "Unweighted mean of available item selling prices in the store/category/day group", "Price feature"),
    ("price_coverage", "Fraction of item/store/day records with a matched price", "Quality metric"),
    ("month", "Calendar month number", "Feature"),
    ("year", "Calendar year", "Feature"),
    ("quarter", "Calendar quarter number", "Feature"),
    ("day_of_week", "Name of the weekday", "Feature"),
    ("season", "Meteorological-style season using Northern Hemisphere month groupings", "Feature"),
    ("treatment_group", "Hypothetical CA_1 treatment label; all other stores are proposed controls", "Proposed design"),
    ("period", "Pre/post period within the selected analysis window, or outside it", "Proposed design"),
    ("post_period", "1 from 2016-04-01 through 2016-06-19; otherwise 0", "Proposed design")
]

dictionary = pd.DataFrame(
    dictionary_rows, columns=["Column", "Definition", "Type / Notes"]
)

design = pd.DataFrame([
    ("Dataset", "Walmart M5 sales, calendar and weekly selling prices"),
    ("Unit of analysis", "Store × product category × day"),
    ("Proposed treatment store", TREATMENT_STORE),
    ("Proposed comparison stores", "All other stores; suitability must be assessed before causal estimation"),
    ("Proposed intervention date", INTERVENTION_DATE.date().isoformat()),
    ("Pre-period", f"{PRE_START.date()} to {(INTERVENTION_DATE - pd.Timedelta(days=1)).date()}"),
    ("Post-period", f"{INTERVENTION_DATE.date()} to {POST_END.date()}"),
    ("Primary outcome candidate", "revenue_estimate"),
    ("Alternative outcome", "units_sold"),
    ("Important limitation", "The M5 dataset does not document a real pricing intervention. Treatment labels and dates are hypothetical and must not be presented as historical facts."),
    ("Revenue limitation", "Estimated sales value uses unit sales × matched weekly selling price. Negative sales/returns are retained. Missing-price records contribute zero to the estimate, so inspect price_coverage before analysis."),
    ("Outliers", "Negative units may represent returns; they were retained. No observations were automatically removed as outliers."),
    ("Aggregation", "Daily observations are aggregated by store, state, category, date and Walmart week.")
], columns=["Design item", "Definition"])

quality = pd.DataFrame([
    ("Input item/store rows", total_input_rows),
    ("Number of daily columns", len(day_cols)),
    ("Output rows", len(aggregate)),
    ("Output columns", len(aggregate.columns)),
    ("Source sales rows with negative daily unit values", negative_units_rows),
    ("Long-form records without a matching selling price", missing_price_rows),
    ("Output records with missing average listed price", int(aggregate["avg_listed_unit_price"].isna().sum())),
    ("Output records with price coverage below 100%", int((aggregate["price_coverage"] < 1).sum())),
    ("Duplicate output keys", int(aggregate.duplicated(keys).sum())),
], columns=["Check", "Result"])

with pd.ExcelWriter(DICTIONARY_FILE, engine="openpyxl") as writer:
    dictionary.to_excel(writer, sheet_name="Data Dictionary", index=False)
    design.to_excel(writer, sheet_name="Treatment Design", index=False)
    quality.to_excel(writer, sheet_name="Data Quality", index=False)

print("\nPREPROCESSING COMPLETE")
print(f"Cleaned dataset: {OUTPUT_FILE}")
print(f"Data dictionary: {DICTIONARY_FILE}")
print(f"Output shape: {aggregate.shape}")
print(f"Date range: {aggregate['date'].min().date()} to {aggregate['date'].max().date()}")
print(f"Duplicate output keys: {aggregate.duplicated(keys).sum()}")
print(f"Negative sales values were retained: {negative_units_rows:,}")
print("Review price coverage and the hypothetical treatment design before causal analysis.")


