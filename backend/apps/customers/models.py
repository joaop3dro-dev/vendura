from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Customer(models.Model):
    class Status(models.TextChoices):
        ACTIVATE = "activate", "Ativo"
        DEACTIVATE = "deactivate", "Desativado"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer")
    phone = models.CharField(max_length=20)
    activate = models.CharField(
        choices=Status.choices, default=Status.ACTIVATE, max_length=20
    )

    class Meta:
        permissions = [("deactivate_customer", "Can deactivate customer")]


class Address(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="addresses"
    )
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=20)
    neighborhood = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip_code = models.CharField(max_length=9)

    @property
    def full_address(self):
        return f"{self.street}, {self.number}, {self.neighborhood}, {self.city}-{self.state}, CEP: {self.zip_code}"
