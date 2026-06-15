from django.db import models
from models import Q


class Supplier(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField()

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="products"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(price__gt=0), name="product_price_positive"),
            models.CheckConstraint(check=Q(stock__gte=0), name="stock_non_negative"),
        ]

    def __str__(self):
        return self.name
