from typing import Dict, List
import pandas as pd


"""
get_cap_composition(holdings) -> [{cap, holding, percentage}]
get_cap_returns(holdings, cap) -> [{scheme, cost, market_value, returns}]


"""


def get_cap_composition(holdings: List[str]) -> Dict[str, float]:
    # Load the CSV
    df = pd.read_csv("data/scheme_data.csv")
    for scheme_holding in holdings:
        matching_rows = df[
            df["ISIN Div Payout/ ISIN GrowthISIN Div Reinvestment"]
            == scheme_holding.get("isin")
        ]
    filtered = df[
        (df["fund_name"] == "Axis Bluechip Fund") & (df["type"] == "Purchase")
    ]
