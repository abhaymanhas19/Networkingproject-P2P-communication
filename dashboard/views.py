from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from .models import Organization, CustomerOrganization, CustomerUsers

class OrganizationListView(LoginRequiredMixin, View):
    def get(self, request):
        organizations = Organization.objects.all()  # Query all organizations

        # Option 1: Using Django's built-in serializer (simplest)
        serialized_data = serializers.serialize("json", organizations)
        return JsonResponse(serialized_data, safe=False)


class UserCustomersListView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user

        customer_users = CustomerUsers.objects.filter(user=user).select_related('customer')
        customers = [cu.customer for cu in customer_users]
        serialized_data = serializers.serialize("json", customers)

        return JsonResponse(serialized_data, safe=False)

class CustomerOrganizationListView(LoginRequiredMixin, View):
    """returns list of organizations for a customer"""

    def get(self, request):
        customer_id = request.GET.get('customer_id')

        if not customer_id:
            return JsonResponse({"error": "customer_id is required"}, status=400)

        try:
            customer_organizations = CustomerOrganization.objects.filter(
                customer_id=customer_id
            ).select_related('organization')

            organizations = [co.organization for co in customer_organizations]
            serialized_data = serializers.serialize("json", organizations)

            return JsonResponse(serialized_data, safe=False)
        except CustomerOrganization.DoesNotExist:
            return JsonResponse({"error": "Customer not found"}, status=404)


#
