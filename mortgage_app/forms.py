from django import forms
from .models import Property, PropertyFundShare, Fund


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['loan_id', 'name', 'cost']


class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ['name']


class PropertyFundShareForm(forms.ModelForm):
    class Meta:
        model = PropertyFundShare
        fields = ['property', 'fund', 'share_amount', 'share_rate', 'date_of_change']
        widgets = {
            'date_of_change': forms.DateInput(attrs={'type': 'date'})
        }
