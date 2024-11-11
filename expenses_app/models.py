from django.db import models

# Entity model
class Entity(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Invoice model
class Invoice(models.Model):

    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='invoices')
    vendor_name = models.CharField(max_length=100)
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField()
    invoice_file = models.FileField(upload_to='invoices/')
    description = models.TextField(blank=True, null=True)
    expense_name = models.CharField(max_length=100)
    dt_account = models.CharField(max_length=100)
    cr_account = models.CharField(max_length=100)
    invoice_amount = models.DecimalField(max_digits=15, decimal_places=2)
    number_of_months = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.vendor_name}"

