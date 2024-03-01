"""show_group_income_details.py

    From an input of income data where each transaction has a category and a
    spending group,generate tables for each spending group that
    shows the annual income by category
"""
import visualization_methods as vms
import webbrowser
import os

# Import the shared configuration file
import expenses_config as ec

# HTML report this module will generate
HTML_OUT = ec.REPORTS_PATH + "group-income_details.html"
HTML_F = open(HTML_OUT, "w")

# Create a dataframe from the annual income  by group data file
df = vms.read_structured_transactions(
    ec.OUTPUT_INCOME_DATA,
    ec.PATH_TO_YOUR_TRANSACTIONS,
    "Date",
    "summarized income group data",
)

# Loop through each of the spending groups and show the year over year details
for group in sorted(df["Spending Group"].unique()):
    filtered_df = df.filter(regex='Amount|Category|Spending Group')
    group_df = vms.build_category_details(filtered_df, group)
    group_df.drop("Spending Group", axis=1, inplace=True)
    print("<H2><center>Details for " + group + " income<center></H2>", file=HTML_F)
    print(group_df.to_html(), file=HTML_F)

# Show the report in a webbrowser
HTML_F.close()
webbrowser.open(
    "file://" + os.path.realpath(HTML_OUT), new=2
)  # new=2: open in a new tab, if possible
