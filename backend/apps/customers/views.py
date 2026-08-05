from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from .models import Address
from .repositories import CustomerRepository
from .serializers import AddressSerializer


class ListCreateAddressView(ListCreateAPIView):
    serializer_class = AddressSerializer
    queryset = Address.objects.all()

    def get_queryset(self):
        customer = CustomerRepository.get_customer_by_user(self.request.user)
        return Address.objects.filter(customer=customer)

    def perform_create(self, serializer):
        customer = CustomerRepository.get_customer_by_user(self.request.user)
        serializer.save(customer=customer)


class UpdateDestroyAddressView(RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    queryset = Address.objects.all()

    def get_queryset(self):
        customer = CustomerRepository.get_customer_by_user(self.request.user)
        return Address.objects.filter(customer=customer)
