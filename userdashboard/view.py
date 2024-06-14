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
from common.utils import calculate_device_status

from dashboard.models import (
    CustomerUsers,
    Customer,
    GroupDevice,
    MerakiDevice
)



def get_customer_devices(customer_id):

    customer_devices = None
    try:
        customer = Customer.objects.get(id=customer_id)
        # peplink_group_ids = customer.customer_peplink_groups.all().values_list('id', flat=True)
        peplink_group_ids = list(customer.customer_peplink_groups.all().values_list('group_id', flat=True))
        customer_devices = GroupDevice.objects.filter(group_id__in=peplink_group_ids)
    except Exception as e:
        pass
        print(f"error got: {e}")
    return customer_devices


# TODO: include the Peplink Routers
def get_wan_summary(customer_id):
    """get WAN summary from the database
    this assumes that the device records and synced at closed intervals
    """
    summary = {}
    try:
        customer = Customer.objects.get(id=customer_id)
        network_ids = list(customer.customernetwork_set.all().values_list('network', flat=True))
        meraki_appliances =  MerakiDevice.objects.filter(network_id__in=network_ids, productType='appliance')

        wan_status_summary = [ma.status_list[0] for ma in meraki_appliances if ma.status_list]
        offline_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="offline"]
        dormant_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="dormant"]
        online_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="online"]
        alerting_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="alerting"]
        # total_devices = len(wan_status_summary)

        total_online = len(online_devices)
        total_dormant = len(dormant_devices)
        total_offline = len(offline_devices)
        total_alerting = len(alerting_devices)

        status_summary = calculate_device_status(total_offline, total_alerting, total_online, total_dormant)

        summary["status_summary"] = status_summary
        summary["online_devices"] = online_devices
        summary["dormant_devices"] = dormant_devices
        summary["offline_devices"] = offline_devices
    except Exception as e:
        pass
        print(f"error got: {e}")

    return summary

#TODO: include the Peplink /Devices
def get_lan_summary(customer_id):
    """get LAN summary from the database
    this assumes that the device records and synced at closed intervals
    """
    summary = {}
    try:
        customer = Customer.objects.get(id=customer_id)
        network_ids = list(customer.customernetwork_set.all().values_list('network', flat=True))
        meraki_appliances =  MerakiDevice.objects.filter(network_id__in=network_ids, productType='switch')

        lan_status_summary = [ma.status_list[0] for ma in meraki_appliances if ma.status_list]
        offline_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="offline"]
        dormant_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="dormant"]
        online_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="online"]
        alerting_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="alerting"]

        total_devices = len(lan_status_summary)

        total_online = len(online_devices)
        total_dormant = len(dormant_devices)
        total_offline = len(offline_devices)
        total_alerting = len(alerting_devices)

        status_summary = calculate_device_status(total_offline, total_alerting, total_online, total_dormant)

        summary["status_summary"] = status_summary
        summary["online_devices"] = online_devices
        summary["dormant_devices"] = dormant_devices
        summary["offline_devices"] = offline_devices
    except Exception as e:
        pass
        print(f"error got: {e}")

    return summary



#TODO: include the Peplink /Devices
def get_wireless_summary(customer_id):
    """get WAN summary from the database
    this assumes that the device records and synced at closed intervals
    """
    summary = {}
    try:
        customer = Customer.objects.get(id=customer_id)
        network_ids = list(customer.customernetwork_set.all().values_list('network', flat=True))
        meraki_appliances =  MerakiDevice.objects.filter(network_id__in=network_ids, productType='wireless')

        wan_status_summary = [ma.status_list[0] for ma in meraki_appliances if ma.status_list]
        offline_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="offline"]
        dormant_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="dormant"]
        online_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="online"]
        alerting_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="alerting"]

        total_devices = len(wan_status_summary)

        total_online = len(online_devices)
        total_dormant = len(dormant_devices)
        total_offline = len(offline_devices)
        total_alerting = len(alerting_devices)

        status_summary = calculate_device_status(total_offline, total_alerting, total_online, total_dormant)
        summary["status_summary"] = status_summary
        summary["online_devices"] = online_devices
        summary["dormant_devices"] = dormant_devices
        summary["offline_devices"] = offline_devices
    except Exception as e:
        pass
        print(f"error got: {e}")

    return summary


def get_threats_summary(customer_id):

    summary = {}
    try:
        customer = Customer.objects.get(id=customer_id)
        network_ids = list(customer.customernetwork_set.all().values_list('network', flat=True))

    except:
        pass


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name="index.html"

    def get_context_data(self, **kwargs):
        customer_id = None
        context = super().get_context_data(**kwargs)
        user = self.request.user
        customer_users = CustomerUsers.objects.filter(user=user).select_related('customer')

        customers = [cu.customer for cu in customer_users]
        current_customer = {}
        context["current_customer"] = {}
        if 'current_customer' in self.request.session:
            current_customer = self.request.session['current_customer']
            context["current_customer"] = current_customer
        else:
            if customers:
                context["current_customer"] = customers[0].basic_info
                self.request.session['current_customer'] = customers[0].basic_info
                current_customer = self.request.session['current_customer']

        customer_id = int(current_customer.get("id", 0))
        # get customer's devices:
        devices = get_customer_devices(customer_id)
        print(f"devices for customer { current_customer['id']}: {devices}")
        context["customer_devices"] = devices
        context["customer_data"] = customers
        context["user_info"] = user
        context["wan_summary"] = get_wan_summary(customer_id)
        context["lan_summary"] = get_lan_summary(customer_id)
        context["wireless_summary"] = get_wireless_summary(customer_id)
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
