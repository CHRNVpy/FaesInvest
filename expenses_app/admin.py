from django.contrib import admin

from expenses_app.models import Entity, Invoice


@admin.register(Entity)
class TableAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Invoice)
class TableRowAdmin(admin.ModelAdmin):
    list_display = ('entity', 'vendor_name', 'invoice_number', 'invoice_date',
                  'invoice_amount')
    list_filter = ('entity__name', 'vendor_name', 'invoice_number', 'invoice_date')
    search_fields = ('invoice_number',)
