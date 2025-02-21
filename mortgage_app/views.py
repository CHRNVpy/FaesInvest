import calendar
import csv
import datetime
import json

from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery, F, Max, Q
from django.db.models.functions import ExtractYear, ExtractMonth
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponse
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

    if funds:
        dataframes = []
        for fund in funds:
            # properties = Property.objects.filter(propertyfundshare__fund__name=fund.name)
            # shares = []
            # for property in properties:
            all_shares = PropertyFundShare.objects.filter(fund=fund, property=property) \
                .annotate(loan_id=F('property__loan_id')) \
                .annotate(closed=F('property__closed'))

            # shares.extend(list(all_shares))

            df = create_dataframe([property])
            update_allocations(df, list(all_shares))
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
            # properties = Property.objects.filter(propertyfundshare__fund__name=selected_fund_name)
            # shares = []
            # for property in properties:
            all_shares = PropertyFundShare.objects.filter(fund=fund, property=property) \
                .annotate(loan_id=F('property__loan_id')) \
                .annotate(closed=F('property__closed'))

            # shares.extend(list(all_shares))

            df = create_dataframe([property])
            update_allocations(df, list(all_shares))
            df.rename(columns={'loan_id': 'Loan ID', 'property_name': 'Property Name', 'cost': 'Cost'}, inplace=True)

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
        date_obj = datetime.datetime.strptime(close_date, '%m/%d/%Y')
        formatted_date = date_obj.strftime('%Y-%m-%d')
        if close_date:
            # Assuming you have a field 'closed' in your Property model
            property.closed = formatted_date
            property.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Invalid date'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


