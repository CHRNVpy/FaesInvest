from django.urls import path
from expenses_app import views

app_name = 'expenses_app'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('add-invoice/', views.add_invoice, name='add_invoice'),
    path('list-invoice/', views.list_invoices, name='list_invoices'),
    path('save-to-google-sheets/', views.push_to_google_table, name='save_to_google_sheets'),
]
