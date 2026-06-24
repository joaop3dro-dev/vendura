from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Store(models.Model):
    owner = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="store",
        verbose_name="Dono da Loja",
    )
    name = models.CharField(max_length=150, unique=True, verbose_name="Nome da Loja")
    description = models.CharField(blank=True)
    document = models.CharField(max_length=18, unique=True, verbose_name="CPF/CNPJ")
    is_active = models.BooleanField(default=True, verbose_name="Loja Ativa?")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
