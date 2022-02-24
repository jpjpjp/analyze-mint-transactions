# get_spending_data_as_csv.py
'''From an input csv of raw mint transaction data
   extract the transactions relevant to an income analysis.
   
   Included in this will be adding spending groups (logical
   groupings of transaction categoreis) to each transaction,
   removing spending groups not relevant to an income analysis, 
   and adjusting any debits so that they offset income in a category
   
   The output of this will be two new CSV files
   - OUTPUT_INCOME_DATA is a CSV of the individual transactions
   related to income only
   - OUTPUT_INCOME_BY_SPENDING_BY_GROUP is a CSV of the total annual income
   by spending group for each year represented in the transaction data
'''
import pandas as pd
import extract_spending_data_methods as esd
import sys
import webbrowser
import os

# Import the shared configuration file
import expenses_config as ec

# Generated list of transactions removed when extracting spending
REMOVED_TRANSACTIONS_REPORT = ec.REPORTS_PATH+'removed-income-transactions.txt'

# Read the raw mint transaction data into a dataframe
parse_dates = ['Date']
try:
    df = pd.read_csv(ec.PATH_TO_YOUR_TRANSACTIONS, parse_dates=parse_dates)
    df.set_index(['Date'], inplace=True)
    df['Amount'] = df['Amount'].astype(float)
except BaseException as e:
    print('Failed to read mint transaction data: {}'.format(e))
    sys.exit(-1)


## Run through the transaction list from mint and add a Spending Group column
# Set the final parameter to True to get some output about which categories are being assigned to which group
try:
    df = esd.group_categories(df, ec.PATH_TO_SPENDING_GROUPS, show_group_details=False)
except BaseException as e:
    sys.exit(-1)

print('Extracting Income by year...')
## Iterate through the mint data a year at a time, write analysis to a file
# This will make the exclude group and refund analysis more "consumable"
all_df = pd.DataFrame()
saved_stdout = sys.stdout
sys.stdout = open(REMOVED_TRANSACTIONS_REPORT, 'w')

for year in df.index.year.unique():        
    # Extract a years worth of spending data from the transaction data    
    # This will remove all transactions in Spending Groups defined in ec.PATH_TO_GROUPS_TO_EXCLUDE
    # Generally these categories represent income or transactions like Credit Card Payments
    from_date = str(year-1) + '-12-31'
    to_date = str(year+1) + '-01-01'
    
    try:
        year_df = esd.extract_income(df, ec.PATH_TO_GROUPS_TO_EXCLUDE_FROM_INCOME, from_date, to_date)
    except BaseException as e:
        sys.exit(-1)

    # Add the years spending data to a running total dataframe
    # Dedicate amount column for each year for easy summarization later
    # TODO: This summarization should be possible without the extra columns
    column_title = str(year)+' Amount'
    if all_df.empty:
        all_df = year_df
        all_df.rename(columns={'Amount': column_title}, inplace=True)
    else:
        year_df.rename(columns={'Amount': column_title}, inplace=True)
        all_df =pd.concat([year_df, all_df])

# Write the raw spending transaction data to disk as a csv
all_df.to_csv(ec.OUTPUT_INCOME_DATA)
# Summarize expenses by category, by year
expenses = all_df.groupby(['Spending Group']).sum()
expenses.to_csv(ec.OUTPUT_INCOME_BY_SPENDING_BY_GROUP)

# Show the report in a webbrowser
sys.stdout.close()
sys.stdout = saved_stdout
print('Done. See analysis of exclude groups and refunds in window')
webbrowser.open('file://' + os.path.realpath(REMOVED_TRANSACTIONS_REPORT), new=2) # new=2: open in a new tab, if possible
sys.exit(0)

