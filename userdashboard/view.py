# LoginRequiredMixin here
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.http import JsonResponse
from django.views.generic.base import TemplateView
from django.views.generic import View
from django.contrib.auth.views import LogoutView

from django.utils.decorators import method_decorator


from dashboard.models import CustomerUsers, Customer, GroupDevice



def get_customer_devices(customer_id):

    customer_devices = None
    try:
        customer = Customer.objects.get(id=customer_id)
        peplink_group_ids = customer.customer_peplink_groups.all().values_list('id', flat=True)
        customer_devices = GroupDevice.objects.filter(group_id__in=peplink_group_ids)
    except Exception as e:
        pass
        print(f"error got: {e}")
    return customer_devices

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name="index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        customer_users = CustomerUsers.objects.filter(user=user).select_related('customer')

        customers = [cu.customer for cu in customer_users]

        context["current_customer"] = {}
        if 'current_customer' in self.request.session:
            current_customer = self.request.session['current_customer']
            context["current_customer"] = current_customer
        else:
            if customers:
                context["current_customer"] = customers[0].basic_info
                self.request.session['current_customer'] = customers[0].basic_info


        # get customer's devices:
        devices = get_customer_devices(int(current_customer["id"]))
        print(f"devices for customer { current_customer['id']}: {devices}")
        context["customer_devices"] = devices
        context["customer_data"] = customers
        context["user_info"] = user
        context["message"] = ""
        return context

class CustomLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        logout(request)
        return JsonResponse({'status': 'success'})

index_view = DashboardView.as_view()
logout_view = CustomLogoutView.as_view()




# class SetCurrentCustomerView(View):

    # @csrf_exempt
    # def post(self, request, *args, **kwargs):
    #     if request.is_ajax():
    #         # get customer_id from posted request
    #         customer_id = request.POST.get('current_customer_id')
    #         if customer_id:
    #             c = Customer.objects.get(id=customer_id)
    #             #self.request.session['current_customer'] = customers[0].basic_info
    #             request.session['current_customer'] = c.basic_info
    #         return JsonResponse({'message': 'Session variable set successfully!'})
    #     return JsonResponse({'error': 'Not an Ajax request'}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class SetCurrentCustomerView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            data = json.loads(request.body)
            customer_id = data.get('current_customer_id')

            if customer_id:
                try:
                    customer = Customer.objects.get(id=int(customer_id))
                    request.session['current_customer'] = customer.basic_info
                    return JsonResponse({'message': 'Session variable set successfully!'})
                except Customer.DoesNotExist:
                    return JsonResponse({'error': 'Customer not found'}, status=404)
            else:
                return JsonResponse({'error': 'Invalid customer ID'}, status=400)
        else:
            return JsonResponse({'error': 'Not an Ajax request'}, status=400)
