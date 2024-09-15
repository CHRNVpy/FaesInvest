from django.contrib import admin

from .models import Table, TableRow


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(TableRow)
class TableRowAdmin(admin.ModelAdmin):
    list_display = ('name', 'loan_id', 'table', 'investment_amount',
                  'interest_rate', 'investment_method', 'created', 'finished')
    list_filter = ('name', 'loan_id', 'table', 'investment_method')
    search_fields = ('table__name',)