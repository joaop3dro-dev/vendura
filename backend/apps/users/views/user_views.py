from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class UserManagementStaffView(APIView):
    permission_classes = [DjangoModelPermissions]
    serializer_class = UserSerializer
    queryset = User.objects.none()

    def get(self, request):
        users = User.objects.all()
        serializer = self.serializer_class(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk=None):
        if not pk:
            return Respose(
                {"detail": "O id do usuário deve ser fornecido na URL"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"error": "Usuário não encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        user.is_active = False
        user.save(
            update_fields=["is_active"]
        )  # Otimaliza o banco salvando apenas esta coluna

        return Response(
            {"detail": f"Usuário '{user.username}' desativado com sucesso."},
            status=status.HTTP_200_OK,
        )
