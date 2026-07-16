from django.urls import path

from .views import FinalizeOrderCartView

urlpatterns = [path("finalize/", FinalizeOrderCartView.as_view())]
