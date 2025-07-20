from datetime import datetime
from io import StringIO

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

    def _merge_curr_holdings_to_txns(self, txns_df, curr_holdings):
        curr_holdings_df = pd.DataFrame(
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "amount": curr_holdings["market_value"],
                "isin": curr_holdings["isin"],
                "scheme": curr_holdings["scheme"],
                "type": "HOLDINGS",
                "description": "Current holdings",
            }
        )
        return pd.concat([txns_df, curr_holdings_df], ignore_index=True)

    def parse(self):
        txns = casparser.read_cas_pdf(self.file_stream, self.password, output="csv")
        txns_df = pd.read_csv(StringIO(str(txns)))
        txns_df["amount"] = txns_df.apply(self._get_cashflow_sign, axis=1)

        # Keep only the specified fields
        required_columns = [
            "amount",
            "date",
            "units",
            "isin",
            "scheme",
            "type",
            "description",
        ]
        available_columns = [col for col in required_columns if col in txns_df.columns]
        txns_df = txns_df[available_columns]

        curr_holdings, past_holdings = self._get_current_and_past_holdings(txns_df)
        txns_df = self._merge_curr_holdings_to_txns(txns_df, curr_holdings)

        return (
            txns_df.to_dict(orient="records"),
            curr_holdings.to_dict(orient="records"),
            past_holdings.to_dict(orient="records"),
        )

    def get_latest_nav(self, isin):
        df = pd.read_csv("./reference_data/navall.csv", delimiter=";", thousands=",")
        nav = df.loc[
            (df["ISIN Div Payout/ ISIN Growth"] == isin)
            | (df["ISIN Div Reinvestment"] == isin),
            "Net Asset Value",
        ].iloc[0]

        return float(nav)
