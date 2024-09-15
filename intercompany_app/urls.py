from django.urls import path

from intercompany_app import views

app_name = 'intercompany_app'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('add_table/', views.add_table, name='add_table'),
    path('view_table/', views.view_table, name='view_table'),
    path('add_transaction/', views.add_transaction, name='add_transaction'),
    path('edit_finished_date/', views.edit_finished_date, name='edit_finished_date'),
    path('save_to_google_sheets/', views.push_to_google_table, name="save_to_google_sheets")
]