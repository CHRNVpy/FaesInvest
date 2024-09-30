import base64
import json
import os
import time
from functools import total_ordering

import gspread
import pandas as pd
from datetime import datetime
import calendar
from dotenv import load_dotenv

from .models import TableRow

load_dotenv()

encoded_service_account = os.getenv('GSPREAD_SERVICE_ACCOUNT')

# Decode the Base64 string to get the JSON content
service_account_info = json.loads(base64.b64decode(encoded_service_account))

client = gspread.service_account_from_dict(service_account_info)

# Create a Google Spreadsheet instance
spreadsheet = client.open("Intercompany")


def create_new_sheet(name: str):
    new_sheet = spreadsheet.add_worksheet(title=name, rows=5, cols=25)
    return new_sheet

def investment_calc(entry: TableRow, google=False):
    # Define the investment details
    entry_date = entry.created
    amount_invested = float(entry.investment_amount)  # in dollars
    annual_rate = float(entry.interest_rate) / 100  # 10% annual interest rate
    start_date = entry_date
    start_month = start_date.replace(day=1)

    # Calculate daily, monthly, and quarterly rates
    daily_rate = annual_rate / 365
    daily_360_rate = annual_rate / 360
    monthly_rate = annual_rate / 12

    # Generate date range from start date to current date
    current_date = pd.Timestamp(datetime.now())
    close_date = pd.Timestamp(entry.finished) if entry.finished else None
    end_date = close_date if close_date else current_date
    date_range_monthly = pd.date_range(start=start_month, end=end_date, freq='MS')

    # Create a dictionary to store the data
    data = {
        'id': entry.id,
        'Date': entry_date,
        'Finished': close_date,
        'Principal': amount_invested,
        'Description': entry.name,
        'Loan ID': entry.loan_id if entry.loan_id else '',
        'Rate': entry.interest_rate,
    }

    if google:
        data = {
            'Date': entry_date,
            'Finished': close_date,
            'Principal': amount_invested,
            'Description': entry.name,
            'Loan ID': entry.loan_id if entry.loan_id else '',
            'Rate': entry.interest_rate,
        }

    # first month interest
    days_in_first_month = calendar.monthrange(start_date.year, start_date.month)[1]
    rest_days_in_first_month = days_in_first_month - start_date.day

    for month in date_range_monthly:
        days_in_month = (end_date - month).days + 1
        if month == date_range_monthly[0]:
            if entry.investment_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
                monthly_interest_month = amount_invested * monthly_rate * (rest_days_in_first_month / days_in_month)
            elif entry.investment_method == 'Daily 360':
                monthly_rate = daily_360_rate * days_in_month
                monthly_interest_month = amount_invested * monthly_rate * (rest_days_in_first_month / days_in_month)
            else:
                if start_date.day == 1:
                    monthly_interest_month = amount_invested * monthly_rate * (days_in_month / days_in_month)
                else:
                    monthly_rate = daily_rate * days_in_month
                    monthly_interest_month = amount_invested * monthly_rate * (rest_days_in_first_month / days_in_month)
        elif month == date_range_monthly[-1] and entry.finished:
            total_days_in_month = calendar.monthrange(month.year, month.month)[1]
            if end_date.day < total_days_in_month:
                daily_rate = daily_360_rate if entry.investment_method == 'Daily 360' else daily_rate
                monthly_interest_month = amount_invested * daily_rate * days_in_month
            else:
                if entry.investment_method == 'Daily':
                    monthly_rate = daily_rate * days_in_month
                elif entry.investment_method == 'Daily 360':
                    monthly_rate = daily_360_rate * days_in_month
                monthly_interest_month = amount_invested * monthly_rate * (total_days_in_month / total_days_in_month)
        else:
            days_in_month = calendar.monthrange(month.year, month.month)[1]
            if entry.investment_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
            elif entry.investment_method == 'Daily 360':
                monthly_rate = daily_360_rate * days_in_month
            monthly_interest_month = amount_invested * monthly_rate * (days_in_month / days_in_month)

        data[month.strftime("%b-%Y")] = round(monthly_interest_month, 2)

    return data

def build_table(entries: TableRow) -> tuple[dict, dict]:
    all_data = []

    for entry in entries:
        enriched_data = investment_calc(entry)
        all_data.append(enriched_data)

    df = pd.DataFrame(all_data)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Date'] = df['Date'].dt.strftime("%b %d, %Y")

    df['Finished'] = pd.to_datetime(df['Finished'])
    df['Finished'] = df['Finished'].dt.strftime("%b %d, %Y")

    df['Rate'] = df['Rate'].astype(float)
    df = df.fillna('')

    data_list = df.values.tolist()

    return df.columns.tolist(), data_list

def update_spreadsheet(data, sheet_name):
    all_data = []

    for entry in data:
        enriched_data = investment_calc(entry, google=True)
        all_data.append(enriched_data)

    df = pd.DataFrame(all_data)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Date'] = df['Date'].dt.strftime('%m-%d-%Y')

    df['Finished'] = pd.to_datetime(df['Finished'])
    df['Finished'] = df['Finished'].dt.strftime('%m-%d-%Y')

    df['Rate'] = df['Rate'].astype(float)
    df = df.fillna('')

    # Extract month-year columns and sort them in chronological order
    month_columns = [col for col in df.columns if '-' in col]
    sorted_month_columns = sorted(month_columns, key=lambda x: pd.to_datetime(x, format='%b-%Y'))

    # Reorder the DataFrame columns with sorted months
    df = df[['Date', 'Finished', 'Principal', 'Description', 'Loan ID', 'Rate'] + sorted_month_columns]

    data_list = df.values.tolist()

    sheet = spreadsheet.worksheet(sheet_name)
    sheet.clear()
    sheet.resize(rows=1)
    sheet.append_row(df.columns.tolist())
    sheet.append_rows(data_list)