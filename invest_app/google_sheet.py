import base64
import json
import os

import gspread
import pandas as pd
from datetime import datetime
import calendar
from dotenv import load_dotenv

load_dotenv()

encoded_service_account = os.getenv('GSPREAD_SERVICE_ACCOUNT')

# Decode the Base64 string to get the JSON content
service_account_info = json.loads(base64.b64decode(encoded_service_account))

client = gspread.service_account_from_dict(service_account_info)

# Create a Google Spreadsheet instance
spreadsheet = client.open("Coupons").worksheet('Investors')


def investment_calc(investor):
    # Define the investment details
    investor_name = f'{investor.first_name} {investor.last_name}'
    amount_invested = investor.investment_amount  # in dollars
    annual_rate = investor.investment_rate / 100  # 10% annual interest rate
    # start_date = datetime.strptime(investor.investment_date, '%m/%d/%Y')
    start_date = investor.investment_date
    start_month = start_date.replace(day=1)

    # Calculate daily, monthly, and quarterly rates
    daily_rate = annual_rate / 365
    daily_360_rate = annual_rate / 360
    monthly_rate = annual_rate / 12

    # Generate date range from start date to current date
    current_date = pd.Timestamp(datetime.now())
    close_date = pd.Timestamp(investor.contract_end_date) if investor.contract_end_date else None
    end_date = close_date if close_date else current_date
    date_range_monthly = pd.date_range(start=start_month, end=end_date, freq='MS')
    # print(date_range_monthly)

    # Create a dictionary to store the data
    data = {
        'ID': investor.investor_id,
        'Investor': investor_name,
        'Amount': amount_invested,
        'Close date': datetime.strftime(investor.investment_date, '%m/%d/%Y'),
        'Rate': f'{investor.investment_rate}%',
        'Type': investor.investment_type,
        'Fund': investor.company_name,
        'Balance': amount_invested
    }

    # Calculate monthly interest for each month and sum for each quarter
    quarterly_interests = {}
    last_quarter_name = None
    last_quarter_interest = 0

    # first month interest
    days_in_first_month = calendar.monthrange(start_date.year, start_date.month)[1]
    rest_days_in_first_month = days_in_first_month - start_date.day

    for month in date_range_monthly:
        days_in_month = (end_date - month).days + 1
        if month == date_range_monthly[0] and start_date.day != 1 and start_date.day != 15:
            if investor.investment_count_method == 'Daily 360':
                rest_days_in_first_month = 30 - start_date.day
                monthly_interest_month = amount_invested * daily_360_rate * rest_days_in_first_month
            else:
                monthly_interest_month = amount_invested * daily_rate * rest_days_in_first_month
        elif month == date_range_monthly[0] and start_date.day == 15:
            if investor.investment_count_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
            elif investor.investment_count_method == 'Daily 360':
                days_in_month = 30
                monthly_rate = daily_360_rate * days_in_month
            monthly_interest_month = (amount_invested * monthly_rate * (days_in_month / days_in_month)) / 2
        elif month == date_range_monthly[-1] and end_date.day >= 15:
            # Calculate interest for the last month based on days passed
            if investor.investment_count_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
            elif investor.investment_count_method == 'Daily 360':
                days_in_month = 30 - end_date.day
                monthly_rate = daily_360_rate * days_in_month
            monthly_interest_month = amount_invested * monthly_rate * (days_in_month / days_in_month)
        elif month == date_range_monthly[-1] and end_date.day < 15:
            # Calculate interest for the last month based on days passed
            if investor.investment_count_method == 'Daily 360':
                days_in_month = 30 - end_date.day
                monthly_interest_month = amount_invested * daily_360_rate * days_in_month
            else:
                monthly_interest_month = amount_invested * daily_rate * days_in_month
        else:
            days_in_month = calendar.monthrange(month.year, month.month)[1]
            if investor.investment_count_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
            elif investor.investment_count_method == 'Daily 360':
                days_in_month = 30
                monthly_rate = daily_360_rate * days_in_month
            monthly_interest_month = amount_invested * monthly_rate * (days_in_month / days_in_month)

        data[month.strftime("%b-%Y")] = round(monthly_interest_month, 2)

        quarter_name = "Q" + str((month.month - 1) // 3 + 1) + "-" + str(month.year)
        if quarter_name not in quarterly_interests:
            quarterly_interests[quarter_name] = 0

        if month == date_range_monthly[-1]:
            last_quarter_name = quarter_name
            last_quarter_interest += monthly_interest_month
        else:
            quarterly_interests[quarter_name] += monthly_interest_month

    # Add last quarter interest if it's in progress
    if last_quarter_name in quarterly_interests:
        quarterly_interests[last_quarter_name] += last_quarter_interest
    else:
        quarterly_interests[last_quarter_name] = last_quarter_interest

    # Add quarterly interests to data
    for quarter_name, quarterly_interest in quarterly_interests.items():
        data[quarter_name] = round(quarterly_interest, 2)

    if close_date:
        data['Balance'] = sum([v for k, v in data.items() if k.startswith('Q')]) + data['Balance']

    return data


def reinvestment_calc(investor):
    # Define the investment details
    investor_name = f'{investor.first_name} {investor.last_name}'
    amount_invested = investor.investment_amount  # in dollars
    annual_rate = investor.investment_rate / 100  # 10% annual interest rate
    # start_date = datetime.strptime(investor.investment_date, '%m/%d/%Y')
    start_date = investor.investment_date
    start_month = start_date.replace(day=1)

    # Calculate daily, monthly, and quarterly rates
    daily_rate = annual_rate / 365
    daily_360_rate = annual_rate / 360
    monthly_rate = annual_rate / 12

    # Generate date range from start date to current date
    current_date = pd.Timestamp(datetime.now())
    close_date = pd.Timestamp(investor.contract_end_date) if investor.contract_end_date else None
    end_date = close_date if close_date else current_date
    date_range_monthly = pd.date_range(start=start_month, end=end_date, freq='MS')

    # Create a dictionary to store the data
    data = {
        'ID': investor.investor_id,
        'Investor': investor_name,
        'Amount': amount_invested,
        'Close date': datetime.strftime(investor.investment_date, '%m/%d/%Y'),
        'Rate': f'{investor.investment_rate}%',
        'Type': investor.investment_type,
        'Fund': investor.company_name,
        'Balance': amount_invested
    }

    # Calculate monthly interest for each month and sum for each quarter
    quarterly_interests = {}
    last_quarter_name = None
    last_quarter_interest = 0

    # first month interest
    days_in_first_month = calendar.monthrange(start_date.year, start_date.month)[1]
    rest_days_in_first_month = days_in_first_month - start_date.day

    accumulated_interest = 0

    for month in date_range_monthly:
        days_in_month = (end_date - month).days + 1
        if month == date_range_monthly[0] and start_date.day != 1 and start_date.day != 15:
            if investor.investment_count_method == 'Daily 360':
                rest_days_in_first_month = 30 - start_date.day
                monthly_interest_month = amount_invested * daily_360_rate * rest_days_in_first_month
            else:
                monthly_interest_month = amount_invested * daily_rate * rest_days_in_first_month
        elif month == date_range_monthly[0] and start_date.day == 15:
            if investor.investment_count_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
            elif investor.investment_count_method == 'Daily 360':
                days_in_month = 30
                monthly_rate = daily_360_rate * days_in_month
            monthly_interest_month = (amount_invested * monthly_rate * (days_in_month / days_in_month)) / 2
        elif month == date_range_monthly[-1] and end_date.day >= 15:
            # Calculate interest for the last month based on days passed
            if investor.investment_count_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
            elif investor.investment_count_method == 'Daily 360':
                days_in_month = 30 - end_date.day
                monthly_rate = daily_360_rate * days_in_month
            monthly_interest_month = amount_invested * monthly_rate * (days_in_month / days_in_month)
        elif month == date_range_monthly[-1] and end_date.day < 15:
            # Calculate interest for the last month based on days passed
            if investor.investment_count_method == 'Daily 360':
                days_in_month = 30 - end_date.day
                monthly_interest_month = amount_invested * daily_360_rate * days_in_month
            else:
                monthly_interest_month = amount_invested * daily_rate * days_in_month
        else:
            days_in_month = calendar.monthrange(month.year, month.month)[1]
            if investor.investment_count_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
            elif investor.investment_count_method == 'Daily 360':
                days_in_month = 30
                monthly_rate = daily_360_rate * days_in_month
            monthly_interest_month = amount_invested * monthly_rate * (days_in_month / days_in_month)

        data[month.strftime("%b-%Y")] = round(monthly_interest_month, 2)

        if month.month not in [3, 6, 9, 12]:
            accumulated_interest += monthly_interest_month
        else:
            amount_invested = amount_invested + accumulated_interest + monthly_interest_month
            accumulated_interest = 0

        quarter_name = "Q" + str((month.month - 1) // 3 + 1) + "-" + str(month.year)
        if quarter_name not in quarterly_interests:
            quarterly_interests[quarter_name] = 0

        if month == date_range_monthly[-1]:
            last_quarter_name = quarter_name
            last_quarter_interest += monthly_interest_month
        else:
            quarterly_interests[quarter_name] += monthly_interest_month

        # Add last quarter interest if it's in progress
    if last_quarter_name in quarterly_interests:
        quarterly_interests[last_quarter_name] += last_quarter_interest
    else:
        quarterly_interests[last_quarter_name] = last_quarter_interest

        # Add quarterly interests to data
    for quarter_name, quarterly_interest in quarterly_interests.items():
        data[quarter_name] = round(quarterly_interest, 2)

    data['Balance'] = sum([v for k, v in data.items() if k.startswith('Q')]) + data['Balance']

    return data

def reinvestment_monthly_calc(investor):
    # Define the investment details
    investor_name = f'{investor.first_name} {investor.last_name}'
    amount_invested = investor.investment_amount  # in dollars
    annual_rate = investor.investment_rate / 100  # 10% annual interest rate
    # start_date = datetime.strptime(investor.investment_date, '%m/%d/%Y')
    start_date = investor.investment_date
    start_month = start_date.replace(day=1)

    # Calculate daily, monthly, and quarterly rates
    daily_rate = annual_rate / 365
    daily_360_rate = annual_rate / 360
    monthly_rate = annual_rate / 12

    # Generate date range from start date to current date
    current_date = pd.Timestamp(datetime.now())
    close_date = pd.Timestamp(investor.contract_end_date) if investor.contract_end_date else None
    end_date = close_date if close_date else current_date
    date_range_monthly = pd.date_range(start=start_month, end=end_date, freq='MS')

    # Create a dictionary to store the data
    data = {
        'ID': investor.investor_id,
        'Investor': investor_name,
        'Amount': amount_invested,
        'Close date': datetime.strftime(investor.investment_date, '%m/%d/%Y'),
        'Rate': f'{investor.investment_rate}%',
        'Type': investor.investment_type,
        'Fund': investor.company_name,
        'Balance': amount_invested
    }

    # Calculate monthly interest for each month and sum for each quarter
    quarterly_interests = {}
    last_quarter_name = None
    last_quarter_interest = 0

    # first month interest
    days_in_first_month = calendar.monthrange(start_date.year, start_date.month)[1]
    rest_days_in_first_month = days_in_first_month - start_date.day

    accumulated_interest = 0

    for month in date_range_monthly:
        days_in_month = (end_date - month).days + 1
        if month == date_range_monthly[0] and start_date.day != 1 and start_date.day != 15:
            if investor.investment_count_method == 'Daily 360':
                rest_days_in_first_month = 30 - start_date.day
                monthly_interest_month = amount_invested * daily_360_rate * rest_days_in_first_month
            else:
                monthly_interest_month = amount_invested * daily_rate * rest_days_in_first_month
        elif month == date_range_monthly[0] and start_date.day == 15:
            if investor.investment_count_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
            elif investor.investment_count_method == 'Daily 360':
                days_in_month = 30
                monthly_rate = daily_360_rate * days_in_month
            monthly_interest_month = (amount_invested * monthly_rate * (days_in_month / days_in_month)) / 2
        elif month == date_range_monthly[-1] and end_date.day >= 15:
            # Calculate interest for the last month based on days passed
            if investor.investment_count_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
            elif investor.investment_count_method == 'Daily 360':
                days_in_month = 30 - end_date.day
                monthly_rate = daily_360_rate * days_in_month
            monthly_interest_month = amount_invested * monthly_rate * (days_in_month / days_in_month)
        elif month == date_range_monthly[-1] and end_date.day < 15:
            # Calculate interest for the last month based on days passed
            if investor.investment_count_method == 'Daily 360':
                days_in_month = 30 - end_date.day
                monthly_interest_month = amount_invested * daily_360_rate * days_in_month
            else:
                monthly_interest_month = amount_invested * daily_rate * days_in_month
        else:
            days_in_month = calendar.monthrange(month.year, month.month)[1]
            if investor.investment_count_method == 'Daily':
                monthly_rate = daily_rate * days_in_month
            elif investor.investment_count_method == 'Daily 360':
                days_in_month = 30
                monthly_rate = daily_360_rate * days_in_month
            monthly_interest_month = amount_invested * monthly_rate * (days_in_month / days_in_month)

        data[month.strftime("%b-%Y")] = round(monthly_interest_month, 2)

        # if month.month not in [3, 6, 9, 12]:
        #     accumulated_interest += monthly_interest_month
        # else:
        #     amount_invested = amount_invested + accumulated_interest + monthly_interest_month
        #     accumulated_interest = 0
        amount_invested += monthly_interest_month

        quarter_name = "Q" + str((month.month - 1) // 3 + 1) + "-" + str(month.year)
        if quarter_name not in quarterly_interests:
            quarterly_interests[quarter_name] = 0

        if month == date_range_monthly[-1]:
            last_quarter_name = quarter_name
            last_quarter_interest += monthly_interest_month
        else:
            quarterly_interests[quarter_name] += monthly_interest_month

        # Add last quarter interest if it's in progress
    if last_quarter_name in quarterly_interests:
        quarterly_interests[last_quarter_name] += last_quarter_interest
    else:
        quarterly_interests[last_quarter_name] = last_quarter_interest

        # Add quarterly interests to data
    for quarter_name, quarterly_interest in quarterly_interests.items():
        data[quarter_name] = round(quarterly_interest, 2)

    data['Balance'] = sum([v for k, v in data.items() if k.startswith('Q')]) + data['Balance']

    return data


def update_spreadsheet(clients):
    all_data = []

    for investor in clients:
        if investor.investment_type == 'Reinvestment':
            data = reinvestment_calc(investor)
        elif investor.investment_type == 'Reinvestment Monthly':
            data = reinvestment_monthly_calc(investor)
        else:
            data = investment_calc(investor)
        all_data.append(data)

    df = pd.DataFrame(all_data)
    # df['Close date'] = df['Close date'].dt.strptime('%Y-%m-%d')
    df = df.fillna('')

    data_list = df.values.tolist()

    spreadsheet.clear()
    spreadsheet.resize(rows=1)
    spreadsheet.append_row(df.columns.tolist())
    spreadsheet.append_rows(data_list)


def get_investors_table(clients):
    all_data = []

    for investor in clients:
        if investor.investment_type == 'Reinvestment':
            data = reinvestment_calc(investor)
        elif investor.investment_type == 'Reinvestment Monthly':
            data = reinvestment_monthly_calc(investor)
        else:
            data = investment_calc(investor)
        all_data.append(data)

    df = pd.DataFrame(all_data)
    df = df.fillna('')

    data_json = df.to_json()
    return data_json
