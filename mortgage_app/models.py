from django.db import models


class Property(models.Model):
    loan_id = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField(null=True, blank=True)
    closed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name


class Fund(models.Model):
    name = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name


class PropertyFundShare(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    share_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Store share in dollars
    date_of_change = models.DateTimeField()

    class Meta:
        unique_together = ('property', 'fund', 'date_of_change')

    def __str__(self):
        return f"{self.property.name} - {self.fund.name} - ${self.share_amount} on {self.date_of_change}"
