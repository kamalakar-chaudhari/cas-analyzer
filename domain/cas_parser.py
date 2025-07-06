from io import StringIO
import casparser
import pandas as pd


class CasParser:
    def __init__(self, file_stream, password):
        self.file_stream = file_stream
        self.password = password

    def parse(self):
        txns = casparser.read_cas_pdf(self.file_stream, self.password, output="csv")

        df = pd.read_csv(StringIO(txns))
        grouped_by_schemes = df.groupby("isin", as_index=False).agg(
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

        return (
            curr_holdings.to_dict(orient="records"),
            past_holdings.to_dict(orient="records"),
            df.to_dict(orient="records"),
        )

    def get_latest_nav(self, isin):
        df = pd.read_csv("./data/navall.csv", delimiter=";", thousands=",")
        nav = df.loc[
            (df["ISIN Div Payout/ ISIN Growth"] == isin)
            | (df["ISIN Div Reinvestment"] == isin),
            "Net Asset Value",
        ].iloc[0]

        return float(nav)
