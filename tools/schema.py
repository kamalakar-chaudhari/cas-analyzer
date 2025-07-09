tools = [
    {
        "type": "function",
        "function": {
            "name": "get_xirr",
            "description": "Calculate the XIRR for a list of mutual fund cashflows. Each cashflow must have 'amount' (float) and 'date' (YYYY-MM-DD).",
            "parameters": {
                "type": "object",
                "properties": {
                    "cashflows": {
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
                        "description": "List of cashflows.",
                    }
                },
                "required": ["cashflows"],
            },
        },
    }
]
