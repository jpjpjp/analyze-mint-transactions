# extract_spending_data.py
'''Read in a bunch of mint transaction data
   Extract it out year by year and "clean" it
   by removing income and other transactions
   that don't relate to spending

   Output a file that just shows spending data
   (including "income" that was determined to
   be a refund)
'''
import pandas as pd
import sys

# Avoid SettingWithCopyWarning
pd.options.mode.chained_assignment = None  # default='warn'

def extract_spending(mint_df, exclude_spending_group_list, start_after_date, end_before_date):
    """ This method takes a dataframe made up of transactions
        that have been exported from mint and returns a dataframe
        that includes only the spending related transactions 
        that occured between the specified start and end dates
        
        It is assumed that prior to calling this method the mint
        transaction data has been post-processed to include a 
        Spending Group category for each transaction.  (This can
        be done by calling the group_categories method).
        
        After extraction all the transactions for the specified 
        date range this method will remove all transaction associated
        with Spending Groups specified in the exclude_spending_group_list
        CSV.
        
        Any credit transactions that remain are assumed to be "refunds"
        and are converted to negative debit transactions in the returned
        dataframe
    """
    # Check that the input mint transaction has been postprocessed
    # to group transaction categories into Spending Groups
    if not 'Spending Group' in mint_df.columns:
        raise Exception('extract_spending: Input mint transaction data does not have a Spending Group column\n.\
            Pass data to group_transactions method before calling this method')
        
    # Extract the transactions for the specified date range
    new_df = extract_transactions_by_date_range(mint_df, start_after_date, end_before_date)
    
    # Remove all the transactions associated with Spending Groups in the exclude list
    new_df = remove_excluded_spending_group(new_df, exclude_spending_group_list)
 
    # Iterate over the remaining groups and remove any income, which at this
    # point should be considered as a "refund"
    print('\n-------- Analyzing Credits by Spending Group ---------\n')
    for group in new_df['Spending Group'].unique():
        print('Analyzing credits for spending group: '+group+'....')
        new_df[(new_df['Spending Group'] == group)] = \
            new_df[(new_df['Spending Group'] == group)].apply(find_refunds, axis=1)
        #TODO ?  If the net of the refunds is income instead of spending should I just remove the group?

    # After filtering out "income" that was probably refunds,
    # see what type of unexpected income is left.  This should not happen (I think...)
    income = new_df[new_df['Transaction Type'] == 'credit']
    if len(income):
        print('\nAfter removing refunds the following income is still unexpected:')
        print(income)
    print('')
    return new_df

def extract_income(mint_df, exclude_spending_group_list, start_after_date, end_before_date):
    """ This method takes a dataframe made up of transactions
        that have been exported from mint and returns a dataframe
        that includes only the transactions that are associated 
        with income generation between the specified
        start and end dates
        
        It is assumed that prior to calling this method the mint
        transaction data has been post-processed to include a 
        Spending Group category for each transaction.  (This can
        be done by calling the group_categories method).
        
        After extracting all the transactions for the specified 
        date range this method will remove all transaction associated
        with Spending Groups specified in the exclude_spending_group_list
        CSV.
        
        The remaining transactions are evaluated to determine if 
        they were income generating. Any transaction data associated 
        with the "Income" Spending Group is assumed to be income.
        
        All other Spending Groups are analyzed to determine if the 
        aggregate sum of the transactions during the period were positive.
        Spending Groups that resulted in more spending than income
        during the period are removed from the data set.
        
    """
    # Extract all transactions in the specified date range
    new_df = extract_transactions_by_date_range(mint_df, start_after_date, end_before_date)
    
    # Remove all the transactions associated with Spending Groups in the exclude list
    new_df = remove_excluded_spending_group(new_df, exclude_spending_group_list)
 
    # Iterate over the remaining groups and remove all the transactions
    # for any group whose transactions did not generate income in the aggregate
    print('\n------Looking for Spending Groups with Income -------')
    for group in new_df['Spending Group'].unique():
        if group != 'Income':
            new_df = analyze_and_remove_non_income(new_df, group, output_analysis=True)
            
    print('\nFound '+str(len(new_df))+' Income related transactions between ' +\
        start_after_date+' and '+end_before_date+'\n\n')
    return new_df

def extract_payments_and_income(input_df, spending_group, output_analysis):
    '''This helper method returns the sum of the credits and debits
       for all the transactions associated with a spending group
    '''
    # Compare the income (credits) and the spending (debits) for the group
    spending_group_df = input_df[input_df['Spending Group'] == spending_group]
    payments = spending_group_df[spending_group_df['Transaction Type'] == 'debit'].Amount.sum()
    income = spending_group_df[spending_group_df['Transaction Type'] == 'credit'].Amount.sum()

    # For some categories (ie: Credit Card Payments or Expenses)
    # the payments and credits should match or be close.  
    # If not the data might be a little dirty, so we provide some output that
    # allows them to review it and update their mint categorization
    if output_analysis and (payments > 0 or income > 0):
        print('\nAnalyzing spending_group: '+spending_group+'...')
        print('Found a total of ${:,.2f}'.format(payments)+' payments for this time period.')
        print('Found a total of ${:,.2f}'.format(income)+'  income for this time period.')
    return (payments, income)



