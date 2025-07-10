tools = [
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
]
