from rest_framework.pagination import CursorPagination, PageNumberPagination


class ProductCursorPagination(CursorPagination):
    page_size = 20
    ordering = "-id"


class OrderPageNumberPagination(PageNumberPagination):
    page_size = 10