def remove_spending_group(input_df, spending_group, output_analysis=True):
    '''This method removes the spending_group from the df
       It is used primarily for things that show up both as debits and credits
       in Mint, for example Credit Card Payments or Reimbursed Expenses
       
       If the output_analysis parameter is set to True
       Print out some info about the credit and debit relationship to allow
       user to analyze the data if it seems pretty far off
    '''
    (payments, income) = extract_payments_and_income(input_df, spending_group, output_analysis)
    output_df = input_df[input_df['Spending Group'] != spending_group]    
    
    if payments > 0 or income > 0:
        if output_analysis and (payments - income) > 0:
            print('Loss of ${:,.2f}'.format(payments - income)+' is not included in the spending analysis')
        elif output_analysis and (income - payments) > 0: 
            print('Unexpected(?) income of ${:,.2f}'.format(income - payments)+' was detected')
        print('After removing ' + spending_group + \
        ' related transactions we have ${:,.2f}'.format(output_df.Amount.sum()) + \
        ' in transactions.')
    else:
        print('\nAnalyzing spending_group: '+spending_group+'... No transactions found')
    return output_df

def analyze_and_remove_non_income(input_df, spending_group, output_analysis=True):
    '''This method analyzes a spending group to see if the sum of the transactions
       are postive.   For groups that did not generate income the set of transactions
       is removed from the data set
       
       If the output_analysis parameter is set to True
       Print out some info about the credit and debit relationship to allow
       user to analyze the data if it seems pretty far off
    '''
    # Compare the income (credits) and the spending (debits) for the group
    (payments, income) = extract_payments_and_income(input_df, spending_group, output_analysis)
    
    if (payments - income) >= 0:
        print('Spending group '+spending_group+' did not generate income. Removing it from income data set')
        return input_df[input_df['Spending Group'] != spending_group]
    else: 
        print('Spending group '+spending_group+' generated income. Keeping it in income data set')
        # Convert any debits into "negative" expenses in the Income generating Spending Group
        input_df[(input_df['Spending Group'] == spending_group)] = \
            input_df[(input_df['Spending Group'] == spending_group)].apply(find_expenses, axis=1)

    return input_df

def group_categories(df, spending_group_defs, show_group_details=False):
    """ Add a new "Spending Group" column to group categories
    
        The categories that belong to each spending group are defined
        in a CSV file that is passed in via the spending_group_defs
    """
    # Create a new "Spending Group" column so that we can start
    # grouping related expenses into a single bucket
    df['Spending Group'] = df.Category
    
    print('Reading spending category definitions from spending from', spending_group_defs)
    try:
        group_cats_df = pd.read_csv(spending_group_defs)
    except BaseException as e:
        print('Failed to read spending category definitions from', \
            spending_group_defs, file=sys.stderr)
        print('The exception: {}'.format(e), file=sys.stderr)
        raise e
    
    # Iterate over spending groups. 
    for group_name, categories in group_cats_df.iteritems():
        categories = categories.dropna()
        if show_group_details:
            print('Setting Spending Group: '+group_name+' to: '+str(categories.tolist()))
        # Assign Spending Group to all transactions with categories for that group
        df['Spending Group'][df.Category.isin(categories.tolist())] = group_name
        # grp = df[df.Category.isin(categories.tolist())]
        # print('\nAnalyzing refunds for spending group: '+group_name+'....')
        # df[grp] = df[grp].apply(find_refunds, axis=1)
            
    return df       

def find_refunds(row):
    """ Look for transactions that have a
        credit for a typical "spending" category
        Change these to a debit with a negative
        amount.

        This results in the refunds getting subtracted
        from the total spend calculations
    """
    if row['Transaction Type'] == 'credit':
        print (' -- Credit on ' + row.name.strftime('%m/%d/%Y') + ' from '+ \
               row.Description + ' for ${:,.2f}'.format(row.Amount))
        row.Amount *= -1
        row['Transaction Type'] = 'debit'
    return row

def find_expenses(row):
    """ Look for transactions that have a
        debit for a typical "income" category
        Change these to a credit with a negative
        amount.

        This results in the expenses getting subtracted
        from the total income calculations
    """
    if row['Transaction Type'] == 'debit':
        print (' -- Expense on ' + row.name.strftime('%m/%d/%Y') + ' from '+ \
               row.Description + ' for ${:,.2f}'.format(row.Amount))
        row.Amount *= -1
        row['Transaction Type'] = 'credit'
    return row

def extract_transactions_by_date_range(input_df, start_after_date, end_before_date):
    '''Helper method to extract all transactions in a date range
    '''
    print('Finding transaction data for period > ' + start_after_date + \
          ' and < ' + end_before_date)
    new_df = input_df[(input_df.index < end_before_date) & (input_df.index > start_after_date)]
    print('Found a total of ${:,.2f}'.format(new_df.Amount.sum()) + \
          ' in transactions for this time period.')
    return new_df

def remove_excluded_spending_group(df, exclude_spending_group_list):
    '''Helper method to remove all transactions in a dataframe
       associated with Spendig Groups identified in the exclude
       spending group list file passed in as a CSV
       
       The first column in the CSV is the name of the Spending groups
       to remove
       
       The second "Hide Analysis" column can optionally be set to false
       to reduce the amount of output printed about the details of the
       spending and income found in the Spending Group
    '''

    print('Reading categories to extract from spending from', exclude_spending_group_list)
    try:
        esg_df = pd.read_csv(exclude_spending_group_list)
    except BaseException as e:
        print('Failed to read list of categories to exclude from spending analysis from', \
            exclude_spending_group_list, file=sys.stderr)
        print('The exception: {}'.format(e), exclude_spending_group_list, file=sys.stderr)
        raise e

    # Remove transactions for each category in the exclude_categories list
    print('\n------ Removing Specified Spending Groups ---------')
    for i, row in esg_df.iterrows():
        if row['Hide Analysis']:
            df = remove_spending_group(df, row['Spending Group'], output_analysis=False)
        else:
            df = remove_spending_group(df, row['Spending Group'])
            
    return df 

