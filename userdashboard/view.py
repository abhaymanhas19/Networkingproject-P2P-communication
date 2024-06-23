# LoginRequiredMixin here

import json
import logging
from datetime import timedelta, datetime
from itertools import chain

from django.conf import settings

from django.db.models import Max, F
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.http import JsonResponse
from django.views.generic.base import TemplateView
from django.views.generic import View
from django.contrib.auth.views import LogoutView
from django.utils import timezone
from django.utils.decorators import method_decorator

from merakiapi import helper

from common.utils import calculate_device_status

from dashboard.models import (
    CustomerUsers,
    Customer,
    GroupDevice,
    MerakiDevice,
    UnifiDevice,
    DeviceStatus
)

_logger = logging.getLogger(__name__)

def get_customer_devices(customer_id):

    combined_devices = []
    try:
        customer = Customer.objects.get(id=customer_id)
        # peplink_group_ids = customer.customer_peplink_groups.all().values_list('id', flat=True)
        peplink_group_ids = list(customer.customer_peplink_groups.all().values_list('group_id', flat=True))
        customer_devices = GroupDevice.objects.filter(group_id__in=peplink_group_ids)
        # include meraki devices
        customer_network_ids = list(customer.customernetwork_set.values_list('network__network_id', flat=True))
        meraki_appliances =  MerakiDevice.objects.filter(networkId__in=customer_network_ids, productType='appliance')
        combined_devices = list(chain(customer_devices, meraki_appliances))
    except Exception as e:
        print(f"======  get_customer_devices  ====>> error got: {e}")
    return combined_devices


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
        peplink_devices = []
        unifi_routers = []

        try:
             group_ids = list(customer.customer_peplink_groups.values_list("group_id", flat=True))
             peplink_devices = GroupDevice.objects.filter(group_id__in=group_ids)
        except Exception as e:
            print(f"error getting peplink routers {e}")

        # get Unifi routers
        try:
            unifi_site_ids = list(customer.customerunifisite_set.all().values_list("site__id", flat=True))
            print(f"================= got {unifi_site_ids} unifi site_ids")
            unifi_routers = UnifiDevice.objects.filter(site__in=unifi_site_ids, device_type__in=['ugw', 'udm','uxg'])
            #  group_ids = list(customer.customer_peplink_groups.values_list("group_id", flat=True))
            #  peplink_devices = GroupDevice.objects.filter(group_id__in=group_ids)
            print(f"================= got {len(unifi_routers)} unifi routers")
        except Exception as e:
            print(f"error getting unifi routers {e}")


        #wan_status_summary = [ma.status_list[0] for ma in meraki_appliances if ma.status_list]
        offline_devices = ([ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="offline"]
                           + [pd.status_list for pd in peplink_devices if pd.status_list and pd.status.lower()=="offline"]
                           + [ud.status_list for ud in unifi_routers if ud.status_list and ud.status.lower()=="offline"]
                           )

        dormant_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="dormant"]
        online_devices = ([ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="online"]
                          + [pd.status_list for pd in peplink_devices if pd.status_list and pd.status.lower()=="online"]
                          + [ud.status_list for ud in unifi_routers if ud.status_list and ud.status.lower()=="online"]
                          )
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
        summary["alerting_devices"] = alerting_devices
    except Exception as e:
        pass
        print(f"error got: {e}")

    return summary

def get_wan_summary2(customer_id):
    """get WAN summary from the database
    this assumes that the device records and synced at closed intervals
    """
    summary = {}
    try:
        customer = Customer.objects.get(id=customer_id)
        latest_device_statuses_filter = {}

        # if not settings.DEBUG:
        #     ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        #     latest_device_statuses_filter['as_of_time__gte'] = ten_minutes_ago
        # else:
        #     print("allowing old reccords to be used for uptime")

        latest_device_statuses = (
            DeviceStatus.objects
            .filter(
                customer_id=customer_id,
                product_type__in=['appliance', 'ugw', 'udm', 'uxg'],
                **latest_device_statuses_filter
            )
            .values('device_name', 'status','model', 'serial')
            .annotate(as_of_time=Max('as_of_time'))
            .filter(as_of_time=F('as_of_time'))
        )

        offline_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="offline"]
        dormant_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="dormant"]
        online_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="online"]
        alerting_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="alerting"]

        # print(f"======================GETTING LIST END ==========================")

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
        _logger.error(f"Error getting WAN summary: {e}", exc_info=True)

    return summary


