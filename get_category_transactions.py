"""get_category_transactions.py

    This program will extract the files associated with a specified category
    for one or more specified years, and write the transactions to one or more
    CSV files.

    This can be useful when performing investigations into why spending by
    category has changed significicantly.  (Note that the program
    show_spending_category_trends.py generates tables that color code changes
    of 25 or 50% over previous years or the running average)

    Loading these CSV files into a spreadsheet and comparing them can be useful
    to identify why spending changed and to identify changes in spending habits
    or possibly miscategorized transactions.
"""

import pandas as pd
import re
import sys

# Import shared configuration file
import expenses_config as ec
import visualization_methods as vms

# List of columns that we want to keep in addition to Date and Amount
COLUMNS_OF_INTEREST = ["Description", "Category"]


def extract_category_transactions(df, year, category, cols_to_keep):
    """ """
    # Narrow transactions  down to just the year and category of interest
    year_col = f"{year} Amount"
    filtered_df = df[(df["Spending Group"] == category) & (df[year_col].notna())]
    col_filter = cols_to_keep + [year_col]
    filtered_df = filtered_df[col_filter]
    print(
        f"There were {len(filtered_df)} transactions for "
        f"Total spending on {category} for {year}: {filtered_df[year_col].sum():.2f}"
    )
    return filtered_df


def sanitize_filename(s):
    # Replace spaces with a hyphen
    s = s.replace(" ", "-")

    # Remove or replace invalid filename characters
    s = re.sub(r"[^\w\-_\.]", "-", s)

    return s


def output_raw_transactions(group_df, df, group, cols_to_keep, years, outfile):
    # Remove indices of dataframes before merging
    group_df.reset_index(inplace=True)

    # Get the list of "XXXX Amount column names we are interested in"
    column_names = [f"{year} Amount" for year in years]

    # Determine the year with the most transactions to create a spacer column
    max_trans = df[column_names].count().max()
    spacer = pd.DataFrame({"": [""] * max_trans})
    group_df = pd.concat([group_df, spacer], axis=1)

    # Build a dataframe of the raw transactions for each each year
    for i, col in enumerate(column_names):
        year = years[i]
        year_df = df[df[col].notna()]
        print(
            f"\nThere were {len(year_df)} transactions for "
            f"Total spending on {group} for {year}: {year_df[col].sum():.2f}"
        )
        year_df = year_df[cols_to_keep + [col]]
        year_df = year_df.rename(
            columns={
                "Description": f"{year} Description",
                "Category": f"{year} Category",
            }
        ).sort_index()
        year_df.rename_axis(f"{year} Date", inplace=True)
        year_df.reset_index(inplace=True)
        group_df = pd.concat([group_df, year_df, spacer], axis=1)

    print(f"\nWriting this summary of spending by category to {outfile}")
    group_df.to_csv(outfile, index=False)


def main():
    # Read in command-line arguments or prompt for spending group and years
    try:
        if len(sys.argv) >= 2:
            args = sys.argv[1:]
            spending_group = args.pop(0)
            years_str = args.pop(0)
        else:
            spending_group = input("Enter the spending group: ")
            years_str = input(
                "Enter the years to examine seperated by hyphens (ie:2020-2022): "
            )

        # convert the string of years into a hyphenated list
        years_str_list = years_str.split("-")
        years = [int(year.strip()) for year in years_str_list]

        if "-" in years_str:
            # convert the string of years into a hyphenated list
            start_year, end_year = map(int, years_str.split("-"))
            years = [str(year) for year in range(start_year, end_year + 1)]
        else:
            years = [int(years_str)]

    except ValueError:
        print("Invalid input. Please enter the spending group and years.")
        print("Alternately if you supply no params you will be prompted.")
        sys.exit(1)

    # Create a dataframe from the csv with all the spending transactions
    all_df = vms.read_structured_transactions(
        ec.PATH_TO_SPENDING_DATA,
        ec.PATH_TO_YOUR_TRANSACTIONS,
        "Date",
        "spending transaction data",
    )

    # Extract just the transactions for the spending group and years in question
    df = all_df[(all_df["Spending Group"] == spending_group)]
    conditions = [df[f"{year} Amount"].notna() for year in years]
    # Combine the conditions with the logical OR operator
    years_condition = conditions[0]
    for condition in conditions[1:]:
        years_condition |= condition
    df = df[years_condition]

    # Drop the empy amount columns for the other years
    df = df.dropna(axis=1, how="all")

    # Build a summary of spending by category for each of the years
    group_df = vms.build_category_details(df)
    print(group_df)
    outfile = f"{sanitize_filename(spending_group)}-by-category-{years_str}.csv"
    # print(f"\nWriting this summary of spending by category to {outfile}")
    # group_df.to_csv(outfile)

    # Write all the raw transactions to another csv
    outfile = f"{sanitize_filename(spending_group)}-transactions-{years_str}.csv"
    output_raw_transactions(
        group_df, df, spending_group, COLUMNS_OF_INTEREST, years, outfile
    )


if __name__ == "__main__":
    main()
