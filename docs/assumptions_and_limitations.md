\# Project Assumptions and Limitations



\*\*Project:\*\* Causal Inference \& Synthetic Control Engine for Algorithmic Pricing



\## 1. Treatment Store and Intervention Date

\- Treatment store: CA\_1

\- Assumed intervention date: April 1, 2016

\- Pre-intervention period: January 1 – March 31, 2016

\- Post-intervention period: April 1 – May 22, 2016



These are hypothetical project assumptions. We have not verified that Walmart actually introduced a pricing change at CA\_1 on this date. The team must clearly define the simulated pricing change before estimating its effect.



\## 2. Outliers in Sales Data

We used the IQR method to identify unusually high or low sales and revenue values. We retained these values because they may represent genuine retail activity. The team should check whether they significantly affect the results.



\## 3. Missing Selling Prices

Estimated revenue was calculated as units sold × selling price. Missing selling prices were replaced with zero during preprocessing, which may underestimate revenue. The team should check the missing-price records and assess their impact.



\## 4. Comparison Stores and Causal Analysis

Synthetic control requires suitable comparison stores whose sales trends closely match CA\_1 before the assumed intervention. The team should check this match and consider other factors, such as holidays, promotions and seasonal demand, that may affect sales.



\## 5. Reliability of Results

The team should perform appropriate robustness and placebo tests to check whether the results remain reliable under alternative assumptions.



\## Conclusion

Dataset preparation is complete. The data is ready for further analysis, but the team must consider these assumptions and limitations before drawing conclusions. Any estimated effect represents the hypothetical project scenario, not proof of an actual historical pricing change.

