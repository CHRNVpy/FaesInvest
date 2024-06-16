from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
    'investor_id', 'first_name', 'last_name', 'company_name', 'investment_date', 'investment_rate', 'investment_amount',
    'investment_type')
    search_fields = ('investor_id', 'first_name', 'last_name', 'company_name')
    list_filter = ('investment_type', 'investment_date')

    fieldsets = (
        (None, {
            'fields': ('investor_id', 'first_name', 'last_name', 'company_name')
        }),
        ('Investment Details', {
            'fields': ('investment_date', 'investment_rate', 'investment_amount', 'investment_type')
        }),
    )
