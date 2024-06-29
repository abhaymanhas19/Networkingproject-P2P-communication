
import json
import logging
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core import serializers
from django.db.models import Q
from django.db import connection
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from django.utils import timezone

from .models import (
    Customer,
    Organization,
    CustomerOrganization,
    CustomerUsers,
    GroupDevice,
    PeplinkGroup,
    DeviceStatus,
    MerakiDevice,
    UnifiDevice,
    StarlinkInfoHistory)

from .utils import get_customer_routers

_logger = logging.getLogger(__name__)

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


# class-based view that returns a list of devices locations
class DeviceLocationListView(LoginRequiredMixin, View):
    def get(self, request):
        # get the current_customer from the session
        current_customer = request.session.get('current_customer')
        # get the current customer's peplink groups
        customer = Customer.objects.get(id=current_customer.get('id'))
        #peplink_groups = customer.customer_peplink_groups.all()
        peplink_group_ids = customer.customer_peplink_groups.all().values_list('id', flat=True)
        # get the devices for the current_customer
        devices = GroupDevice.objects.filter(group_id__in=peplink_group_ids)
        return JsonResponse({"message": "Not implemented yet"})


class DeviceStatusChartView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        customer_id = request.GET.get('customer_id')
        interval = request.GET.get('interval', 'day')
        time_group = request.GET.get('time_group', 'day')

        if not customer_id:
            return JsonResponse({'error': 'customer_id is required'}, status=400)

        try:
            chart_data_json = DeviceStatus.get_median_device_status(customer_id, time_group)
            chart_data = json.loads(chart_data_json)

            return JsonResponse(chart_data)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)


class DeviceLocationHistoryView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        serial = request.GET.get('serial', None)
        # default to 30
        period_minutes = request.GET.get('period_minutes', 60*24*5)

        if not serial:
            return JsonResponse({'error': 'serial is required'}, status=400)

        try:
            period_minutes = int(period_minutes)
        except ValueError:
            # print("========ERROR: period_minutes must be an integer")
            _logger.warning(f'period_minutes must be an integer: {period_minutes}', exc_info=True)
            period_minutes = 30

        result = {
            "result": 0,
            "message": "",
            "times": [],
            "coordinates": [],
            "headings": [],
            "last_location": [],
            "device_info": {
                "serial": serial,
                "model": "",
                "mac": "",
                "last_reported_at": "",
                "name": "",
            },
        }

        n_minutes_ago = timezone.now() - timedelta(minutes=period_minutes)
        try:
            dev = (GroupDevice.objects.filter(sn=serial).first()
                   or MerakiDevice.objects.filter(serial=serial).first())
            if dev:
                device_name = ""
                device_serial = ""
                device_last_loc = []
                device_last_seen = ""
                device_model = ""

                if isinstance(dev, GroupDevice):
                    device_name = dev.name
                    device_last_loc = [dev.latitude, dev.longitude]
                    device_last_seen = dev.location_timestamp
                    device_model = dev.product_name
                    device_mac = dev.lan_mac
                elif isinstance(dev, MerakiDevice):
                    device_name = dev.device_name
                    device_last_loc = [dev.lat, dev.lng]
                    device_last_seen = dev.last_reported_at
                    device_model = dev.model
                    device_mac = dev.mac

                # print(f"=============got the {'Peplink' if isinstance(dev, GroupDevice) else 'Meraki'} record")
                result["device_info"]["model"] = device_model
                result["device_info"]["name"] = device_name
                result["device_info"]["mac"] = device_mac
                result["device_info"]["heading"] = ""
                result["device_info"]["last_reported_at"] = device_last_seen
                result["last_location"] = device_last_loc


            # print(f"Getting device location history for: {serial}")
            status_list = DeviceStatus.objects.filter(
                serial=serial,
                as_of_time__gte=n_minutes_ago,
            ).values_list('as_of_time', 'latitude', 'longitude', 'heading', 'device_name', 'mac', 'last_reported_at', 'model').order_by('as_of_time')
            #chart_data = json.loads(map_data_json)
            times = []
            coordinates = []
            headings = []
            last_location = []
            print(f"Got  {len(status_list)}  device location history for: {serial}")
            status_len = len(status_list)
            for idx, status in enumerate(status_list):
                if not status[1]:
                    return JsonResponse(result)

                times.append(status[0].strftime('%Y-%m-%d %H:%M:%S'))
                coordinates.append([status[1], status[2]])
                headings.append(status[3])

                if idx == status_len-1:
                    last_location = (status[1], status[2])
                    # print("===============GOT HERE")
                    result["last_location"] = last_location
                    result["device_info"] = {
                        "name": status[4],
                        "serial": serial,
                        "mac": status[5],
                        "last_reported_at": status[6].strftime('%Y-%m-%d %H:%M:%S'),
                        "heading": status[3],
                        "model": status[7]
                    }

            result["times"] = times
            result["coordinates"] = coordinates
            result["headings"] = headings
            result['result'] = 1


            return JsonResponse(result)
        except (ValueError, Exception) as e:
            # print("========>>>>>ERROR: ", e)
            _logger.error(e, exc_info=True)
            result["result"] = 0
            result["message"] = f"ERROR: {e}"
            return JsonResponse(result, status=400)



class DeviceDetailView(LoginRequiredMixin, TemplateView):
    template_name = "router_details.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        request  = self.request
        current_customer = request.session['current_customer']
        internal_class = kwargs.get('internal_class')
        device_serial = kwargs.get('serial')

        device = None
        if internal_class == 'meraki':
            device = MerakiDevice.objects.filter(serial=device_serial).first()
        elif internal_class == 'unifi':
            device = UnifiDevice.objects.filter(serial=device_serial).first()
        elif internal_class == 'peplink':
            device = GroupDevice.objects.filter(sn=device_serial).first()
        customer_id = current_customer.get('id')
        all_routers = get_customer_routers(customer_id)
        context['device'] = device
        return context


class StarlinkDataView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        internal_class = kwargs.get('internal_class')
        device_serial = kwargs.get('serial')
        data_type = kwargs.get('data_type')

        try:
            chart_data_json = StarlinkInfoHistory.get_starlink_chart_data(internal_class, device_serial, data_type)
            chart_data = json.dumps(chart_data_json)
            print(f"\n\n======================  {chart_data} \n\n")
            return JsonResponse(chart_data, safe=False)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)


