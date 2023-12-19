import os
import shutil
import datetime

import read_mint_transaction_data as rmtd
# Import shared configuration file
import expenses_config as ec


def move_csv_file(trans):
    """
    Moves a transaction csv file that was updated today to the
    default mint transaction data if it was updated today and the user approves
    """
    todays = rmtd.get_latest_transaction_file(trans, query_user=False)
    if todays != trans:
        answer = input(f"Do you want to update {trans} with the newly updated {todays}? (y/n) ")
        if answer.lower() == 'y':
            # Move file1 to file2
            shutil.move(todays, trans)
            print(f"{todays} has been moved to {trans}.")
    else:
        print(f"{trans} was not updated today.")

if __name__ == '__main__':
    move_csv_file(ec.PATH_TO_YOUR_TRANSACTIONS)