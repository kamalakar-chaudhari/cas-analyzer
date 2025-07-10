def filter_transactions_by_isin(transactions, isin):
    """
    Filters the given list of transactions to only include those with the specified ISIN.

    Args:
        transactions (list): List of transaction dicts, each with an "isin" key.
        isin (str): The ISIN to filter by.

    Returns:
        list: Filtered list of transactions with matching ISIN.
    """
    return [txn for txn in transactions if txn.get("isin") == isin]
