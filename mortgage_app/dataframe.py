import base64
import json
import os
from decimal import Decimal
from typing import List

import gspread
import pandas as pd
import datetime

from .models import Property, PropertyFundShare
from dotenv import load_dotenv

load_dotenv()

encoded_service_account = os.getenv('GSPREAD_SERVICE_ACCOUNT')


def create_dataframe(properties: List[Property]) -> pd.DataFrame:

    initial_allocation = 0

    # Collect all unique months across all properties
    all_months = set()
    for prop in properties:
        now = datetime.datetime.now()
        start_date = prop.created
        end_date = prop.closed if prop.closed else now
        months = pd.date_range(start=start_date.replace(day=1), end=end_date, freq='MS').strftime('%b-%y').tolist()
        all_months.update(months)

    all_months = sorted(list(all_months), key=lambda x: datetime.datetime.strptime(x, '%b-%y'))

    # Create a DataFrame to store allocations
    columns = ['loan_id', 'property_name', 'cost'] + all_months
    data = []

    # Iterate over properties to populate the DataFrame
    for prop in properties:
        now = datetime.datetime.now()
        start_date = prop.created
        end_date = prop.closed if prop.closed else now
        months = pd.date_range(start=start_date.replace(day=1), end=end_date, freq='MS').strftime('%b-%y').tolist()

        # Initialize all allocations to initial_allocation
        property_data = [prop.loan_id, prop.name, prop.cost] + [initial_allocation] * len(all_months)

        # Update only the relevant months for this property
        for month in months:
            idx = columns.index(month)
            property_data[idx] = initial_allocation

        data.append(property_data)

    df = pd.DataFrame(data, columns=columns).fillna(0)
    df = df.drop_duplicates(subset=['loan_id'])

    return df


# Function to update allocations from a certain month
def update_allocations(df, updates: List[PropertyFundShare]) -> pd.DataFrame:
    for update in updates:
        prop_id = update.loan_id
        prop_closed = update.closed
        start_month = update.date_of_change.strftime('%b-%y')
        new_allocation = update.share_amount

        if start_month in df.columns:
            idx = df['loan_id'] == prop_id
            # Find the column index to start updating
            start_idx = df.columns.get_loc(start_month)
            # Update the allocation from the start month onwards
            df.iloc[idx, start_idx:] = float(new_allocation)
            if prop_closed:
                closed_idx = df.columns.get_loc(prop_closed.strftime('%b-%y')) + 1
                df.iloc[idx, closed_idx:] = float(0.00)
    return df


# Example: Change allocations in one run
# updates = [
#     {'loan_id': '0728-23-01', 'start_month': 'Jan-24', 'new_allocation': 100000},
#     {'loan_id': '0728-23-01', 'start_month': 'Feb-24', 'new_allocation': 110000},
#     {'loan_id': '0728-23-01', 'start_month': 'Apr-24', 'new_allocation': 20000},
#     {'loan_id': '0728-23-02', 'start_month': 'Mar-24', 'new_allocation': 120000},
#     {'loan_id': '0728-23-02', 'start_month': 'Jun-24', 'new_allocation': 140000}
# ]


# df = create_dataframe(properties)
# update_allocations(df, updates)
#
# # Set display options
# pd.set_option('display.max_columns', None)  # Show all columns
# pd.set_option('display.expand_frame_repr', False)  # Do not wrap columns

# df_reset = df.reset_index(drop=True)
# print(df_reset)

# Print the updated DataFrame
# print(df_reset)
# print(df_reset.to_json())
# Save to an HTML file
# df.to_html('property_fund_allocation.html', index=False)
def merge_dataframes(dataframes: List[pd.DataFrame]) -> pd.DataFrame:
    # Concatenate dataframes
    df_combined = pd.concat(dataframes, ignore_index=True)

    # Set the index for merging purposes
    df_combined.set_index(['loan_id', 'property_name', 'cost', 'fund_name'], inplace=True)

    # Reshape the data using pivot_table
    df_pivot = df_combined.unstack('fund_name')

    # Flatten the MultiIndex columns
    df_pivot.columns = ['_'.join(col).strip() for col in df_pivot.columns.values]

    # Reset the index to turn the loan_id, property_name, and cost back into columns
    df_pivot.reset_index(inplace=True)
    df_pivot.fillna(0.0, inplace=True)
    # Rename columns to prettify the names
    df_pivot.rename(columns={'loan_id': 'Loan ID', 'property_name': 'Property Name', 'cost': 'Cost'}, inplace=True)

    # Ensure the month order is maintained as in the input data
    # month_order = ['Jan-24', 'Feb-24', 'Mar-24', 'Apr-24', 'May-24', 'Jun-24', 'Jul-24']
    # ordered_columns = ['loan_id', 'property_name', 'cost'] + [f'{month}_{fund}' for month in month_order for fund in ['Fund1', 'Fund2'] if f'{month}_{fund}' in df_pivot.columns]
    #
    # # Reorder the columns accordingly
    # df_pivot = df_pivot[ordered_columns]

    # Display the result
    return df_pivot


def update_spreadsheet(df: pd.DataFrame) -> None:
    # Decode the Base64 string to get the JSON content
    service_account_info = json.loads(base64.b64decode(encoded_service_account))

    client = gspread.service_account_from_dict(service_account_info)

    # Create a Google Spreadsheet instance
    spreadsheet = client.open("Investments allocation by Loan").worksheet('Loan Book')

    df = df.map(lambda x: float(x) if isinstance(x, Decimal) else x)
    data_list = df.values.tolist()

    spreadsheet.clear()
    spreadsheet.resize(rows=1)
    spreadsheet.append_row(df.columns.tolist())
    spreadsheet.append_rows(data_list)

