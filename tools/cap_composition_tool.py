import pandas as pd
from langchain_core.tools import tool

scheme_data = pd.read_csv("reference_data/scheme_data.csv")
scheme_cat_asset_cls_df = pd.read_csv("reference_data/scheme_cat_asset_cls.csv")


@tool
def get_asset_class_composition(curr_holdings: list):
    """
    extend curr_holdings by adding scheme category and then asset class

    Args:
        curr_holdings: DataFrame with 'isin' column

    Returns:
        DataFrame with added 'scheme_category' and 'asset_class' columns
    """

    # Create a copy to avoid modifying the original dataframe

    result_df = pd.DataFrame(curr_holdings)

    # Function to match ISIN and get scheme category
    def match_category(row):
        isin = row["isin"]
        # Find matching scheme in scheme_data
        match = scheme_data[
            scheme_data["ISIN Div Payout/ ISIN GrowthISIN Div Reinvestment"].str.contains(
                isin, na=False
            )
        ]

        if not match.empty:
            return match["Scheme Category"].item()
        return None

    # Add scheme category column
    result_df["scheme_category"] = result_df.apply(match_category, axis=1)

    # Merge with asset class mapping
    result_df = result_df.merge(
        scheme_cat_asset_cls_df,
        left_on="scheme_category",
        right_on="scheme_cat",
        how="left",
    )

    # Drop the redundant scheme_cat column from the merge
    if "scheme_cat" in result_df.columns:
        result_df = result_df.drop("scheme_cat", axis=1)

    return result_df


def get_asset_class_summary(curr_holdings: list) -> dict:
    """
    Aggregate holdings by asset class and return summary with market value and percentage

    Args:
        curr_holdings: DataFrame with 'isin', 'market_value' columns and asset class info

    Returns:
        List of dictionaries with asset_class, market_value, and percentage
    """
    # First get the asset class composition
    holdings_with_asset_class = get_asset_class_composition(curr_holdings)

    # Calculate total portfolio value
    total_value = holdings_with_asset_class["market_value"].sum()

    # Group by asset class and aggregate
    asset_class_summary = (
        holdings_with_asset_class.groupby("asset_class").agg({"market_value": "sum"}).reset_index()
    )

    # Calculate percentage of portfolio
    asset_class_summary["percentage"] = (
        asset_class_summary["market_value"] / total_value * 100
    ).round(2)

    # Convert to list of dictionaries
    result = asset_class_summary.to_dict("records")

    return result
