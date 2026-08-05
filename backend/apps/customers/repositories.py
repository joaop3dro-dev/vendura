from .exceptions import CustomerNotFoundError, DeliveryAddressNotFoundError
from .models import Address, Customer


class AddressRepository:
    @staticmethod
    def get_address_by_id(customer, address_id):
        try:
            address = Address.objects.get(
                pk=address_id,
                customer=customer,
            )
        except Address.DoesNotExist:
            raise DeliveryAddressNotFoundError("Endereço de entrega não encontrado")

        return {
            "street": address.street,
            "number": address.number,
            "neighborhood": address.neighborhood,
            "city": address.city,
            "state": address.state,
            "zip_code": address.zip_code,
        }


class CustomerRepository:
    @staticmethod
    def get_customer_by_user(user):
        try:
            return Customer.objects.get(user=user)
        except Customer.DoesNotExist:
            raise CustomerNotFoundError(
                "O perfil de cliente deste usuário não foi encontrado"
            )
