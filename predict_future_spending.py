# predict_future_spending.py
"""From an input of expense data summarized
   by group per year, generate a set of visualizations
   that may be useful to predict future spending
"""
import visualization_methods as vms
import webbrowser
import os
import sys

# Import the shared configuration file
import expenses_config as ec

# HTML report this module will generate
HTML_OUT = ec.REPORTS_PATH + "fulture-spending.html"
HTML_F = open(HTML_OUT, "w")

# Create a dataframe from the annual spending by group data file
df = vms.read_structured_transactions(
    ec.PATH_TO_SPENDING_BY_GROUP,
    ec.PATH_TO_YOUR_TRANSACTIONS,
    "Spending Group",
    "summarized spending group data",
)

# year over year visualizations we may have different categories each year
# Create an assigned color for each category so the colors are consistent
colors = vms.assign_colors_to_groups(df)

# Remove old and current year data to generate a good average
minyr = 3000
maxyr = 1900
for col in df.columns:
    year = int(col.split(" ", 1)[0])
    if year < ec.IGNORE_YEARS_BEFORE or year == ec.CURRENT_YEAR:
        del df[col]
    elif year < minyr:
        minyr = year
    elif year > maxyr:
        maxyr = year

# Make sure we have some data to work with
if len(df.columns) <= 0:
    print("No complete year data to work with. Exiting.")
    sys.exit(0)

# Create a new column with the average annual spending by group
df["Average"] = df.mean(numeric_only=True, axis=1)
# Drop spending groups that have an average of zero spending
df = df[df["Average"] != 0]

report_png = "average-spending-by-category.png"
title = title = "Average Annual Spending " + str(minyr) + " - " + str(maxyr)
vms.visualize_average_spending_by_group(df, title, colors, ec.REPORTS_PATH + report_png)
print("<image src=./" + report_png + ">", file=HTML_F)

# Remove certain spending groups that should not be applicable in retirement
ret_df = df
for group in ec.EXCLUDE_FROM_RETIREMENT:
    ret_df = ret_df[ret_df.index != group]

report_png = "projected-retirement-spending-by-category.png"
vms.visualize_average_spending_by_group(
    ret_df, "Projected Retirement Spending", colors, ec.REPORTS_PATH + report_png
)
print("<br>", file=HTML_F)
print("<image src=./" + report_png + ">", file=HTML_F)


# Show the report in a webbrowser
HTML_F.close()
webbrowser.open(
    "file://" + os.path.realpath(HTML_OUT), new=2
)  # new=2: open in a new tab, if possible
