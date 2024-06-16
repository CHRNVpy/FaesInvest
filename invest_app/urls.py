from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', views.home, name='home'),
    path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),  # Redirect root to login
    path('add-client/', views.add_client, name='add_client'),
    path('list-clients/', views.list_clients, name='list_clients'),
    path('show-table/', views.show_table, name='show_table'),
    path('show-google-table/', views.show_google_table, name='show_google_table'),
]
