from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import pandas as pd

from .forms import InvoiceForm
from .models import Invoice


@login_required
def home(request):
    return render(request, 'expenses_app/home.html')

@csrf_exempt
def add_invoice(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Save or process form data
            return redirect('expenses_app:add_invoice')
    else:
        form = InvoiceForm()

    return render(request, 'expenses_app/add_invoice.html', {'form': form})

@login_required
def list_invoices(request):
    invoices = Invoice.objects.all().order_by('invoice_date')

    invoices_with_months = []
    max_months_length = 0  # Initialize a variable to track the longest formatted_months list
    earliest_invoice_date = None

    for invoice in invoices:
        # Get the invoice date
        invoice_date = invoice.invoice_date

        # Use pandas to calculate the future months
        months = pd.date_range(invoice_date, periods=invoice.number_of_months, freq='MS')

        # Format the months as "Month Year" (e.g., "Jan 2024")
        formatted_months = [month.strftime('%b %Y') for month in months]

        # Update the max_months_length if the current invoice's months list is longer
        max_months_length = max(max_months_length, len(formatted_months))

        # Track the earliest invoice date to calculate the header months
        if earliest_invoice_date is None or invoice_date < earliest_invoice_date:
            earliest_invoice_date = invoice_date

        float_value = invoice.invoice_amount / invoice.number_of_months

        # Add the invoice data along with the month headers
        invoices_with_months.append({
            'invoice': invoice,
            'formatted_months': formatted_months,
            'monthly_amount': round(float_value, 2),
        })

    # Create the header row with months based on the earliest invoice date and max length
    header_months = [
        (earliest_invoice_date + pd.DateOffset(months=i)).strftime('%b %Y')
        for i in range(max_months_length)
    ]

    # Pass the data to the template
    return render(request, 'expenses_app/list_invoices.html',
                  {'invoices_with_months': invoices_with_months,
                   'header_months': header_months})