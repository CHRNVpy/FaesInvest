from django.db import models


class Client(models.Model):
    INVESTMENT_TYPE_CHOICES = [
        ('Direct Deposit', 'Direct Deposit'),
        ('Reinvestment', 'Reinvestment')
    ]

    investor_id = models.CharField(max_length=100)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    company_name = models.CharField(max_length=100)
    investment_date = models.DateField()
    investment_rate = models.FloatField()
    investment_amount = models.FloatField()
    investment_type = models.CharField(max_length=15, choices=INVESTMENT_TYPE_CHOICES)
    contract_end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.investor_id})"
