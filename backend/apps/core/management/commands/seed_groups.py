from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from apps.coupon.models import Coupon
from apps.customer.models import Customer
from apps.order.models import Order, OrderItem
from apps.product.models import Product


class Command(BaseCommand):
    help = "Cria os grupos iniciais do Vendura com suas permissões"

    def handle(self, *args, **options):
        self._create_group_coupons()
        self._create_group_orders()
        self._create_group_stock()
        self._create_group_users()
        self.stdout.write(self.style.SUCCESS("Grupos criados com sucesso"))

    def _get_permissions(self, model, actions):
        ct = ContentType.objects.get_for_model(model)
        codenames = [f"{action}_{model.__name__.lower()}" for action in actions]
        return list(Permission.objects.filter(content_type=ct, codename__in=codenames))

    def _create_group_stock(self):
        group, _ = Group.objects.get_or_create(name="Estoque")

        permissions = self._get_permissions(Product, ["view", "add", "change"])

        group.permissions.set(permissions)

    def _create_group_orders(self):
        group, _ = Group.objects.get_or_create(name="Orders")

        permissions = self._get_permissions(Order, ["view"])

        permissions += self._get_permissions(OrderItem, ["view"])

        group.permissions.set(permissions)

    def _create_group_coupons(self):
        group, _ = Group.objects.get_or_create(name="Coupons")

        permissions = self._get_permissions(Coupon, ["add", "change", "view", "delete"])

        group.permissions.set(permissions)

    def _create_group_users(self):
        group, _ = Group.objects.get_or_create(name="User")

        permissions = self._get_permissions(Customer, ["view"])

        group.permissions.set(permissions)
