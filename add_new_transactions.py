"""
    Program to add newly exported transaction data to an existing local
    csv file of transaction data in mint format
"""
import pandas as pd
import sys

# Local helper modules
import read_mint_transaction_data as rmtd
import get_lunchmoney_transactions as glt
import process_empower_transactions as pet
import expenses_config as ec


def add_row_if_unique(old_df, row, verbose=True):
    """
    Check if a given transaction exists in a dataframe of existing
    transaction data.  If it is completely unique, add it.
    If it is similar to an existing transaction ask the user how to
    process it.

    Params:
        old_df - existing transaction data dataframe
        row - series with one potential new transaction

    Returns:
        an updated or unchanged dataframe of existing transaction data
        a boolean that indicates if a previously existing entry was updated
    """
    did_overwrite = False
    # Find any existing transactions with the same Date, Amount, Account Name,
    # and Transaction Type that are in the new transaction being analyzed
    unique_match = old_df[
        (old_df["Date"] == row["Date"])
        & (old_df["Amount"] == row["Amount"])
        & (old_df["Account Name"] == row["Account Name"])
        & (old_df["Transaction Type"] == row["Transaction Type"])
    ]
    if not unique_match.empty:
        # Row is not unique based on Date, Amount, Account Name & Trans Type
        # Check if Description and Category columns are different
        desc_cat_change = unique_match[
            (unique_match["Description"] != row["Description"])
            | (unique_match["Category"] != row["Category"])
        ]
        if not desc_cat_change.empty:
            # Possible duplicate entry with new Description and/or Category
            print(
                "\nFound a possible duplicate entry with new Description and/or Category."  # noqa
            )
            print(
                "{} {} {} {:.2f}".format(
                    row["Date"].strftime("%Y-%m-%d"),
                    row["Account Name"],
                    row["Transaction Type"],
                    row["Amount"],
                )
            )
            print("Existing Description and Category:")
            print(unique_match.iloc[0][["Description", "Category"]].values)
            print("New Description and Category:")
            print(row[["Description", "Category"]].values)
            response = input("(O)verwrite, (A)dd as new, or (I)gnore?")
            if response.lower() == "o":
                # Update existing transactions with the new info
                old_df.loc[unique_match.index, ["Description", "Category"]] = [
                    row["Description"],
                    row["Category"],
                ]
                did_overwrite = True
            elif response.lower() == "a":
                # Add row as a new transactions to the existing data
                old_df = pd.concat([old_df, row.to_frame().T], ignore_index=True)
            else:
                # Ignore the new transaction's updated info
                return old_df, False
        else:
            # Row already in transaction data, skip it
            return old_df, False
    else:
        # Row is not in existing transaction data, add it
        if verbose:
            print("Found New Transaction:")
            print(
                "{}: {} : {} {} {:.2f}".format(
                    row["Date"].strftime("%Y-%m-%d"),
                    row["Description"],
                    row["Category"],
                    row["Transaction Type"],
                    row["Amount"],
                )
            )
        old_df = pd.concat([old_df, row.to_frame().T], ignore_index=True)

    return old_df, did_overwrite


def add_new_transactions(new_df, old_df, outfile, prefix="", verbose=True):
    # Unindex the dataframes if they were indexed
    if old_df.index.name is not None:
        old_df.reset_index(inplace=True)
    if new_df.index.name is not None:
        new_df.reset_index(inplace=True)

    # Apply add_row_if_unique function to each row in empower_df
    num_overwritten = 0
    orig_len = len(old_df)
    for index, row in new_df.iterrows():
        old_df, did_overwrite = add_row_if_unique(old_df, row)
        if did_overwrite:
            num_overwritten += 1

    if verbose:
        num_added = len(old_df) - orig_len
        print(f"\nAdded {num_added} new transactions")
        if num_overwritten:
            print(f"and updated {num_overwritten} existing transactions")
        print(
            f"{len(new_df) - num_added - num_overwritten} transactions "
            "in the new export already existed in the existing transaction data"
        )

    # Sort and index merged dataframe by descending date
    df = old_df.sort_values(by="Date", ascending=False)
    df.set_index(["Date"], inplace=True)

    # Write updated mint_df to new CSV file
    rmtd.output_new_transaction_data(df, outfile, prefix)
    return df


def add_new_and_return_all(trans, new_trans=None):
    # Get newly exported transaction data
    if ec.NEW_TRANSACTION_SOURCE == "mint":
        new_df = rmtd.read_mint_transaction_csv(new_trans, index_on_date=False)
    elif ec.NEW_TRANSACTION_SOURCE == "empower":
        new_df = pet.empower_to_mint_format(new_trans)
    elif ec.NEW_TRANSACTION_SOURCE == "lunchmoney":
        old_df = rmtd.read_mint_transaction_csv(trans, index_on_date=False)
        new_df = glt.get_latest_good_lm_transactions(old_df)
    else:
        print(
            f"No support for transactions in {ec.NEW_TRANSACTION_SOURCE} format yet."
        )  # noqa
        sys.exit(-1)

    # If configured split the transaction data and add it to the accumulated
    # transaction data for the user and the third party
    if hasattr(ec, "THIRD_PARTY_ACCOUNTS") and hasattr(ec, "THIRD_PARTY_PREFIX"):
        print("Splitting out the transactions for the 3rd party accounts...")
        (my_df, their_df) = rmtd.extract_accounts(new_df, ec.THIRD_PARTY_ACCOUNTS)
        if len(their_df):
            print(
                f"\nProcessing {len(their_df)} new transactions for "
                f"{ec.THIRD_PARTY_PREFIX}..."
            )
            their_old_df = rmtd.read_mint_transaction_csv(
                f"{ec.THIRD_PARTY_PREFIX}-{ec.PATH_TO_YOUR_TRANSACTIONS}",
                index_on_date=False,
            )
            add_new_transactions(
                their_df,
                their_old_df,
                ec.PATH_TO_YOUR_TRANSACTIONS,
                ec.THIRD_PARTY_PREFIX,
            )

        print(f"\n\nProcessing your {len(my_df)} new transactions...")
        old_df = rmtd.read_mint_transaction_csv(trans, index_on_date=False)
        df = add_new_transactions(my_df, old_df, ec.PATH_TO_YOUR_TRANSACTIONS)
    else:
        # Add new or changed transactions to accumulated data
        old_df = rmtd.read_mint_transaction_csv(trans, index_on_date=False)
        df = add_new_transactions(new_df, old_df, ec.PATH_TO_YOUR_TRANSACTIONS)

    return df


if __name__ == "__main__":
    add_new_and_return_all(ec.PATH_TO_YOUR_TRANSACTIONS, ec.PATH_TO_NEW_TRANSACTIONS)
