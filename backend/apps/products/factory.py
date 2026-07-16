import factory

from .models import Category, Product


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Categoria {n}")
    description = "Test description"


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f"Produto {n}")
    description = "Test description"
    price = 100
    stock = 10
    public = True
    category = factory.SubFactory(CategoryFactory)
