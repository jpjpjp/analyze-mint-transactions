'''
    Utilities to inspect and manipulate transactions exported by Empower to
    make them work with the tools to analyze mint transaction data
'''
import pandas as pd
import numpy as np
import datetime
import expenses_config as ec

EMPOWER_TRANSACTIONS = "./empower-transactions.csv"
MINT_TRANSACTIONS = "./mint-transactions.csv"

def empower_to_mint_format(empower_transactions):
    '''
        Reads an export of transaction data from Empower, ie:
        https://home.personalcapital.com/page/login/app#/all-transactions
        and returns a dataframe modified to match the format and column
        names used when transaction data is exported from mint
    '''
    parse_dates = ['Date']
    try:
        # Read CSV files into dataframes
        empower_df = pd.read_csv(empower_transactions, parse_dates=parse_dates)

        # Remove empty rows 
        empower_df = empower_df.dropna(how='all')
    except BaseException as e:
        raise ValueError(f'Failed to read Transaction data from {empower_transactions}: {e}')

    # Validate required columns exist
    required_cols = {'Date', 'Account', 'Description', 'Amount', 'Category', 'Tags'}
    if not required_cols.issubset(set(empower_df.columns)):
        raise ValueError("Missing required columns empower transaction data")
    
    # Convert Amount column to float
    empower_df['Amount'] = empower_df['Amount'].astype(float)
    
    # Convert Empower data to Mint format
    empower_df = empower_df.rename(columns={'Account': 'Account Name', 'Tags': 'Labels'})
    empower_df['Transaction Type'] = np.where(empower_df['Amount'] >= 0, 'credit', 'debit')
    empower_df['Amount'] = empower_df['Amount'].abs()

    return empower_df

def compare_csv_files(file1, file2, file3):
    '''
        Find all the values in the "Category" column of file1
        that don't exists in file2 or file3
    '''
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    df3 = pd.read_csv(file3)
    
    # Read in all the values in the Category column of file1
    categories_file1 = set(df1['Category'])
    # Read in all the column names and values from file2 and file3
    categories_file2 = set(df2.columns).union(set(df2.values.flatten()))
    categories_file3 = set(df3.columns).union(set(df3.values.flatten()))
    
    # return a list of categories not in file2 or file3
    categories_not_in_file2_or_file3 = categories_file1 - categories_file2 - categories_file3
    
    return list(categories_not_in_file2_or_file3)

def main():
    # problems = compare_csv_files(EMPOWER_TRANSACTIONS, ec.PATH_TO_SPENDING_GROUPS, ec.PATH_TO_GROUPS_TO_EXCLUDE_FROM_INCOME)
    # print(problems)
    add_empower_transactions(EMPOWER_TRANSACTIONS, MINT_TRANSACTIONS)
if __name__ == '__main__':
    main()
