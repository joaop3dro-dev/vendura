class CustomerError(Exception):
    pass


class AddressError(Exception):
    pass


class DeliveryAddressNotFoundError(AddressError):
    pass


class CustomerNotFoundError(CustomerError):
    pass
