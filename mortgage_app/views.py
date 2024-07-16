import datetime
import json

from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery, F, Max
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .dataframe import create_dataframe, update_allocations, merge_dataframes, update_spreadsheet
from .forms import PropertyForm, PropertyFundShareForm, FundForm
from .models import Property, Fund, PropertyFundShare, PropertyCostHistory


@login_required
def home(request):
    return render(request, 'mortgage_app/home.html')


@csrf_exempt
def loan_book(request):
    return render(request, 'mortgage_app/loan_book.html')


@csrf_exempt
def add_property(request):
    if request.method == 'POST':
        loan_id = request.POST.get('loan_id')
        name = request.POST.get('name')
        cost = request.POST.get('cost')
        date = request.POST.get('created')
        if not date:
            date = datetime.datetime.now()

        errors = []

        # Validate cost
        try:
            cost = float(cost)
        except ValueError:
            errors.append("Cost must be a number.")

        if errors:
            return render(request, 'mortgage_app/add_property.html', {
                'errors': errors,
                'loan_id': loan_id,
                'name': name,
                'cost': cost,
                'date': date
            })

        Property.objects.create(
            loan_id=loan_id,
            name=name,
            cost=cost,
            created=date
        )

        # Fetch the newly created Property object based on loan_id
        property_instance = Property.objects.get(loan_id=loan_id)

        # Create a PropertyCostHistory object associated with the newly created Property
        PropertyCostHistory.objects.create(
            property=property_instance,
            cost=cost,
            created=date
        )
        return render(request, 'mortgage_app/add_property.html', {
            'success': 'Property added successfully!',
            'loan_id': '',
            'name': '',
            'cost': '',
            'date': ''
        })

    return render(request, 'mortgage_app/add_property.html')


@login_required
def list_property(request):
    funds = Fund.objects.all()
    selected_fund_name = request.GET.get('fund_name')
    search_property_id = request.GET.get('search_property_id', '')

    if search_property_id:
        # Fetch properties by property ID
        properties = Property.objects.filter(loan_id__icontains=search_property_id)
    elif selected_fund_name:
        # Fetch properties associated with PropertyFundShare where fund name matches
        properties = Property.objects.filter(propertyfundshare__fund__name=selected_fund_name).order_by(
            '-loan_id').distinct()
    else:
        # Fetch all properties if no fund name or property ID is selected
        # properties = Property.objects.all().distinct('loan_id')
        # Annotate each Property with the maximum created date for its loan_id
        max_created_subquery = Property.objects.filter(
            loan_id=OuterRef('loan_id')
        ).values('loan_id').annotate(
            max_created=Max('created')
        ).values('max_created')

        # Filter the properties to keep only those with the maximum created date for their loan_id
        properties = Property.objects.annotate(
            max_created=Subquery(max_created_subquery)
        ).filter(
            created=F('max_created')
        )

    return render(request, 'mortgage_app/list_property.html', {
        'properties': properties,
        'funds': funds,
        'selected_fund_name': selected_fund_name,
        'search_property_id': search_property_id,
    })


@login_required()
def property_detail(request, loan_id):
    property = get_object_or_404(Property, loan_id=loan_id)
    funds = Fund.objects.all()
    selected_fund_name = request.GET.get('fund')
    history = PropertyCostHistory.objects.filter(property=property)

    latest_date_subquery = PropertyFundShare.objects.filter(
        property=property,
        fund=OuterRef('fund')
    ).order_by('-date_of_change').values('date_of_change')[:1]

    latest_shares = PropertyFundShare.objects.filter(
        property=property,
        date_of_change=Subquery(latest_date_subquery)
    )

    available_share = property.cost - sum([share.share_amount for share in latest_shares])

    context = {
        'property': property,
        'funds': funds,
        'selected_fund_name': selected_fund_name,
        'latest_shares': latest_shares,
        'available_share': available_share,
        'current_shares': latest_shares,
        'history': history,
        # 'csrf_token': request.COOKIES['csrftoken'],
    }

    if selected_fund_name:
        fund = get_object_or_404(Fund, name=selected_fund_name)
        all_shares = PropertyFundShare.objects.filter(fund=fund, property=property) \
            .annotate(loan_id=F('property__loan_id')) \
            .annotate(closed=F('property__closed'))
        df = create_dataframe([property])
        update_allocations(df, all_shares)
        df_json = df.to_json(index=False)
        json_data = json.loads(df_json)
        headers = list(json_data.keys())
        rows = zip(*[value.values() for value in json_data.values()])
        context['headers'] = headers
        context['rows'] = rows
        return render(request, 'mortgage_app/property_detail.html', context)

    return render(request, 'mortgage_app/property_detail.html', context)


@csrf_exempt
def close_contract(request, loan_id):
    if request.method == 'POST':
        property = get_object_or_404(Property, loan_id=loan_id)
        close_date = request.POST.get('contract_end_date')
        if close_date:
            # Assuming you have a field 'closed' in your Property model
            property.closed = close_date
            property.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Invalid date'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@csrf_exempt
