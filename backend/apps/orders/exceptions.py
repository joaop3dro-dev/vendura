class OrderError(Exception):
    pass


class OrderNotExists(OrderError):
    pass


class OrderCannotBeCancelledError(OrderError):
    pass
