# visualization_methods.py
"""A set of functions that enable visualization
   of dataframes or series of spending and income
   information
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


# Function for generating a pie chart of expenses
def visualize_expenses_by_group(year, year_data, colors, out_file="", spending=True):
    """Build a pie chart with a legend that shows spending
    by spending group for a year.

    year - year (str) that grouped spending totals are for
    year_data - a series with spending totals fby spending group
    colors - a dict of assigned matplotlib colormap vals for each group
    out_file - an optional output file to write the visualization to
    spending - optional.  Set to false if visualizing income transactions
    """
    # Build a legend for a Pie Chart that includes the Spending Category and the Amount
    legend_label = []
    for idx in year_data.index:
        if year_data.loc[idx] <= 0:
            # Remove categories with "negative spending"
            if year_data.loc[idx] < 0:
                print(
                    "Spending on "
                    + idx
                    + ": ${:,.2f}".format(year_data.loc[idx])
                    + " was really income."
                )
            year_data.drop([idx], inplace=True)
        else:
            # Otherwise add the group name and amount to the legend
            legend_label.append(idx + ": ${:,.2f}".format(year_data.loc[idx]))
    expenses_for_year = year_data.sum()

    # Plot the chart
    if spending:
        title = str(year) + " Spending: " + "${:,.2f}".format(expenses_for_year)
    else:
        title = str(year) + " Income: " + "${:,.2f}".format(expenses_for_year)
    year_data.plot(
        kind="pie",
        figsize=(8, 8),
        title=title,
        colors=[colors[key] for key in year_data.index],
    )
    plt.legend(legend_label, loc="center right", bbox_to_anchor=(1.9, 0.5))

    # Write chart to a file or stdout
    if out_file:
        plt.savefig(out_file, bbox_inches="tight")
    else:
        plt.show()
    plt.close()


def visualize_average_spending_by_group(sbg, title, colors, out_file=""):
    """Build a pie chart with a legend that shows spending
    the average spending by group for previous years.

    sbg - a dataframe with Spending Groups as index and a column called "Average"
    title - the title for the visualization
    colors - a dictionary of assigned matplotlib colormap values for each spending group
    out_file - an optional output file to write the visualization to
    """
    # Build a legend for a Pie Chart that includes the Spending Category and the Amount
    legend_label = []
    average_total = sbg["Average"].sum()

    for idx in sbg.index:
        if sbg.loc[idx].Average < 0:
            print(
                "Average spending on "
                + idx
                + ": ${:,.2f}".format(sbg.loc[idx].Average)
                + " is negative. Removing from analysis."
            )
            average_total -= sbg.loc[idx].Average
            sbg.drop([idx], inplace=True)
        else:
            legend_label.append(idx + ": ${:,.2f}".format(sbg.loc[idx].Average))

    sbg.plot(
        kind="pie",
        y="Average",
        figsize=(8, 8),
        colors=[colors[key] for key in sbg.index],
        title=title + ": " + "${:,.2f}".format(sbg.Average.sum()),
    )
    plt.legend(legend_label, loc="center left", bbox_to_anchor=(1.5, 0.5))

    if out_file:
        plt.savefig(out_file, bbox_inches="tight")
    else:
        plt.show()
    plt.close()


#
# Create an assigned color for each category so the colors are consistent
def assign_colors_to_groups(df):
    """Create a dictionary to map each spending category in a
    dataframe to a specific color so that they are consistent
    across different visaulizations

    df - a dataframe indexed by a spending group
    """
    # Tab20 is a matplotlib colormap
    # Others can be found here:
    # https://matplotlib.org/stable/tutorials/colors/colormaps.html
    tab20_colors = list(plt.cm.tab20.colors)
    color_list = tab20_colors
    # If we have more than 20 Spending Groups grow
    # the color list so that each Group gets a specific color
    # Repeats should not be close to each other
    while len(color_list) < len(df.index):
        color_list += tab20_colors
    color_list = tuple(color_list)
    # Assign each Spending Group a specific color
    return dict(zip(df.index, color_list[: len(df.index)]))


def read_structured_transactions(
    structured_transactions,
    raw_transactions,
    index,
    structured_data_description="structured transaction data",
):
    """Create a dataframe from a csv file that has contains a subset of
    transactions which have been structured to include only spending or income,
    with spending groups, etc

    structured_stransactions - a CSV file with the structured transaction data
    raw_transactions - the raw mint transaction data used to create the structured data
    index - the column that should be used for the index in the returned dataframe
    structured_data_description - description for error messages
    """
    # Make sure structured is newer than raw mint data
    try:
        f1 = os.path.getmtime(structured_transactions)
        f2 = os.path.getmtime(raw_transactions)

        if f1 < f2:
            print(
                "Raw mint transactions data: "
                + raw_transactions
                + " is newer than the "
                + structured_data_description
                + ": "
                + structured_transactions
                + ".\n"
                + 'Please run "python extract_spending_and_income.py" first.'
            )
            quit()
    except BaseException as e:
        print(
            "Failed to read "
            + structured_data_description
            + ": "
            + structured_transactions
            + "\n{}".format(e)
        )
        print('Please run "python extract_spending_and_income.py" first.')
        quit()

    # Read the summarized annual expenses by spending group
    try:
        print(
            "Reading "
            + structured_data_description
            + " from "
            + structured_transactions
        )
        df = pd.read_csv(structured_transactions)
        df.set_index(index, inplace=True)
    except BaseException as e:
        print("Failed to read " + structured_data_description + ": {}".format(e))
        quit()

    return df


def build_summary_table(df, ret_df=None):
    """Creata dataframe suitable for output as a table
    to provide a "big picture" view of year over year
    spending/income by category

    If included add predicted retirment spending in the summary
    """
    # Calculate the Annual Totals for all Groups
    sum_row = {col: df[col].sum() for col in df}

    # Calculate the Annual Total of Retirement expenses
    if ret_df is not None:
        sum_ret_row = {col: ret_df[col].sum() for col in ret_df}

    # Add these new rows to the table for display
    df.loc[" "] = pd.Series(" ")
    df.loc["Total"] = sum_row
    if ret_df is not None:
        df.loc["Retirement Total"] = sum_ret_row

    # Dispaly nueric values as currency, NaN as an empty row
    pd.options.display.float_format = "${:,.2f}".format
    df.replace(np.nan, "", inplace=True)

    return df


def build_category_details(df, category=""):
    if category != "":
        category_costs = df[df["Spending Group"] == category]
    else:
        category_costs = df
    category_expenses = category_costs.groupby(["Category"]).sum()
    category_expenses = category_expenses.sort_index(axis=1)
    category_expenses.loc["Total"] = category_expenses.sum()
    return category_expenses
