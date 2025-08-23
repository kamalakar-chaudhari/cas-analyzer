from tools.cap_composition_tool import get_asset_class_summary
from tools.filter_transactions_tool import filter_transactions_by_isin
from tools.xirr_tool import get_xirr

tools = [get_xirr, filter_transactions_by_isin, get_asset_class_summary]

tools_ = [
    {
        "type": "function",
        "function": {
            "name": "get_xirr",
            "description": "Calculate the XIRR for a list of mutual fund transactions. Each cashflow must have 'amount' (float) and 'date' (YYYY-MM-DD).",
            "parameters": {
                "type": "object",
                "properties": {
                    "transactions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "amount": {
                                    "type": "number",
                                    "description": "Cashflow amount. Negative for investment, positive for redemption.",
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Cashflow date in YYYY-MM-DD format.",
                                },
                            },
                            "required": ["amount", "date"],
                        },
                        "description": "List of transactions.",
                    }
                },
                "required": ["transactions"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "filter_transactions_by_isin",
            "description": "Filters a list of transactions to only include transactions with the specified ISIN.",
            "parameters": {
                "type": "object",
                "properties": {
                    "transactions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "isin": {
                                    "type": "string",
                                    "description": "ISIN code of the transaction",
                                },
                                "amount": {
                                    "type": "number",
                                    "description": "Transaction amount",
                                },
                                "date": {
                                    "type": "string",
                                    "description": "Date of the transaction in YYYY-MM-DD format",
                                },
                                # Add any other relevant fields as per your data
                            },
                            "required": ["isin"],
                        },
                        "description": "List of cashflow transactions, each with an ISIN and other details",
                    },
                    "isin": {
                        "type": "string",
                        "description": "The ISIN to filter the transactions by",
                    },
                },
                "required": ["transactions", "isin"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_asset_class_summary",
            "description": "Summarizes current holdings by asset class, returning market value and percentage share for each asset class.",
            "parameters": {
                "type": "object",
                "properties": {
                    "curr_holdings": {
                        "type": "array",
                        "description": "List of current holding records, each containing at least 'isin' and 'market_value'.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "isin": {
                                    "type": "string",
                                    "description": "ISIN code of the security",
                                },
                                "market_value": {
                                    "type": "number",
                                    "description": "Market value of the holding",
                                },
                            },
                            "required": ["isin", "market_value"],
                        },
                    }
                },
                "required": ["curr_holdings"],
            },
        },
    },
]