def get_lan_summary2(customer_id):
    """get LAN summary from the database
    this assumes that the device records and synced at closed intervals
    """
    summary = {}
    try:
        customer = Customer.objects.get(id=customer_id)
        latest_device_statuses = (
            DeviceStatus.objects
            .filter(
                customer_id=customer_id,
                product_type__in=['switch', 'usw']
            )
            .values('device_name', 'status','model', 'serial')
            .annotate(as_of_time=Max('as_of_time'))
            .filter(as_of_time=F('as_of_time'))
        )
        print("======================latest_device_statuses==========================")
        print(f"{latest_device_statuses}")
        print("======================GETTING LIST==========================")

        offline_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="offline"]
        dormant_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="dormant"]
        online_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="online"]
        alerting_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="alerting"]

        print(f"======================GETTING LIST END ==========================")

        total_online = len(online_devices)
        total_dormant = len(dormant_devices)
        total_offline = len(offline_devices)
        total_alerting = len(alerting_devices)

        print("======================COUND STATUSES ==========================")
        status_summary = calculate_device_status(total_offline, total_alerting, total_online, total_dormant)

        summary["status_summary"] = status_summary
        summary["online_devices"] = online_devices
        summary["dormant_devices"] = dormant_devices
        summary["offline_devices"] = offline_devices
        summary["alerting_devices"] = alerting_devices
    except Exception as e:
        _logger.error(f"Error getting LAN summary: {e}", exc_info=True)

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
        unifi_devices = []
        try:
            unifi_site_ids = list(customer.customerunifisite_set.all().values_list("site__id", flat=True))
            unifi_devices = UnifiDevice.objects.filter(site__in=unifi_site_ids, device_type='usw')
        except Exception as e:
            print(f"error getting unifi switches {e}")

        offline_devices = ([ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="offline"]
                           + [ud.status_list for ud in unifi_devices if ud.status_list and ud.status.lower()=="offline"])
        dormant_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="dormant"]

        online_devices = ([ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="online"]
                           + [ud.status_list for ud in unifi_devices if ud.status_list and ud.status=="online"])

        alerting_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="alerting"]


        total_online = len(online_devices)
        total_dormant = len(dormant_devices)
        total_offline = len(offline_devices)
        total_alerting = len(alerting_devices)

        status_summary = calculate_device_status(total_offline, total_alerting, total_online, total_dormant)

        summary["status_summary"] = status_summary
        summary["online_devices"] = online_devices
        summary["dormant_devices"] = dormant_devices
        summary["offline_devices"] = offline_devices
        summary["alerting_devices"] = alerting_devices
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
        # include unifi uaps
        unifi_devices = []
        try:
            unifi_site_ids = list(customer.customerunifisite_set.all().values_list("site__id", flat=True))
            unifi_devices = UnifiDevice.objects.filter(site__in=unifi_site_ids, device_type='uap')
        except Exception as e:
            print(f"error getting unifi APs {e}")

        offline_devices = ([ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="offline"]
                           + [ud.status_list for ud in unifi_devices if ud.status_list and ud.status.lower()=="offline"])
        dormant_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="dormant"]
        online_devices = ([ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="online"]
                          + [ud.status_list for ud in unifi_devices if ud.status_list and ud.status.lower()=="online"])
        alerting_devices = [ma.status_list[0] for ma in meraki_appliances if ma.status_list and ma.status_text=="alerting"]
        # import pdb; pdb.set_trace()
        total_online = len(online_devices)
        total_dormant = len(dormant_devices)
        total_offline = len(offline_devices)
        total_alerting = len(alerting_devices)

        status_summary = calculate_device_status(total_offline, total_alerting, total_online, total_dormant)
        summary["status_summary"] = status_summary
        summary["online_devices"] = online_devices
        summary["dormant_devices"] = dormant_devices
        summary["offline_devices"] = offline_devices
        summary["alerting_devices"] = alerting_devices
    except Exception as e:
        _logger.error(f"Error getting wireless summary: {e}", exc_info=True)

    return summary


def get_wireless_summary2(customer_id):
    """get wireless summary from the database
    this assumes that the device records and synced at closed intervals
    """
    summary = {}
    try:
        customer = Customer.objects.get(id=customer_id)
        latest_device_statuses = (
            DeviceStatus.objects
            .filter(
                customer_id=customer_id,
                product_type__in=['uap', 'wireless']
            )
            .values('device_name', 'status','model', 'serial')
            .annotate(as_of_time=Max('as_of_time'))
            .filter(as_of_time=F('as_of_time'))
        )
        print("======================latest_device_statuses==========================")
        print(f"{latest_device_statuses}")
        print("======================GETTING LIST==========================")

        offline_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="offline"]
        dormant_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="dormant"]
        online_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="online"]
        alerting_devices = [dev for dev in latest_device_statuses if dev and dev['status']=="alerting"]

        print(f"======================GETTING LIST END ==========================")

        total_online = len(online_devices)
        total_dormant = len(dormant_devices)
        total_offline = len(offline_devices)
        total_alerting = len(alerting_devices)

        print("======================COUNTING STATUSES ==========================")
        status_summary = calculate_device_status(total_offline, total_alerting, total_online, total_dormant)

        summary["status_summary"] = status_summary
        summary["online_devices"] = online_devices
        summary["dormant_devices"] = dormant_devices
        summary["offline_devices"] = offline_devices
        summary["alerting_devices"] = alerting_devices
    except Exception as e:
        _logger.error(f"Error getting wireless summary: {e}", exc_info=True)

    return summary


def get_threats_summary(customer_id):
    summary = {"total": 0, "data":[]}
    try:
        mera = helper.Meraki()
        summary = mera.get_network_events_for_customer(customer_id)
    except:
        pass
    return summary


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
        # print(f"devices for customer { current_customer['id']}: {devices}")
        # print("==================>")
        # print(devices)
        # print("==================<")
        context["customer_devices"] = devices
        context["customer_data"] = customers
        context["user_info"] = user
        context["wan_summary"] = get_wan_summary(customer_id)
        context["lan_summary"] = get_lan_summary(customer_id)
        context["wireless_summary"] = get_wireless_summary(customer_id)
        context["threats_summary"] = get_threats_summary(customer_id)
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
