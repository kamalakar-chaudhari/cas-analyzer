from datetime import datetime
from typing import List, Dict
import numpy as np
from scipy.optimize import newton


def get_xirr(transactions: List[Dict]) -> float:
    """
    Calculate the XIRR for a list of mutual fund transactions.

    Each cashflow must have:
    - "amount": float (positive for inflows/redemptions, negative for investments)
    - "date": str in "YYYY-MM-DD" format

    Args:
        transactions (List[Dict]): List of dicts with "amount" and "date" keys

    Returns:
        float: XIRR as a decimal (e.g., 0.124 means 12.4%)
    """

    if not transactions or len(transactions) < 2:
        raise ValueError("At least two transactions are required to compute XIRR.")

    # Convert to amounts and datetime objects
    cash_flows = []
    dates = []
    for tx in transactions:
        cash_flows.append(float(tx["amount"]))
        dates.append(datetime.strptime(tx["date"], "%Y-%m-%d"))

    # Use the earliest date as base
    start_date = min(dates)

    # XIRR objective function
    def xnpv(rate: float):
        return sum(
            cf / (1 + rate) ** ((dt - start_date).days / 365)
            for cf, dt in zip(cash_flows, dates)
        )

    # Use Newton-Raphson method to solve for IRR
    try:
        result = newton(func=xnpv, x0=0.1)
    except RuntimeError:
        raise ValueError("XIRR calculation failed to converge.")

    return float(result * 100)
