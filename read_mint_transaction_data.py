"""
    Read a local csv of transaction data in mint format to a dataframe
"""
import pandas as pd
import datetime
import os
import shutil
import sys
import process_empower_transactions as pet
import expenses_config as ec


def get_latest_transaction_file(path_to_data, query_user=True):
    # Check if there is a file named transactions-YYYY-MM-DD.csv in the same
    # directory as path_to_data
    dir_name = os.path.dirname(path_to_data)
    file_name = (
        os.path.splitext(os.path.basename(path_to_data))[0]
        + f"-{datetime.date.today():%Y-%m-%d}.csv"
    )
    file_path = os.path.join(dir_name, file_name)
    if os.path.exists(file_path):
        if query_user:
            # Prompt the user to choose whether to use the existing file or the
            # original file specified by path_to_data
            choice = input(
                f"A file named {file_name} was found. Would you like to use "
                "this file instead of {path_to_data}? (y/n): "
            )
            if choice.lower() == "y":
                path_to_data = file_path
        else:
            path_to_data = file_path

    return path_to_data


def extract_accounts(df, acct_list):
    my_accounts = df[~df["Account Name"].isin(acct_list)]
    their_accounts = df[df["Account Name"].isin(acct_list)]

    return (my_accounts, their_accounts)


def get_new_transaction_data(trans, data_format):
    if data_format == "mint":
        df = read_mint_transaction_csv(trans)
    elif data_format == "empower":
        df = pet.empower_to_mint_format(ec.PATH_TO_NEW_TRANSACTIONS)
    else:
        print(f"No support for transactions in {data_format} fromat yet.")
        sys.exit(-1)

    return df


def extract_their_accounts_and_get_mine(
    trans, data_format, account_list, output, prefix=""
):
    df = get_new_transaction_data(trans, data_format)
    (my_df, their_df) = extract_accounts(df, ec.THIRD_PARTY_ACCOUNTS)
    if len(their_df):
        # Write out the 3rd party data
        print(f'Will write ${len(their_df)} transactions to the " \
              "${ec.THIRD_PARTY_PREFIX} transactions file')
        output_new_transaction_data(their_df, output, prefix)
    if len(my_df):
        # Write out a clean version of my transaction data
        print(f'Will write remaining transactions to ${output}')
        output_new_transaction_data(my_df, output)

    return my_df


def output_new_transaction_data(df, outfile, prefix=""):
    if prefix != "":
        outfile = f"{prefix}-{outfile}"
    if os.path.isfile(outfile):
        # Create a temp version of the transactions with today's data
        dir_name = os.path.dirname(outfile)
        file_name = (
            os.path.splitext(os.path.basename(outfile))[0]
            + f"-{datetime.date.today():%Y-%m-%d}.csv"
        )
        outfile = os.path.join(dir_name, file_name)

    df.to_csv(f"{outfile}")


def new_transactions_available(trans, new_trans):
    """
    Returns true if the new transactions data is newer than the
    full transaction data

    Params
    trans - filename of transaction data in mint format
    new_trans - filename with new transactions to add
    """
    trans = get_latest_transaction_file(trans, False)
    if not os.path.isfile(trans):
        print(f'Did not find a ${trans} file.')
        # Edge case - new transactions exist, but historical ones don't yet
        # If configured split the transaction data
        if hasattr(ec, "THIRD_PARTY_ACCOUNTS") and hasattr(ec, "THIRD_PARTY_PREFIX"):
            extract_their_accounts_and_get_mine(
                new_trans,
                ec.NEW_TRANSACTION_SOURCE,
                ec.THIRD_PARTY_ACCOUNTS,
                trans,
                ec.THIRD_PARTY_PREFIX,
            )
        else:
            # New transactions are the only transactions!
            print(f'Will use {new_trans} as the basis for a new local ${trans} file.')
            shutil.copy(new_trans, trans)
        return False
    elif os.path.getmtime(new_trans) > os.path.getmtime(trans):
        return True
    else:
        return False


def read_mint_transaction_csv(path_to_data, index_on_date=True):
    # See if we have an update transaction data file from a previous run today
    path_to_data = get_latest_transaction_file(path_to_data)
    # Read the raw mint transaction data into a dataframe
    parse_dates = ["Date"]
    try:
        df = pd.read_csv(path_to_data, parse_dates=parse_dates)
        df["Amount"] = df["Amount"].astype(float)
        if index_on_date:
            df.set_index(["Date"], inplace=True)
    except BaseException as e:
        # TODO - print a warning and return an empty df?
        # Maybe add a parameter for this
        print("Failed to read mint transaction data: {}".format(e))
        sys.exit(-1)

    return df


# def read_mint_transaction_csv(path_to_data, index_on_date=True):
#     # Read the raw mint transaction data into a dataframe
#     parse_dates = ['Date']
#     try:
#         df = pd.read_csv(path_to_data, parse_dates=parse_dates)
#         df['Amount'] = df['Amount'].astype(float)
#         if index_on_date:
#             df.set_index(['Date'], inplace=True)
#     except BaseException as e:
#         print('Failed to read mint transaction data: {}'.format(e))
#         sys.exit(-1)

#     return df
