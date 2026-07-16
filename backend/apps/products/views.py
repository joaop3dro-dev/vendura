from rest_framework import viewsets
from rest_framework.permissions import AllowAny, DjangoModelPermissions, IsAdminUser

from config.pagination import ProductCursorPagination

from .filters import ProductFilter
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


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
        return Product.objects.select_related("category").filter(public=True)


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]
    queryset = Category.objects.all()


class CategoryPublicViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    queryset = Category.objects.all()
