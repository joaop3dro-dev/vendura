from django.db import models
from django.db.models import Q
from stores.models import Store


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
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name="products")
    public = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(price__gt=0), name="product_price_positive"
            ),
            models.CheckConstraint(
                condition=Q(stock__gte=0), name="stock_non_negative"
            ),
        ]

    def __str__(self):
        return self.name
