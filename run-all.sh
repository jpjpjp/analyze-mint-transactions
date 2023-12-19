#!/usr/bin/env bash

# Run all the python scripts to analyze spending
echo Extracting income and spending from mint transaction data...
python extract_spending_and_income.py;
if [ $? -gt 0 ]; then
	exit $?
fi

echo Visualizing Year over Year income...
python visualize_income_by_year.py
if [ $? -gt 0 ]; then
	exit $?
fi

echo Building Detailed Income by Group view....
python show_income_group_details.py
if [ $? -gt 0 ]; then
	exit $?
fi

echo Visualizing Year over Year spending...
python visualize_spending_by_year.py
if [ $? -gt 0 ]; then
	exit $?
fi

echo Visualizing Predicted Future Spending...
python predict_future_spending.py
if [ $? -gt 0 ]; then
	exit $?
fi

echo Building Detailed Spending by Group view....
python show_spending_group_details.py
if [ $? -gt 0 ]; then
	exit $?
fi

python save_todays_transactions.py


