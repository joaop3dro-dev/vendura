class ProductError(Exception):
    pass


class InvalidProductError(ProductError):
    pass


class InsufficientStockError(ProductError):
    pass
