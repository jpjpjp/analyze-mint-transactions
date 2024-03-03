import pandas as pd
from datetime import datetime, timedelta
import sys
from transactions import read_or_fetch_lm_transactions
from expenses_config import (
    LOOKBACK_TRANSACTION_DAYS,
    LM_FETCHED_TRANSACTIONS_CACHE,
)


def get_latest_good_lm_transactions(existing_df):
    """
    Fetches all transactions from lunchmoney that are newer than
    LOOKBACK_TRANSACTION_DAYS from the most recent transaction in MINT_CSV_FILE

    If there are transactions that have not yet been classified in LunchMoney, exit
    and tell user to finish classifying.

    Once all are classified, remove duplicates that
    are already in MINT_CSV_FILE, and then add the remaining transactions
    to MINT_CSV_FILE in OUPUT_FILES
    """
    new_transactions_df = get_new_lunchmoney_transactions(
        existing_df, LOOKBACK_TRANSACTION_DAYS
    )

    # Exit if there are any transactions that still need to be cleared or categorized
    exit_if_transactions_not_ready(new_transactions_df)

    return lunchmoney_to_mint_format(new_transactions_df)


def normalize_empty_values(values_list):
    # Replace NaN, None, and empty lists with an empty string
    empty = ""
    return [
        (
            empty
            if (isinstance(value, list) and len(value) == 0)
            or pd.isna(value)
            or value is None
            else value
        )
        for value in values_list
    ]


def validate_splits(df):
    parents = df[df["has_children"]]
    for parent_id in parents["id"]:
        if parent_id not in df["parent_id"].values:
            print(f"Parent id {parent_id} does not exist in the dataframe.")
            sys.exit(1)
    print(f"Removing {len(parents)} transactions that were split")
    return df[~df["has_children"]]


def get_new_lunchmoney_transactions(existing_df, lookback_days):
    """
    Fetches new transactions from LunchMoney for the specified date range.
    """
    # Calculate the start date as 7 days before the most recent transaction date
    most_recent_date = existing_df["Date"].max()
    start_date = most_recent_date - timedelta(days=lookback_days)
    end_date = datetime.now().date()  # Set the end date to today

    # Initialize the LunchMoney client

    # Fetch transactions from LunchMoney for the specified date range
    # new_transactions_df = lunchmoney_transactions_to_df(start_date, end_date)
    new_transactions_df = read_or_fetch_lm_transactions(
        start_date, end_date, LM_FETCHED_TRANSACTIONS_CACHE
    )
    print(f"Fetched {len(new_transactions_df)} new transactions from LunchMoney.")

    # For some reason there is often a space before the account name
    # Clean this up until I can figure out why it's happening
    new_transactions_df["account_display_name"] = new_transactions_df[
        "account_display_name"
    ].str.strip()

    # remove any pending transactions
    not_pending_df = new_transactions_df[~new_transactions_df.is_pending]
    num_pending = len(new_transactions_df) - len(not_pending_df)
    print(f"Removing {num_pending} new transactions that are pending.")

    # remove any parents of split transactions
    not_pending_df = validate_splits(not_pending_df)

    return not_pending_df


def exit_if_transactions_not_ready(df):
    """Exits if there are any transactions that still need to be cleared or categorized"""
    unreviewed = df[df.status == "uncleared"]
    if len(unreviewed) > 0:
        print(f"There are {len(unreviewed)} transactions that need to be reviewed.")
        print(
            "Please visit\n"
            "https://my.lunchmoney.app/transactions/2024/02?match=all&status=unreviewed&time=all\n"
            "to classify them, and then rerun this script."
        )
        sys.exit(1)
    uncategorized = df["category_id"].isna().sum()
    if uncategorized:
        print(f"There are {uncategorized} transactions that need to be reviewed.")
        print(
            "Please visit\n"
            "https://my.lunchmoney.app/transactions/2024/02?match=all&time=all&uncategorized=true\n"
            "to classify them, and then rerun this script."
        )
        sys.exit(1)


def lunchmoney_to_mint_format(to_add_df):
    if len(to_add_df) == 0:
        print("No new transactions to add.")
        return to_add_df
    to_add_mint_format = to_add_df[
        [
            "date",
            "payee",
            "amount",
            "category_name",
            "account_display_name",
            "tags",
            "notes",
        ]
    ].rename(
        columns={
            "date": "Date",
            "payee": "Description",
            "amount": "Amount",
            "category_name": "Category",
            "account_display_name": "Account Name",
            "tags": "Labels",
            "notes": "Notes",
        }
    )
    to_add_mint_format.insert(2, "Original Description", "")
    to_add_mint_format.insert(
        4,
        "Transaction Type",
        to_add_mint_format["Amount"].apply(lambda x: "debit" if x > 0 else "credit"),
    )
    to_add_mint_format["Amount"] = to_add_mint_format["Amount"].abs()
    to_add_mint_format["Labels"] = to_add_mint_format["Labels"].apply(
        lambda x: " ".join([tag["name"] for tag in x]) if x else ""
    )

    return to_add_mint_format
