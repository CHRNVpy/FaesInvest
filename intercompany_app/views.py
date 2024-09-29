import json
import time

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from . import google_sheet
from .forms import TableForm, TableRowForm
from .models import Table, TableRow


@login_required
def home(request):
    return render(request, 'intercompany_app/home.html')

@csrf_exempt
def add_table(request):
    if request.method == 'POST':
        form = TableForm(request.POST)
        if form.is_valid():
            name_value = form.cleaned_data.get('name')
            form.save()  # Save the new company to the database
            google_sheet.create_new_sheet(name_value)
            return redirect('intercompany_app:home')  # Redirect to a list of companies after adding
    else:
        form = TableForm()

    return render(request, 'intercompany_app/add_table.html', {'form': form})

@login_required
def view_table(request):
    tables = Table.objects.all()
    selected_table_name = request.GET.get('company')

    context = {
        'company_tables': tables,
        'selected_company_name': selected_table_name,
    }

    if selected_table_name:
        total_investment = \
        TableRow.objects.filter(table_id__name=selected_table_name,
                                finished__isnull=True).aggregate(Sum('investment_amount'))[
            'investment_amount__sum']

        context['total_balance'] = total_investment

        rows = TableRow.objects.filter(table_id__name=selected_table_name).order_by('created')
        if rows:

            headers, rows = google_sheet.build_table(rows)

            context["company_table_data"] = True
            context["headers"] = headers
            context["rows"] = rows

    return render(request, 'intercompany_app/table_view.html', context)

@csrf_exempt
def add_transaction(request):
    selected_company_name = request.GET.get('company', '')

    if request.method == 'POST':
        form = TableRowForm(request.POST)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': form.errors})
    else:
        form = TableRowForm()

    # Get the table for the selected company
    table = Table.objects.filter(name=selected_company_name).first()
    if table:
        form.fields['table'].initial = table

    # Return only the form fields as HTML for the modal
    return render(request, 'intercompany_app/transaction_form_partial.html', {'form': form})

@csrf_exempt
def edit_finished_date(request):
    if request.method == 'POST':
        transaction_id = request.POST.get('transaction_id')
        print(transaction_id)
        finished_date = request.POST.get('finished')

        # Fetch and update the transaction
        try:
            transaction = TableRow.objects.get(id=transaction_id)
            transaction.finished = finished_date
            transaction.save()
            return JsonResponse({'success': True})
        except TableRow.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Transaction not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required()
def push_to_google_table(request):
    data = json.loads(request.body)
    if data.get('update', False):
        tables = Table.objects.all()
        try:
            for table in tables:
            # if selected_table_name:
                rows = TableRow.objects.filter(table_id__name=table.name)
                google_sheet.update_spreadsheet(rows, table.name)
                time.sleep(1)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})