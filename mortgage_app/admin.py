from django.contrib import admin
from .models import Property, Fund, PropertyFundShare, PropertyCostHistory


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'cost')


@admin.register(Fund)
class FundAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(PropertyFundShare)
class PropertyFundShareAdmin(admin.ModelAdmin):
    list_display = ('property', 'fund', 'share_amount', 'share_rate', 'date_of_change')
    list_filter = ('property', 'fund')
    search_fields = ('property__name', 'fund__name')


@admin.register(PropertyCostHistory)
class PropertyFundShareAdmin(admin.ModelAdmin):
    list_display = ('property', 'cost', 'created')
    list_filter = ('property',)
    search_fields = ('property__name',)
