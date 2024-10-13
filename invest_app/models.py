from django.db import models


class Client(models.Model):
    INVESTMENT_TYPE_CHOICES = [
        ('Direct Deposit', 'Direct Deposit'),
        ('Reinvestment', 'Reinvestment')
    ]

    INVESTMENT_COUNT_METHOD = [
        ('Monthly', 'Monthly'),
        ('Daily', 'Daily'),
        ('Daily 360', 'Daily 360')
    ]

    investor_id = models.CharField(max_length=100)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    company_name = models.CharField(max_length=100)
    investment_date = models.DateField()
    investment_rate = models.FloatField()
    investment_amount = models.FloatField()
    investment_type = models.CharField(max_length=15, choices=INVESTMENT_TYPE_CHOICES)
    investment_count_method = models.CharField(max_length=15, choices=INVESTMENT_COUNT_METHOD, default='Monthly')
    contract_end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.investor_id})"
