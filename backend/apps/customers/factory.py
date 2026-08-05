import factory

from apps.users.factory import UserFactory

from .models import Address, Customer


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    user = factory.SubFactory(UserFactory)
    phone = "+5511999999999"


class AddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Address

    customer = factory.SubFactory(CustomerFactory)
    street = "Rua Teste"
    number = "123"
    neighborhood = "Centro"
    city = "São Paulo"
    state = "SP"
    zip_code = "01001-000"
