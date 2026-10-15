\# M5 Raw Dataset



This folder contains the raw M5 Forecasting dataset used for the Zaalima project: Causal Inference \& Synthetic Control Engine for Algorithmic Pricing.



\## Dataset files



| File | Description |

|---|---|

| `calendar.csv` | Dates, events, and calendar information |

| `sales\_train\_evaluation.csv` | Historical daily sales for products across stores |

| `sell\_prices.csv` | Product selling prices by store and week |



\## Purpose



These files provide historical sales, calendar, and pricing information for exploratory data analysis, sales trends, price-related analysis, and preparation of analytical datasets.



\*\*Important:\*\* The M5 dataset was originally created for retail sales forecasting. It does not directly provide a randomized pricing experiment or competitor pricing data. Causal-inference analyses will require clearly stated assumptions and a suitable treatment definition.



\## Data handling



\- Keep these files unchanged as raw source data.

\- Perform cleaning and transformations in `data/processed/`.

\- Use Git LFS for the large CSV files.

\- Do not overwrite the original raw files.

