import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from . import google_sheet
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

    headers, rows = google_sheet.build_table(invoices)

    # Pass the data to the template
    return render(request, 'expenses_app/list_invoices.html',
                  {'headers': headers,
                   'rows': rows})

@login_required()
def push_to_google_table(request):
    data = json.loads(request.body)
    if data.get('update', False):
        invoices = Invoice.objects.all().order_by('invoice_date')
        try:
            google_sheet.update_spreadsheet(invoices)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})