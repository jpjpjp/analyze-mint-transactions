"""extract_spending_and_income.py

    From an input csv of raw mint transaction data
    extract the transactions relevant to a spending and income analysis.

    Data is read from an input files specified by the PATH_TO_YOUR_TRANSACTIONS
    configuration parameters in expenses_config.py.

    If PATH_TO_NEW_TRANSACTIONS is also specified, the transactions in this file
    will be merged with the exististing data in the PATH_TO_YOUR_TRANSACTIONS
    file.   As part of this merging process the following will take place:
    - If NEW_TRANSACTION_SOURCE is set to "empower" the data will be converted
    from Empower to Mint format
    - If THIRD_PARTY_ACCOUNTS is set, transactions associated from these accounts
    will be extracted and merged with a different transactions file that is
    prepended with the string specified in the THIRD_PARTY_PREFIX parameter

    As part of the merging process new transactions are automatically added to
    file specified by PATH_TO_YOUR_TRANSACTIONS.  Possible duplicates are flagged
    and the user is prompted for how to treat them. In order to avoid permanently
    overwriting existing historical transaction data, today's date is added to
    the updated transactions file.

    Once the new raw data (if any is detected) is aggregate, the transaction
    data is processed. Included in this will be adding groups (logical
    groupings of transaction categoreis) to each transaction,
    removing groups not relevant to a spending or income analysis,
    and adjusting any credits in spending categories so that they appear as
    "refunds", or and adjusting any debits to offset income in a category

    The output of this will be four new CSV files defined in expenses_config.py:
    - OUTPUT_INCOME_DATA is a CSV of the individual transactions
    related to income only
    - OUTPUT_INCOME_BY_SPENDING_BY_GROUP is a CSV of the total annual income
    by spending group for each year represented in the transaction data
    - OUTPUT_SPENDING_DATA is a CSV of the individual transactions
    related to spending only
    - OUTPUT_SPENDING_BY_GROUP is a CSV of the total annual spending
    by spending group for each year represented in the transaction data
"""

# Import necessary modules
import pandas as pd
import numpy as np
import sys
import webbrowser
import os

# Import local helper modules
import extract_spending_data_methods as esd
import read_mint_transaction_data as rmtd
import add_new_transactions as ant

# Import shared configuration file
import expenses_config as ec


def extract_data(
    df, exclude_groups_path, output_data_path, output_by_group_path, is_income
):
    """
    Extracts either spending or income data from the given dataframe,
    and writes the results to disk.

    Parameters:
    df (pandas.DataFrame): The dataframe containing the raw transaction data.
    exclude_groups_path (str): The path to the file containing the list of
                               spending groups to exclude.
    output_data_path (str): The path to the file where the extracted data
                            will be written.
    output_by_group_path (str): The path to the file where the summarized data
                                will be written.
    is_income (bool): True if extracting income data,
                      False if extracting spending data.
    """
    # Set the appropriate function to extract either spending or income data
    if is_income:
        report_path = ec.REPORTS_PATH + "removed-income-transactions.txt"
        extract_func = esd.extract_income
    else:
        report_path = ec.REPORTS_PATH + "removed-transactions.txt"
        extract_func = esd.extract_spending

    # Create an empty dataframe to hold the extracted data
    all_df = pd.DataFrame()

    # Redirect stdout to a file to capture any output from the extract function
    saved_stdout = sys.stdout
    sys.stdout = open(report_path, "w")

    # Iterate through the transaction data a year at a time
    for year in df.index.year.unique():
        # Set the date range for the current year
        from_date = str(year - 1) + "-12-31"
        to_date = str(year + 1) + "-01-01"

        try:
            # Extract the appropriate data for the current year
            year_df = extract_func(df, exclude_groups_path, from_date, to_date)
        except BaseException as e:
            print(f"Failed to extract data for year {year}: {e}")
            sys.exit(-1)

        # Add the extracted data to the running total dataframe
        column_title = str(year) + " Amount"
        if all_df.empty:
            all_df = year_df
            all_df.rename(columns={"Amount": column_title}, inplace=True)
        else:
            year_df.rename(columns={"Amount": column_title}, inplace=True)
            all_df = pd.concat([year_df, all_df])

    # Write the raw extracted data to disk as a csv
    all_df.to_csv(output_data_path)

    # Keep only the columns we will summarize
    all_df.drop(
        columns=[
            "Description",
            "Original Description",
            "Transaction Type",
            "Category",
            "Empower Category",
            "Account Name",
            "Labels",
            "Notes",
        ],
        inplace=True,
        errors="ignore",  # ignore errors in case column does not exist
    )

    # Summarize the data by spending group
    expenses = all_df.groupby(["Spending Group"]).sum()
    expenses.to_csv(output_by_group_path)

    # Show the report in a webbrowser
    sys.stdout.close()
    sys.stdout = saved_stdout
    if is_income:
        print("Done. See analysis of income exclude groups and refunds in window")
    else:
        print("Done. See analysis of spending exclude groups and refunds in window")
    webbrowser.open(
        "file://" + os.path.realpath(report_path), new=2
    )  # new=2: open in a new tab, if possible


