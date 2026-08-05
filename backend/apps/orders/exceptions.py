class OrderError(Exception):
    pass


class OrderNotFoundError(OrderError):
    pass


class OrderCannotBeCancelledError(OrderError):
    pass
