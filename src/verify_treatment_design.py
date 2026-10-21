import pandas as pd

path = "data/processed/cleaned_pricing_data.csv"
df = pd.read_csv(path, parse_dates=["date"])

print("DATASET SHAPE:", df.shape)
print("\nDATE RANGE:")
print(df["date"].min(), "to", df["date"].max())

print("\nSTORES PER TREATMENT LABEL:")
print(df.groupby("treatment_group")["store_id"].unique())

print("\nROWS BY TREATMENT AND PERIOD:")
print(pd.crosstab(df["treatment_group"], df["period"]))

print("\nROWS BY POST-PERIOD FLAG:")
print(pd.crosstab(df["treatment_group"], df["post_period"]))

print("\nDUPLICATE STORE-DATE-CATEGORY KEYS:")
print(df.duplicated(["store_id", "date", "cat_id"]).sum())
