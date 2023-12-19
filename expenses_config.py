# expenses_config.py
'''This file defines a set of configuration
   variables that will be used by the various
   scripts to help analyze mint transaction data
'''


#################
# Input Files
#################
# File with accumulated raw mint transaction data
PATH_TO_YOUR_TRANSACTIONS = "transactions.csv"

# File with new transaction data
PATH_TO_NEW_TRANSACTIONS = "empower-transactions.csv"

# Set the Source of the new transactions.  "mint" and "empower" are currently supported
NEW_TRANSACTION_SOURCE = "empower"
# Empower supports fewer categories than mint, but doesn't appear to limit tags
# Set USE_EMPOWER_LABELS to override categories with labels
USE_EMPOWER_LABELS = "true"
# Optionally specify any categories which you don't want to override with tags
SKIP_CATEGORIES = ['122 Spring St']

# Input file describing which categories to group into which larger spending groups
# This is a CSV where the first row in each column is the name of a "Spending Group"
# The mint categories that belongs to each Spending Group are in listed in each column
# Categories not assigned to a group will be assigned a Spending Group that matches the Category
# See mint-spending-groups-template.csv for an example
PATH_TO_SPENDING_GROUPS = "./mint-spending-groups.csv"

# Input file describing Mint categories to exclude from spending analysis
# This is a CSV file that describes the Spending Groups whose transctions will be removed
# from the spending data.  This is typically Income, Credit Card Payments along with any
# other non spending data (ie: reimbursed expenses, transactions related to a rental property, etc)
# The format of the files is a Spending Group in the first column.  A second column can be set to False
# to hide a short printed analysis of the income and expense associated with the category
# See exclude-spending-group-template.csv for an example
PATH_TO_GROUPS_TO_EXCLUDE = "./exclude-from-spending-groups.csv"

# Input file describing Mint categories to exclude from income analysis
# This is a CSV file that describes the Spending Groups whose transctions will be removed
# from the income data.  This is typically Spending Groups that have some credits
# but shouldn't be considered as income, such as Credit Card Payments, Transfer or 
# or potentially categories that are used to track reimbursable business expenses
PATH_TO_GROUPS_TO_EXCLUDE_FROM_INCOME = "./exclude-from-income-groups.csv"



#################
# Configuration
#################
# Third party accounts to extract from Transaction Data:
THIRD_PARTY_ACCOUNTS = ["Granny Checking", "Granny Savings", "Granny Line of Credit", "Granny Upromise Mastercard"]
THIRD_PARTY_PREFIX = "granny"

# When predicting future spending, the tools will use the averages
# of previous years' spending.  In order to not skew the numbers,
# partial year transaction data should be excluded from this analysis

# Set this to skip data from old or imcomplete years
IGNORE_YEARS_BEFORE = 2014

# Get the current year.  We'll exclude expenses in the current year from the Averages
# Simply set current year to a future year if you prefer to include this year in the average
import datetime
currentDateTime = datetime.datetime.now()
date = currentDateTime.date()
CURRENT_YEAR = int(date.strftime("%Y"))
# CURRENT_YEAR = 2999

# List of Spending Groups to remove from Projected Retirement Spending 
# List groups as strings, seperated by commas, with no space inbetween
EXCLUDE_FROM_RETIREMENT="Kids","Retirement Saving","State & Federal Taxes"

#################
# Output Files
#################
# Output file of just the spending data broken into spending categories
PATH_TO_SPENDING_DATA = 'spending.csv'

# Output file of the summarized spending by category
# This file is used as input for the visualizations
PATH_TO_SPENDING_BY_GROUP = 'group_spending.csv'

# Output file of just the transactions that generated net income
OUTPUT_INCOME_DATA = 'income.csv'

# Output file of the summarized income by category
# This file is used as input for the visualizations
OUTPUT_INCOME_BY_SPENDING_BY_GROUP = 'group_income.csv'

# Directory where visualization files and HTML Reports should be written to
# If changed make sure that the directory exists
REPORTS_PATH = './reports/'

