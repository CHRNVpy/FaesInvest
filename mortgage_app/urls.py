from django.urls import path
from . import views

app_name = 'mortgage_app'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('loan_book/', views.loan_book, name='loan_book'),
    path('property/add/', views.add_property, name='property_add'),
    path('property/list/', views.list_property, name='property_list'),
    path('property/<str:loan_id>/', views.property_detail, name='property_detail'),
    path('property/<str:loan_id>/close_contract/', views.close_contract, name='close_contract'),
    path('property/<str:loan_id>/update_cost/', views.update_cost, name='update_cost'),
    path('fund/add/', views.add_fund, name='fund_add'),
    path('property_fund_share/add/', views.PropertyFundShareCreateView.as_view(), name='property_fund_share_add'),
    path('get_property_info/', views.get_property_info, name='get_property_info'),
    path('fund_shares', views.list_shares, name='fund_shares'),
    path('fund_shares_monthly', views.list_shares_monthly, name='fund_shares_monthly'),
    path('save-to-google-sheets/', views.save_to_google_sheets, name='save_to_google_sheets'),
    path('save-to-csv/', views.save_to_csv, name='save_to_csv'),
]