from django.db import models

class Table(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class TableRow(models.Model):
    INVESTMENT_COUNT_METHOD = [
        ('Monthly', 'Monthly'),
        ('Daily', 'Daily'),
        ('Daily 360', 'Daily 360')
    ]

    name = models.CharField(max_length=255)
    loan_id = models.CharField(max_length=255, null=True, blank=True)
    gl_id = models.CharField(max_length=255, null=True, blank=True)
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='projects')
    investment_amount = models.DecimalField(max_digits=15, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    investment_method = models.CharField(max_length=15, choices=INVESTMENT_COUNT_METHOD, default='Monthly')
    created = models.DateField()
    finished = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name
