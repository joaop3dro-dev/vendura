from rest_framework import viewsets

from .models import Store
from .serializers import StoreSerializer


class StoreStaffViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StoreSerializer
    queryset = Store.objects.all()


class StoreSellerViewSet(viewsets.ModelViewSet):
    serializer_class = StoreSerializer

    def get_queryset(self):
        return Store.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
