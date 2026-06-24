from rest_framework import viewsets
from rest_framework.permissions import AllowAny, DjangoModelPermissions

from apps.stores.permissions import IsSeller, IsSellerOwner
from config.pagination import ProductCursorPagination

from .filters import ProductFilter
from .models import Product
from .serializers import ProductSerializer


class ProductMixin:
    pagination_class = ProductCursorPagination
    filterset_class = ProductFilter


class ProductStaffViewSet(ProductMixin, viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("category")
    permission_classes = [DjangoModelPermissions]


class ProductPublicViewSet(ProductMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Product.objects.select_related("category", "store").filter(public=True)


class ProductSellerViewSet(ProductMixin, viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsSeller, IsSellerOwner]

    def get_queryset(self):
        return Product.objects.select_related("category", "store").filter(
            store=self.request.user.store
        )

    def perform_create(self, serializer):
        serializer.save(store=self.request.user.store)
