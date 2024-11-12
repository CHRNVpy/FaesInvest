import base64
import json
import os
from typing import List, Tuple, Dict, Any

import gspread
import pandas as pd
from dotenv import load_dotenv

from expenses_app.models import Invoice

load_dotenv()

encoded_service_account = os.getenv('GSPREAD_SERVICE_ACCOUNT') #GSPREAD_SERVICE_ACCOUNT

service_account_info = json.loads(base64.b64decode(encoded_service_account))

client = gspread.service_account_from_dict(service_account_info)

spreadsheet = client.open("Prepaid_exp") #Prepaid_exp


def build_table(invoices: List[Invoice], google=False) -> tuple[list[dict[str, list[Any] | Invoice | Any]], list[Any]]:
    all_data = []

    for invoice in invoices:
        data = {
            'Entity Name': invoice.entity.name,
            'Vendor Name': invoice.vendor_name,
            'Invoice Number': {'text': invoice.invoice_number, 'url': invoice.invoice_file.url},
            'Invoice Date': invoice.invoice_date,
            'Description': invoice.description,
            'Expense name': invoice.expense_name,
            'Dt Account': invoice.dt_account,
            'Cr Account': invoice.cr_account,
            'Amount': float(invoice.invoice_amount)
        }

        if google:
            data['Invoice Number'] = invoice.invoice_number

        months = pd.date_range(invoice.invoice_date, periods=invoice.number_of_months, freq='ME').to_period('M').to_timestamp()

        float_value = invoice.invoice_amount / invoice.number_of_months

        for month in months:
            data[month.strftime("%b-%Y")] = float(round(float_value, 2))

        all_data.append(data)

    df = pd.DataFrame(all_data)
    df['Invoice Date'] = pd.to_datetime(df['Invoice Date'])
    df['Invoice Date'] = df['Invoice Date'].dt.strftime("%b %d, %Y")

    df = df.fillna('')

    data_list = df.values.tolist()

    return df.columns.tolist(), data_list

def update_spreadsheet(data):

    headers, rows = build_table(data, google=True)

    sheet = spreadsheet.sheet1
    sheet.clear()
    sheet.resize(rows=1)
    sheet.append_row(headers)
    sheet.append_rows(rows)