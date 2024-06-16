import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from .models import Client
from .google_sheet import update_spreadsheet, get_investors_table


# from invest.pandas import update_spreadsheet


@login_required
def home(request):
    return render(request, 'home.html')


@login_required
def add_client(request):
    if request.method == 'POST':
        investor_id = request.POST.get('investor_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        company_name = request.POST.get('company_name')
        investment_date = request.POST.get('investment_date')
        investment_rate = request.POST.get('investment_rate')
        investment_amount = request.POST.get('investment_amount')
        investment_type = request.POST.get('investment_type')

        errors = []

        # Validate investment_rate
        try:
            investment_rate = float(investment_rate)
        except ValueError:
            errors.append("Investment rate must be a number.")

        # Validate investment_amount
        try:
            investment_amount = int(investment_amount)
        except ValueError:
            errors.append("Investment amount must be a number.")

        if errors:
            return render(request, 'add_client.html', {
                'errors': errors,
                'investor_id': investor_id,
                'first_name': first_name,
                'last_name': last_name,
                'company_name': company_name,
                'investment_date': investment_date,
                'investment_rate': investment_rate,
                'investment_amount': investment_amount,
                'investment_type': investment_type,
            })

        Client.objects.create(
            investor_id=investor_id,
            first_name=first_name,
            last_name=last_name,
            company_name=company_name,
            investment_date=investment_date,
            investment_rate=investment_rate,
            investment_amount=investment_amount,
            investment_type=investment_type,
        )

        return render(request, 'add_client.html', {
            'success': 'Client added successfully!',
            'investor_id': '',
            'first_name': '',
            'last_name': '',
            'company_name': '',
            'investment_date': '',
            'investment_rate': '',
            'investment_amount': '',
            'investment_type': '',
        })

    return render(request, 'add_client.html')


@login_required
def list_clients(request):
    clients = Client.objects.all()
    return render(request, 'list_clients.html', {'clients': clients})


@login_required
def show_table(request):
    clients = Client.objects.all()
    data = get_investors_table(clients)

    json_data = json.loads(data)

    headers = list(json_data.keys())
    rows = zip(*[value.values() for value in json_data.values()])

    context = {
        "headers": headers,
        "rows": rows,
    }
    return render(request, 'show_table.html', context)


@login_required()
def show_google_table(request):
    clients = Client.objects.all()
    update_spreadsheet(clients)

    return render(request, 'show_google_table.html')
