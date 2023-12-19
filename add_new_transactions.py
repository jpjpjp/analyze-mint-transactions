'''
    Program to add newly exported transaction data to an existing local
    csv file of transaction data
'''
import pandas as pd
import numpy as np
import datetime
import os

# Local helper modules
import read_mint_transaction_data as rmtd
import process_empower_transactions as pet
import expenses_config as ec

def add_row_if_unique(old_df, row, verbose=True):
    '''
        Check if a given transaction exists in a dataframe of existing
        transaction data.  If it is completely unique, add it.
        If it is similar to an existing transaction ask the user how to 
        process it.

        Params:
            old_df - existing transaction data dataframe
            row - series with one potential new transaction

        Returns:
            an updated or unchanged dataframe of existing transaction data
    '''
    # Check if row is unique based on Date, Amount, Account Name, Transaction Type, Description, and Category
    unique_match = old_df[
        (old_df['Date'] == row['Date']) &
        (old_df['Amount'] == row['Amount']) &
        (old_df['Account Name'] == row['Account Name']) &
        (old_df['Transaction Type'] == row['Transaction Type'])
    ]
    if not unique_match.empty:
        # Row is not unique based on Date, Amount, Account Name, and Transaction Type
        # Check if Description and Category columns are different
        desc_cat_change = unique_match[
            (unique_match['Description'] != row['Description']) |
            (unique_match['Category'] != row['Category'])
        ]
        if not desc_cat_change.empty:
            # Possible duplicate entry with new Description and/or Category
            print("\nFound a possible duplicate entry with new Description and/or Category.")
            print('{} {} {} {:.2f}'.format(row['Date'].strftime('%Y-%m-%d'), row['Account Name'], row['Transaction Type'], row['Amount']))
            print("Existing Description and Category:")
            print(unique_match.iloc[0][['Description', 'Category']].values)
            print("New Description and Category:")
            print(row[['Description', 'Category']].values)
            response = input("(O)verwrite, (A)dd as new, or (I)gnore?")
            if response.lower() == 'o':
                # Update existing row in old_df
                old_df.loc[unique_match.index, ['Description', 'Category']] = [row['Description'], row['Category']]
            elif response.lower() == 'a':
                # Add row from empower_df to old_df
                old_df = pd.concat([old_df, row.to_frame().T], ignore_index=True)
            else:
                # Ignore row from empower_df
                return old_df
        else:
            # Row already in transaction data, skip it
            return old_df
    else:
        # Row is not in existing transaction data, add it
        if verbose:
            print('Found New Transaction:')
            print('{} {} {} {} {:.2f}'.format(row['Date'].strftime('%Y-%m-%d'), row['Description'], row['Category'], row['Transaction Type'], row['Amount']))
        old_df = pd.concat([old_df, row.to_frame().T], ignore_index=True)
    
    return old_df

def add_new_transactions(new_df, old_df, outfile, prefix=""):
    # Unindex the dataframes if they were indexed
    if old_df.index.name is not None:
        old_df.reset_index(inplace=True)
    if new_df.index.name is not None:
        new_df.reset_index(inplace=True)
    
    # Apply add_row_if_unique function to each row in empower_df
    for index, row in new_df.iterrows():
        old_df = add_row_if_unique(old_df,row)
    #old_df = new_df.apply(lambda row: add_row_if_unique(old_df, row), axis=1).iloc[-1]

    # Sort and index merged dataframe by descending date
    df = old_df.sort_values(by='Date', ascending=False)
    df.set_index(['Date'], inplace=True)

    # Write updated mint_df to new CSV file
    rmtd.output_new_transaction_data(df, outfile, prefix)
    return df
 
def add_new_and_return_all(trans, new_trans):
        # Get newly exported transaction data
    if ec.NEW_TRANSACTION_SOURCE == "mint":
        new_df = rmtd.read_mint_transaction_csv(new_trans, index_on_date=False)
    elif ec.NEW_TRANSACTION_SOURCE == "empower":
        new_df = pet.empower_to_mint_format(new_trans)
    else:
        print(f"No support for transactions in {ec.NEW_TRANSACTION_SOURCE} fromat yet.")
        sys.exit(-1)

    # If configured split the transaction data and add it to the accumulated
    # transaction data for the user and the third party
    if hasattr(ec, 'THIRD_PARTY_ACCOUNTS') and hasattr(ec, 'THIRD_PARTY_PREFIX'):
        print('Splitting out the transactions for the 3rd party accounts...')
        (my_df, their_df) = rmtd.extract_accounts(new_df,ec.THIRD_PARTY_ACCOUNTS)
        print(f'\nProcessing {len(their_df)} new transactions for {ec.THIRD_PARTY_PREFIX}...')
        their_old_df = rmtd.read_mint_transaction_csv(f"{ec.THIRD_PARTY_PREFIX}-{ec.PATH_TO_YOUR_TRANSACTIONS}", index_on_date=False)
        add_new_transactions(their_df, their_old_df, ec.PATH_TO_YOUR_TRANSACTIONS, ec.THIRD_PARTY_PREFIX)
        print(f"\n\nProcessing your {len(my_df)} new transactions...")
        old_df = rmtd.read_mint_transaction_csv(trans, index_on_date=False)
        df = add_new_transactions(my_df, old_df, ec.PATH_TO_YOUR_TRANSACTIONS)
    else:
        # Add new or changed transactions to accumulated data
        old_df = rmtd.read_mint_transaction_csv(trans, index_on_date=False)
        df = add_new_transactions(new_df, old_df, ec.PATH_TO_YOUR_TRANSACTIONS)

    return df

if __name__ == '__main__':
    add_new_and_return_all(ec.PATH_TO_NEW_TRANSACTIONS, ec.PATH_TO_NEW_TRANSACTIONS)
