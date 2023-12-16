'''
    Read a local csv of transaction data in mint format to a dataframe
'''
import pandas as pd
import datetime
import os

def get_latest_transaction_file(path_to_data, query_user=True):
    # Check if there is a file named transactions-YYYY-MM-DD.csv in the same directory as path_to_data
    dir_name = os.path.dirname(path_to_data)
    file_name = os.path.splitext(os.path.basename(path_to_data))[0] + f'-{datetime.date.today():%Y-%m-%d}.csv'
    file_path = os.path.join(dir_name, file_name)
    if os.path.exists(file_path):
        if query_user:
            # Prompt the user to choose whether to use the existing file or the original file specified by path_to_data
            choice = input(f"A file named {file_name} was found. Would you like to use this file instead of {path_to_data}? (y/n): ")
            if choice.lower() == 'y':
                path_to_data = file_path
        else:
            path_to_data = file_path
        
    return path_to_data

def new_transactions_available(trans, new_trans):
    """
    Returns true if the new transactions data is newer than the
    full transaction data

    Params
    trans - filename of transaction data in mint format
    new_trans - filename with new transactions to add
    """
    trans = get_latest_transaction_file(trans)
    if os.path.getmtime(new_trans) > os.path.getmtime(trans):
        return True
    else:
        return False


def read_mint_transaction_csv(path_to_data, index_on_date=True):

    # Read the raw mint transaction data into a dataframe
    parse_dates = ['Date']
    try:
        df = pd.read_csv(path_to_data, parse_dates=parse_dates)
        df['Amount'] = df['Amount'].astype(float)
        if index_on_date:
            df.set_index(['Date'], inplace=True)
    except BaseException as e:
        # TODO - print a warning and return an empty df?
        # Maybe add a parameter for this
        print('Failed to read mint transaction data: {}'.format(e))
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