def validate_transactions(df, required_columns):
    bad_col = None
    for column in required_columns:
        if column in df.index.names:
            if np.isnan(df.index.get_level_values(column)).any():
                bad_col = column
                break
        else:
            if df[column].isnull().values.any():
                bad_col = column
                break
    if bad_col is None:
        return True
    else:
        print(f"Column {bad_col} is missing data")
        return False


def main():
    # If configured and detected, read the new transaction data and aggregate it
    if hasattr(ec, "PATH_TO_NEW_TRANSACTIONS") and hasattr(
        ec, "NEW_TRANSACTION_SOURCE"
    ):
        if rmtd.new_transactions_available(
            ec.PATH_TO_YOUR_TRANSACTIONS, ec.PATH_TO_NEW_TRANSACTIONS
        ):
            choice = input(
                f"{ec.PATH_TO_NEW_TRANSACTIONS} is newer than "
                f"{ec.PATH_TO_YOUR_TRANSACTIONS}.  "
                "Add new transaction data (y/n)? "
            )
            if choice.lower() == "y":
                df = ant.add_new_and_return_all(
                    ec.PATH_TO_YOUR_TRANSACTIONS, ec.PATH_TO_NEW_TRANSACTIONS
                )
            else:
                df = rmtd.read_mint_transaction_csv(ec.PATH_TO_YOUR_TRANSACTIONS)
        else:
            df = rmtd.read_mint_transaction_csv(ec.PATH_TO_YOUR_TRANSACTIONS)
    else:
        # PATH_TO_YOUR_TRANSACTIONS is the only data we have in mint format
        # If configured split out the 3rd party transaction data
        if hasattr(ec, "THIRD_PARTY_ACCOUNTS") and hasattr(ec, "THIRD_PARTY_PREFIX"):
            df = rmtd.extract_their_accounts_and_get_mine(
                ec.PATH_TO_YOUR_TRANSACTIONS,
                "mint",
                ec.THIRD_PARTY_ACCOUNTS,
                ec.PATH_TO_YOUR_TRANSACTIONS,
                ec.THIRD_PARTY_PREFIX,
            )
        else:
            df = rmtd.read_mint_transaction_csv(ec.PATH_TO_YOUR_TRANSACTIONS)

    # TODO Figure out if the required columns list is legit...
    if not validate_transactions(df, ["Date", "Amount", "Category", "Description"]):
        print(f"Fix {ec.PATH_TO_YOUR_TRANSACTIONS} and try again.")
        sys.exit(-1)

    # Run through the transaction list from mint and add a Spending Group column
    # Set the final parameter to True to get some output about which categories
    # are being assigned to which group
    try:
        df = esd.group_categories(
            df, ec.PATH_TO_SPENDING_GROUPS, show_group_details=False
        )
    except BaseException as e:
        print(f"Failed to group categories: {e}")
        sys.exit(-1)

    # Extract spending data and generate local CSV files for further processing
    extract_data(
        df,
        ec.PATH_TO_GROUPS_TO_EXCLUDE,
        ec.PATH_TO_SPENDING_DATA,
        ec.PATH_TO_SPENDING_BY_GROUP,
        False,
    )

    # Extract income data  and generate local CSV files for further processing
    extract_data(
        df,
        ec.PATH_TO_GROUPS_TO_EXCLUDE_FROM_INCOME,
        ec.OUTPUT_INCOME_DATA,
        ec.OUTPUT_INCOME_BY_SPENDING_BY_GROUP,
        True,
    )


if __name__ == "__main__":
    main()
