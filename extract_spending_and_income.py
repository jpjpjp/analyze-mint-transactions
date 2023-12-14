'''extract_spending_and_income.py

   From an input csv of raw mint transaction data
   extract the transactions relevant to a spending and income analysis.
   
   Included in this will be adding groups (logical
   groupings of transaction categoreis) to each transaction,
   removing groups not relevant to a spending or income analysis, 
   and adjusting any credits in spending categories so that they appear as 
   "refunds", or and adjusting any debits to offset income in a category
   
   The output of this will be four new CSV files as specied in expenses_config.py   - OUTPUT_INCOME_DATA is a CSV of the individual transactions
   related to income only
   - OUTPUT_INCOME_BY_SPENDING_BY_GROUP is a CSV of the total annual income
   by spending group for each year represented in the transaction data
   - OUTPUT_SPENDING_DATA is a CSV of the individual transactions
   related to spending only
   - OUTPUT_SPENDING_BY_GROUP is a CSV of the total annual spending
   by spending group for each year represented in the transaction data
'''
# Import necessary modules
import pandas as pd
import sys
import webbrowser
import os

# Import local helper modules
import extract_spending_data_methods as esd
import read_mint_transaction_data as rmtd

# Import shared configuration file
import expenses_config as ec

def extract_data(df, exclude_groups_path, output_data_path, output_by_group_path, is_income):
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
        report_path = ec.REPORTS_PATH+'removed-income-transactions.txt'
        extract_func = esd.extract_income
    else:
        report_path = ec.REPORTS_PATH+'removed-transactions.txt'
        extract_func = esd.extract_spending

    # Create an empty dataframe to hold the extracted data
    all_df = pd.DataFrame()

    # Redirect stdout to a file to capture any output from the extract function
    saved_stdout = sys.stdout
    sys.stdout = open(report_path, 'w')

    # Iterate through the transaction data a year at a time, and extract the appropriate data
    for year in df.index.year.unique():
        # Set the date range for the current year
        from_date = str(year-1) + '-12-31'
        to_date = str(year+1) + '-01-01'

        try:
            # Extract the appropriate data for the current year
            year_df = extract_func(df, exclude_groups_path, from_date, to_date)
        except BaseException as e:
            sys.exit(-1)

        # Add the extracted data to the running total dataframe
        column_title = str(year)+' Amount'
        if all_df.empty:
            all_df = year_df
            all_df.rename(columns={'Amount': column_title}, inplace=True)
        else:
            year_df.rename(columns={'Amount': column_title}, inplace=True)
            all_df = pd.concat([year_df, all_df])

    # Write the raw extracted data to disk as a csv
    all_df.to_csv(output_data_path)

    # Keep only the columns we will summarize
    all_df.drop(columns=['Description', 'Original Description', 'Transaction Type', 'Category', 'Account Name', 'Labels', 'Notes'], inplace=True)

    # Summarize the data by spending group
    expenses = all_df.groupby(['Spending Group']).sum()
    expenses.to_csv(output_by_group_path)

    # Show the report in a webbrowser
    sys.stdout.close()
    sys.stdout = saved_stdout
    print('Done. See analysis of exclude groups and refunds in window')
    webbrowser.open('file://' + os.path.realpath(report_path), new=2) # new=2: open in a new tab, if possible

def main():
    # Read the raw mint transaction data into a dataframe
    df = rmtd.read_mint_transaction_csv(ec.PATH_TO_YOUR_TRANSACTIONS)

    ## Run through the transaction list from mint and add a Spending Group column
    # Set the final parameter to True to get some output about which categories are being assigned to which group
    try:
        df = esd.group_categories(df, ec.PATH_TO_SPENDING_GROUPS, show_group_details=False)
    except BaseException as e:
        sys.exit(-1)

    # Extract spending data
    extract_data(df, ec.PATH_TO_GROUPS_TO_EXCLUDE, ec.PATH_TO_SPENDING_DATA, ec.PATH_TO_SPENDING_BY_GROUP, False)

    # Extract income data
    extract_data(df, ec.PATH_TO_GROUPS_TO_EXCLUDE_FROM_INCOME, ec.OUTPUT_INCOME_DATA, ec.OUTPUT_INCOME_BY_SPENDING_BY_GROUP, True)

if __name__ == '__main__':
    main()