@csrf_exempt
def update_cost(request, loan_id):
    if request.method == 'POST':
        new_cost = request.POST.get('new_cost')
        date = request.POST.get('new_cost_date')
        date_obj = datetime.datetime.strptime(date, '%m/%d/%Y')
        formatted_date = date_obj.strftime('%Y-%m-%d')
        if new_cost:
            try:
                new_cost = float(new_cost)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid cost value.'})

            property = get_object_or_404(Property, loan_id=loan_id)
            property.cost = new_cost
            PropertyCostHistory.objects.create(property=property, cost=new_cost, created=formatted_date)
            property.save()
            return JsonResponse({'status': 'success', 'message': 'Cost updated successfully.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'No cost provided.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


@csrf_exempt
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
def list_shares_monthly(request):
    funds = Fund.objects.all()
    years = PropertyFundShare.objects.annotate(year=ExtractYear('date_of_change')).values('year').distinct()
    months = PropertyFundShare.objects.annotate(month=ExtractMonth('date_of_change')).values('month').distinct()
    sorted_months = sorted(months, key=lambda x: x['month'])
    named_months = [{'month': calendar.month_name[month['month']]} for month in sorted_months]
    selected_year = int(request.GET.get('year')) if request.GET.get('year') else None
    selected_month = request.GET.get('month')
    filter_ended_loan = request.GET.get('filter', 'false') == 'true'

    context = {
        'funds': funds,
        'years': years,
        'months': named_months,
        'selected_year': selected_year if selected_year else None,
        'selected_month': selected_month,
        'filter_ended_loan': filter_ended_loan
    }

    if selected_year and selected_month:
        month_number = list(calendar.month_name).index(selected_month.capitalize())
        previous_month = 12 if month_number == 1 else month_number - 1
        if filter_ended_loan:
            properties = Property.objects.filter(closed__isnull=False)
            print(properties)
        else:
            properties = Property.objects.all()
        extended_records = []

        for property in properties:
            # Include records from the previous year and the current year up to the previous month
            properties_shares = PropertyFundShare.objects.filter(
                Q(
                    Q(date_of_change__year=int(selected_year) - 1) |  # Previous year
                    Q(date_of_change__year=int(selected_year), date_of_change__month__lte=previous_month)
                    # Current year, previous months
                ),
                property=property
            ).order_by('fund_id', '-date_of_change')  # Order by fund_id and latest date

            # Dictionary to track whether to skip shares for a fund
            skip_fund = {}

            for share in properties_shares:
                # Check if we have already decided to skip this fund
                if share.fund_id in skip_fund:
                    continue

                # If the latest share amount for this fund is 0, mark this fund to be skipped
                if share.share_amount == 0:
                    skip_fund[share.fund_id] = True
                    continue  # Skip all shares from this fund

                # If this share is the first (latest) one and the share amount is not 0, add it to extended_records
                if share.fund_id not in skip_fund:
                    # Update the date_of_change for the share
                    share.date_of_change = share.date_of_change.replace(year=int(selected_year), month=month_number,
                                                                        day=1)
                    if property.closed and share.date_of_change > property.closed:
                        continue

                    extended_records.append(share)
                    skip_fund[share.fund_id] = False  # Mark this fund as processed

        if not filter_ended_loan:
            # Original records with the selected year and month
            records = list(PropertyFundShare.objects.filter(
                Q(date_of_change__year=selected_year) & Q(date_of_change__month=month_number)
            ).order_by('date_of_change'))

            # Extend the original records with the updated shares
            records.extend(extended_records)

            # You may want to sort the records again by date_of_change if needed
            records = sorted(records, key=lambda x: x.date_of_change)

            context['shares'] = records

        else:
            records = sorted(extended_records, key=lambda x: x.date_of_change)

            context['shares'] = records

    return render(request, 'mortgage_app/fund_shares_monthly.html', context)

@login_required
def available_shares(request):
    properties = Property.objects.all()

    valid_shares = []

    for property in properties:

        latest_date_subquery = PropertyFundShare.objects.filter(
            property=property,
            fund=OuterRef('fund')
        ).order_by('-date_of_change').values('date_of_change')[:1]

        latest_shares = PropertyFundShare.objects.filter(
            property=property,
            date_of_change=Subquery(latest_date_subquery)
        )

        available_share = property.cost - sum([share.share_amount for share in latest_shares])

        property_info = {'loan_id': property.loan_id,
                         'name': property.name,
                         'cost': property.cost,
                         'available_share': available_share,
                         'created': property.created,
                         'closed': property.closed}

        if available_share != 0:
            valid_shares.append(property_info)

    context = {'shares': valid_shares}

    return render(request, 'mortgage_app/available_shares.html', context)


@csrf_exempt
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


@csrf_exempt
def save_to_csv(request):
    selected_year = request.GET.get('year')
    selected_month = request.GET.get('month')

    # Fetch shares based on selected filters
    month_number = list(calendar.month_name).index(selected_month.capitalize())
    previous_month = 12 if month_number == 1 else month_number - 1
    properties = Property.objects.all()
    extended_records = []

    for property in properties:
        # Include records from the previous year and the current year up to the previous month
        properties_shares = PropertyFundShare.objects.filter(
            Q(
                Q(date_of_change__year=int(selected_year) - 1) |  # Previous year
                Q(date_of_change__year=int(selected_year), date_of_change__month__lte=previous_month)
                # Current year, previous months
            ),
            property=property
        ).order_by('fund_id', '-date_of_change')  # Order by fund_id and latest date

        # Dictionary to track whether to skip shares for a fund
        skip_fund = {}

        for share in properties_shares:
            # Check if we have already decided to skip this fund
            if share.fund_id in skip_fund:
                continue

            # If the latest share amount for this fund is 0, mark this fund to be skipped
            if share.share_amount == 0:
                skip_fund[share.fund_id] = True
                continue  # Skip all shares from this fund

            # If this share is the first (latest) one and the share amount is not 0, add it to extended_records
            if share.fund_id not in skip_fund:
                # Update the date_of_change for the share
                share.date_of_change = share.date_of_change.replace(year=int(selected_year), month=month_number,
                                                                    day=1)
                if property.closed and share.date_of_change > property.closed:
                    continue

                extended_records.append(share)
                skip_fund[share.fund_id] = False  # Mark this fund as processed

    # Original records with the selected year and month
    records = list(PropertyFundShare.objects.filter(
        Q(date_of_change__year=selected_year) & Q(date_of_change__month=month_number)
    ).order_by('date_of_change'))

    # Extend the original records with the updated shares
    records.extend(extended_records)

    # You may want to sort the records again by date_of_change if needed
    shares = sorted(records, key=lambda x: x.date_of_change)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="shares_data_{selected_year}_{selected_month}.csv"'

    # CSV writer
    writer = csv.writer(response)
    writer.writerow(['Date', 'Loan ID', 'Property Name', 'Fund', 'Amount'])

    for share in shares:
        writer.writerow([
            share.date_of_change,
            share.property.loan_id,
            share.property.name,
            share.fund.name,
            share.share_amount
        ])

    return response

def save_to_csv_available_shares(request):
    properties = Property.objects.all()

    valid_shares = []

    for property in properties:

        latest_date_subquery = PropertyFundShare.objects.filter(
            property=property,
            fund=OuterRef('fund')
        ).order_by('-date_of_change').values('date_of_change')[:1]

        latest_shares = PropertyFundShare.objects.filter(
            property=property,
            date_of_change=Subquery(latest_date_subquery)
        )

        available_share = property.cost - sum([share.share_amount for share in latest_shares])

        property_info = {'loan_id': property.loan_id,
                         'name': property.name,
                         'cost': property.cost,
                         'available_share': available_share,
                         'created': property.created,
                         'closed': property.closed}

        if available_share != 0:
            valid_shares.append(property_info)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="available_shares.csv"'

    # CSV writer
    writer = csv.writer(response)
    writer.writerow(['Loan ID', 'Property Name', 'Cost', 'Available Share', 'Created', 'Closed'])

    for share in valid_shares:
        writer.writerow([
            share['loan_id'],
            share['name'],
            share['cost'],
            share['available_share'],
            share['created'],
            share['closed']
        ])

    return response
