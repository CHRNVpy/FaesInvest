from django import forms

from .models import Table, TableRow


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['name']

class TableRowForm(forms.ModelForm):
    class Meta:
        model = TableRow
        fields = ['name', 'loan_id', 'gl_id', 'table', 'investment_amount',
                  'interest_rate', 'investment_method', 'created', 'finished']