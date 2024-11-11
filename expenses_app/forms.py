from django import forms
from .models import Invoice

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'entity',
            'vendor_name',
            'invoice_number',
            'invoice_date',
            'invoice_file',
            'description',
            'expense_name',
            'dt_account',
            'cr_account',
            'invoice_amount',
            'number_of_months'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'entity': 'Entity Name',
            'invoice_number': 'Invoice #',
            'dt_account': 'Dt Account',
            'cr_account': 'Cr Account',
        }
