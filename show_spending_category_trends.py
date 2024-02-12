# show_spending_category_trends.py
"""From an input of expense data show a table of spending by category
   year over year, color coding significant deviations from the previous
   year or the yearly average for the category
"""
import visualization_methods as vms
import pandas as pd
import webbrowser
import os
import sys

# Import the shared configuration file
import expenses_config as ec

# HTML report this module will generate
HTML_OUT = ec.REPORTS_PATH + "spending-category-trends.html"


# Function to color code spending by year
def style_year_over_year(x, use_average=False):
    # Create a DataFrame with the same shape, filled with empty strings
    styles = pd.DataFrame("", index=x.index, columns=x.columns)
    avg_col = len(x.columns) - 1

    # Loop through the DataFrame by rows
    for row in range(0, len(x)):
        if x.index[row] == " ":
            continue
        for col in range(1, len(x.columns) - 1):  # Exclude the 'average' column
            # Calculate the percent change from the previous year or average
            if use_average:
                comp = x.iloc[row, avg_col]
            else:
                comp = x.iloc[row, col - 1]
            current_year = x.iloc[row, col]
            if comp != 0:  # Avoid division by zero
                if abs(comp - current_year) < 500:
                    # Don't bother for small values
                    continue
                percent_change = (current_year - comp) / comp * 100

                # Apply color coding based on the conditions
                if -25 <= percent_change < -10:
                    styles.iloc[row, col] = "background-color: green; color: white"
                elif percent_change < -25:
                    styles.iloc[row, col] = "background-color: blue; color: white"
                elif 10 <= percent_change < 25:
                    styles.iloc[row, col] = "background-color: yellow; color: black"
                elif percent_change > 25:
                    styles.iloc[row, col] = "background-color: red; color: white"

    return styles


# Function to format numbers as dollar amounts
def format_dollars(val):
    try:
        return "${:,.2f}".format(val)
    except (ValueError, TypeError):
        return val  # Return the value as is if it can't be formatted


# Create a dataframe from the annual spending by group data file
df = vms.read_structured_transactions(
    ec.PATH_TO_SPENDING_BY_GROUP,
    ec.PATH_TO_YOUR_TRANSACTIONS,
    "Spending Group",
    "summarized spending group data",
)

# Make sure we have some data to work with
if len(df.columns) <= 0:
    print("No complete year data to work with. Exiting.")
    sys.exit(0)

# Create a new column with the average annual spending by group
df["Average"] = df.mean(numeric_only=True, axis=1)
# Drop spending groups that have an average of zero spending
df = df[df["Average"] != 0]

# Remove certain spending groups that should not be applicable in retirement
ret_df = df
for group in ec.EXCLUDE_FROM_RETIREMENT:
    ret_df = ret_df[ret_df.index != group]

# Build a "summary" dataframe that we can visulize as a table
sum_df = vms.build_summary_table(df, ret_df)

caption = """
Changes in Category Spending Year over Year -- Color Codes:
<br>
<span style='color: green;'>Green</span>: 10-25% less than the prev. year,
<span style='color: blue;'>Blue</span>: >25% less than the previous year
<br>
<span style='color: yellow;'>Yellow</span>: 10-25% more than the previous year,
<span style='color: red;'>Red</span>: >25% more than the previous year
"""

table_styles = [
    {
        "selector": "th, td",
        "props": "border: 1px solid black;",
    },  # Borders for cells
    {
        "selector": "table",
        "props": "border-collapse: collapse; margin: 10px 0; border: 2px solid black;",
    },  # Border for the table
    {
        "selector": "caption",
        "props": "caption-side: top; font-size: 1.5em; text-align: center;",
    },  # Style for caption
]

# Apply the styling comparing with previous year
styled_df = (
    sum_df.style.apply(style_year_over_year, axis=None)
    .format(format_dollars)  # Format numbers as dollar amounts
    .set_table_styles(table_styles)
    .set_caption(caption)
)  # Set table title

HTML_F = open(HTML_OUT, "w")
print(styled_df.to_html(), file=HTML_F)

# Apply the styling comparing with yearly average
caption = """
<br>
Yearly Spending by Category vs Average -- Color Codes:
<br>
<span style='color: green;'>Green</span>: 10-25% less than average,
<span style='color: blue;'>Blue</span>: >25% less than average
<br>
<span style='color: yellow;'>Yellow</span>: 10-25% more than average,
<span style='color: red;'>Red</span>: >25% more than average
"""

styled_df = (
    sum_df.style.apply(style_year_over_year, axis=None, use_average=True)
    .format(format_dollars)  # Format numbers as dollar amounts
    .set_table_styles(table_styles)
    .set_caption(caption)
)  # Set table title
print(styled_df.to_html(), file=HTML_F)

# Show the report in a webbrowser
HTML_F.close()
webbrowser.open(
    "file://" + os.path.realpath(HTML_OUT), new=2
)  # new=2: open in a new tab, if possible
