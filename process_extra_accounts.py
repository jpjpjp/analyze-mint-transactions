'''process_granny_data.py

    Utilities to process transactions from extra accounts

    In my case I monitor my mother's accounts in Mint but don't want her
    transactions included in mine when doing analysis

    Accounts that are listed in the THIRD_PARTY_ACCOUNTS variable in
    expenses_config.py are extracted from the transaction list and added
    to a new transactions file that is prepended with the string set in the
    THIRD_PARTY_PREFIX parameter
'''
import sys
import pandas as pd
import expenses_config as ec
import read_mint_transaction_data as rmtd
import process_empower_transactions as pet

# This is called automatically from the add_new_transactions module
def extract_accounts(df, acct_list):
    my_accounts = df[~df['Account Name'].isin(acct_list)]
    their_accounts = df[df['Account Name'].isin(acct_list)]
    return my_accounts, their_accounts

# Extracting 3rd party accounts can also be done by running this as a standalone
# This is useful for performing an initial extraction on a long running transaction list
def main():
    '''
        Reads configured new transaction data and checks that all transactions
        in accounts belonging to granny are categorized for granny
    '''
    old_df = rmtd.read_mint_transaction_csv(ec.PATH_TO_YOUR_TRANSACTIONS)
    df = pd.DataFrame(old_df['Category'].drop_duplicates())
    df.to_csv("categories.csv")

    if ec.NEW_TRANSACTION_SOURCE == "mint":
        df = rmtd.read_mint_transaction_csv(ec.PATH_TO_NEW_TRANSACTIONS)
    elif ec.NEW_TRANSACTION_SOURCE == "empower":
        df = pet.empower_to_mint_format(ec.PATH_TO_NEW_TRANSACTIONS)
    else:
        print(f"No support for transactions in {ec.NEW_TRANSACTION_SOURCE} fromat yet.")
        sys.exit(-1)

    # I can probably get rid of this
    check_granny_transactions(df)

    # Split the transaction data
    (my_df, their_df) = extract_accounts(df,ec.THIRD_PARTY_ACCOUNTS)

    # Write out the new transaction files
    my_df.to_csv(ec.PATH_TO_NEW_TRANSACTIONS, index=True)
    their_df.to_csv(f"{ec.THIRD_PARTY_PREFIX}-{ec.PATH_TO_NEW_TRANSACTIONS}", index=True)


if __name__ == '__main__':
    main()

