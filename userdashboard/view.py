# LoginRequiredMixin here
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.http import JsonResponse
from django.views.generic.base import TemplateView
from django.contrib.auth.views import LogoutView
from dashboard.models import CustomerUsers




class DashboardView(LoginRequiredMixin, TemplateView):
    template_name="index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user

        customer_users = CustomerUsers.objects.filter(user=user).select_related('customer')
        customers = [cu.customer for cu in customer_users]
        #serialized_data = serializers.serialize("json", customers)


        context["customer_data"] = customers

        context["user_info"] = user
        context["message"] = "this is from the dashboard view"

        return context

class CustomLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return JsonResponse({'status': 'success'})

index_view = DashboardView.as_view()
logout_view = CustomLogoutView.as_view()
