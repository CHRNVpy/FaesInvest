import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import Client
from .google_sheet import update_spreadsheet, get_investors_table


# from invest.pandas import update_spreadsheet


@login_required
def home(request):
    return render(request, 'invest_app/home.html')


@csrf_exempt
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
        investment_count_method = request.POST.get('investment_count_method')

        errors = []

        # Validate investment_rate
        try:
            investment_rate = float(investment_rate)
        except ValueError:
            errors.append("Investment rate must be a number.")

        # Validate investment_amount
        try:
            investment_amount = float(investment_amount)
        except ValueError:
            errors.append("Investment amount must be a number.")

        if errors:
            return render(request, 'invest_app/add_client.html', {
                'errors': errors,
                'investor_id': investor_id,
                'first_name': first_name,
                'last_name': last_name,
                'company_name': company_name,
                'investment_date': investment_date,
                'investment_rate': investment_rate,
                'investment_amount': investment_amount,
                'investment_type': investment_type,
                'investment_count_method': investment_count_method
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
            investment_count_method=investment_count_method
        )

        return render(request, 'invest_app/add_client.html', {
            'success': 'Client added successfully!',
            'investor_id': '',
            'first_name': '',
            'last_name': '',
            'company_name': '',
            'investment_date': '',
            'investment_rate': '',
            'investment_amount': '',
            'investment_type': '',
            'investment_count_method': ''
        })

    return render(request, 'invest_app/add_client.html')


@login_required
def list_clients(request):
    filter_contract_end_date = request.GET.get('filter', 'false') == 'true'

    if filter_contract_end_date:
        clients = Client.objects.filter(contract_end_date__isnull=False)
    else:
        clients = Client.objects.all()

    return render(request, 'invest_app/list_clients.html', {
        'clients': clients,
        'filter_contract_end_date': filter_contract_end_date,
    })


@login_required()
def client_detail(request, client_id):
    client = Client.objects.get(id=client_id)
    return render(request, 'invest_app/client_detail.html', {'client': client})


@csrf_exempt
def close_contract(request, client_id):
    if request.method == 'POST':
        client = get_object_or_404(Client, id=client_id)
        end_date = request.POST.get('contract_end_date')
        if end_date:
            # Assuming you have a field 'contract_end_date' in your Client model
            client.contract_end_date = end_date
            client.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Invalid date'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


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
    return render(request, 'invest_app/show_table.html', context)


@login_required()
def show_google_table(request):
    clients = Client.objects.all()
    update_spreadsheet(clients)

    return render(request, 'invest_app/show_google_table.html')
