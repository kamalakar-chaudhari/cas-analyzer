from io import StringIO
from datetime import datetime
import casparser
import pandas as pd


class CasParser:
    def __init__(self, file_stream, password):
        self.file_stream = file_stream
        self.password = password

    def _get_cashflow_sign(self, txn):
        positive_types = [
            "REDEMPTION",
            "DIVIDEND_PAYOUT",
            "SWITCH_OUT",
            "SWITCH_OUT_MERGER",
            "REVERSAL",
        ]

        negative_types = [
            "PURCHASE",
            "PURCHASE_SIP",
            "DIVIDEND_REINVEST",
            "SWITCH_IN",
            "SWITCH_IN_MERGER",
            "STT_TAX",  # only if not already netted in redemption
            "STAMP_DUTY_TAX",
            "TDS_TAX",
        ]

        ignore_types = [
            "SEGREGATION",
            "MISC",
            "UNKNOWN",
        ]

        if txn["type"] in positive_types:
            return abs(txn["amount"])
        elif txn["type"] in negative_types:
            return -abs(txn["amount"])
        elif txn["type"] in ignore_types:
            return 0

    def _get_current_and_past_holdings(self, txns_df):
        grouped_by_schemes = txns_df.groupby("isin", as_index=False).agg(
            {
                "scheme": "first",
                "units": "sum",
                "amount": "sum",
            }
        )

        curr_holdings = grouped_by_schemes[grouped_by_schemes["units"] >= 0.001]
        curr_holdings["latest_nav"] = curr_holdings["isin"].map(self.get_latest_nav)
        curr_holdings["market_value"] = (
            curr_holdings["units"] * curr_holdings["latest_nav"]
        )

        past_holdings = grouped_by_schemes[grouped_by_schemes["units"] < 0.001]
        past_holdings.drop(columns=["units", "amount"], inplace=True)

        return curr_holdings, past_holdings

    def _get_cashflows(self, txns_df, curr_holdings):
        cashflows = txns_df[["date", "amount", "isin", "scheme", "type"]].to_dict(
            orient="records"
        )
        for _, row in curr_holdings.iterrows():
            cashflows.append(
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "amount": row["market_value"],
                    "isin": row["isin"],
                    "scheme": row["scheme"],
                    "type": "HOLDINGS",
                }
            )
        return cashflows

    def parse(self):
        txns = casparser.read_cas_pdf(self.file_stream, self.password, output="csv")
        txns_df = pd.read_csv(StringIO(txns))
        txns_df["amount"] = txns_df.apply(self._get_cashflow_sign, axis=1)

        curr_holdings, past_holdings = self._get_current_and_past_holdings(txns_df)
        cashflows = self._get_cashflows(txns_df, curr_holdings)

        return (
            txns_df.to_dict(orient="records"),
            curr_holdings.to_dict(orient="records"),
            past_holdings.to_dict(orient="records"),
            cashflows,
        )

    def get_latest_nav(self, isin):
        df = pd.read_csv("./data/navall.csv", delimiter=";", thousands=",")
        nav = df.loc[
            (df["ISIN Div Payout/ ISIN Growth"] == isin)
            | (df["ISIN Div Reinvestment"] == isin),
            "Net Asset Value",
        ].iloc[0]

        return float(nav)