def update_cost(request, loan_id):
    if request.method == 'POST':
        new_cost = request.POST.get('new_cost')
        date = request.POST.get('new_cost_date')
        if new_cost:
            try:
                new_cost = float(new_cost)
                print(new_cost)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid cost value.'})

            property = get_object_or_404(Property, loan_id=loan_id)
            property.cost = new_cost
            PropertyCostHistory.objects.create(property=property, cost=new_cost, created=date)
            property.save()
            return JsonResponse({'status': 'success', 'message': 'Cost updated successfully.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No cost provided.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


def add_fund(request):
    if request.method == 'POST':
        name = request.POST.get('name')

        errors = []

        # Validate name
        try:
            name = str(name)
        except ValueError:
            errors.append("Rate must be a string.")

        if errors:
            return render(request, 'mortgage_app/add_fund.html', {
                'errors': errors,
                'name': name,
            })

        Fund.objects.create(
            name=name,
        )

        return render(request, 'mortgage_app/add_fund.html', {
            'success': 'Fund added successfully!',
            'name': '',
        })

    return render(request, 'mortgage_app/add_fund.html')


class PropertyFundShareCreateView(View):
    def get(self, request):
        form = PropertyFundShareForm()
        return render(request, 'mortgage_app/property_fund_share_form.html', {'form': form})

    def post(self, request):
        form = PropertyFundShareForm(request.POST)
        if form.is_valid():
            form.save()
            context = {'form': form,
                       'success': 'Allocation successfull'}
            return render(request, 'mortgage_app/property_fund_share_form.html', context)
        return render(request, 'mortgage_app/property_fund_share_form.html', {'form': form})


@csrf_exempt
def get_property_info(request):
    property_id = request.GET.get('property_id')
    if property_id:
        property = Property.objects.get(pk=property_id)

        latest_date_subquery = PropertyFundShare.objects.filter(
            property=property,
            fund=OuterRef('fund')
        ).order_by('-date_of_change').values('date_of_change')[:1]

        latest_shares = PropertyFundShare.objects.filter(
            property=property,
            date_of_change=Subquery(latest_date_subquery)
        )

        latest_shares_json = [{'fund_name': share.fund.name,
                               'share_amount': share.share_amount,
                               'date': share.date_of_change} for share in latest_shares]

        available_share = property.cost - sum([share.share_amount for share in latest_shares])

        property_info = {'loan_id': property.loan_id,
                         'name': property.name,
                         'cost': property.cost,
                         'available_share': available_share,
                         'latest_shares': latest_shares_json,
                         'created': property.created,
                         'closed': property.closed}
        return JsonResponse(property_info)
    else:
        return JsonResponse({'error': 'No property_id provided'}, status=400)


@login_required
def list_shares(request):
    funds = Fund.objects.all()
    selected_fund_name = request.GET.get('fund')

    context = {
        'funds': funds,
        'selected_fund_name': selected_fund_name,
    }

    if funds:
        dataframes = []
        for fund in funds:
            properties = Property.objects.filter(propertyfundshare__fund__name=fund.name)
            shares = []
            for property in properties:
                all_shares = PropertyFundShare.objects.filter(fund=fund, property=property) \
                    .annotate(loan_id=F('property__loan_id')) \
                    .annotate(closed=F('property__closed'))

                shares.extend(list(all_shares))

            df = create_dataframe(properties)
            update_allocations(df, shares)
            df['fund_name'] = fund.name
            dataframes.append(df)

        merged_df = merge_dataframes(dataframes)
        df_json = merged_df.to_json(index=False)
        json_data = json.loads(df_json)

        headers = list(json_data.keys())
        rows = zip(*[value.values() for value in json_data.values()])

        context['headers'] = headers
        context['rows'] = rows

        if selected_fund_name:
            fund = get_object_or_404(Fund, name=selected_fund_name)
            properties = Property.objects.filter(propertyfundshare__fund__name=selected_fund_name)
            shares = []
            for property in properties:
                all_shares = PropertyFundShare.objects.filter(fund=fund, property=property) \
                    .annotate(loan_id=F('property__loan_id')) \
                    .annotate(closed=F('property__closed'))

                shares.extend(list(all_shares))

            df = create_dataframe(properties)
            update_allocations(df, shares)
            df.rename(columns={'loan_id': 'Loan ID', 'property_name': 'Property Name', 'cost': 'Cost'}, inplace=True)

            df_json = df.to_json(index=False)
            json_data = json.loads(df_json)

            headers = list(json_data.keys())
            rows = zip(*[value.values() for value in json_data.values()])

            context['headers'] = headers
            context['rows'] = rows
            return render(request, 'mortgage_app/fund_shares.html', context)

    return render(request, 'mortgage_app/fund_shares.html', context)


@login_required
@require_POST
def save_to_google_sheets(request):
    try:
        data = json.loads(request.body)
        selected_fund_name = data.get('fund')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

    if selected_fund_name:
        fund = get_object_or_404(Fund, name=selected_fund_name)
        properties = Property.objects.filter(propertyfundshare__fund__name=selected_fund_name)
        shares = []
        for property in properties:
            all_shares = PropertyFundShare.objects.filter(fund=fund, property=property) \
                .annotate(loan_id=F('property__loan_id')) \
                .annotate(closed=F('property__closed'))

            shares.extend(list(all_shares))

        df = create_dataframe(properties)
        update_allocations(df, shares)
        df.rename(columns={'loan_id': 'Loan ID', 'property_name': 'Property Name', 'cost': 'Cost'}, inplace=True)
    else:
        # If no fund is selected, use the merged dataframe
        funds = Fund.objects.all()
        dataframes = []
        for fund in funds:
            properties = Property.objects.filter(propertyfundshare__fund__name=fund.name)
            shares = []
            for property in properties:
                all_shares = PropertyFundShare.objects.filter(fund=fund, property=property) \
                    .annotate(loan_id=F('property__loan_id')) \
                    .annotate(closed=F('property__closed'))

                shares.extend(list(all_shares))

            df = create_dataframe(properties)
            update_allocations(df, shares)
            df['fund_name'] = fund.name
            dataframes.append(df)

        df = merge_dataframes(dataframes)

    try:
        update_spreadsheet(df)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
