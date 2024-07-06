import logging

from itertools import chain
from django.conf import settings

from incontrol.client import API as PeplinkAPI

from .models import Customer, MerakiDevice, GroupDevice, UnifiDevice


_logger = logging.getLogger(__name__)


def get_customer_routers(customer_id):

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

def calculate_device_status(offline_devices, alerting_devices, online_devices, dormant_devices):
    total_routers = offline_devices + alerting_devices + online_devices

    # Handle case with no routers
    if total_routers == 0:
        return ("None", "#808080")  # Gray
    if alerting_devices == 0 and offline_devices == 0  and online_devices == 0 and dormant_devices == total_routers:
        return ("Critical", "#FF0000")  # Red
    if alerting_devices == 0 and offline_devices == 0 and total_routers == online_devices:
        return ("Good", "#228B22")
    # Calculate percentages (safe to divide now since total_routers > 0)
    # Include dormant in offline
    offline_percent = ((offline_devices) / total_routers) * 100
    alerting_percent = (alerting_devices / total_routers) * 100
    online_percent = (online_devices / total_routers) * 100

    # Check for critical scenarios (all or most offline/dormant)
    if offline_percent == 100 or offline_percent > 50:
        return ("Critical", "#FF0000")  # Red

    # Determine if 'few' applies to offline and alerting
    few_offline = offline_percent <= 30
    few_alerting = alerting_percent <= 30

    # Categorize based on percentages (matching the new table)
    if online_percent == 100:
        return ("Good", "#228B22")  # Green
    elif online_percent > 50:
        if few_offline:
            return ("Good", "#228B22")  # Green
        else:
            return ("Fair", "#FFD700")  # Yellow
    else:
        if few_offline and few_alerting:
            return ("Fair", "#FFD700")  # Yellow
        else:
            return ("Poor", "#FFA500")  # Orange



def get_wan_summary(customer_id):
    """get WAN summary from the database
    this assumes that the device records and synced at closed intervals

    devices classified under WAN:
    - MerakiDevice.productType == 'appliance'
    - UnifiDevice.device_type in ['ugw', 'udm','uxg']

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
            msg = f"error getting peplink routers {e}"
            print(msg)
            _logger.warn(msg, exc_info=True)


        # get Unifi routers
        try:
            unifi_site_ids = list(customer.customerunifisite_set.all().values_list("site__id", flat=True))
            unifi_routers = UnifiDevice.objects.filter(site__in=unifi_site_ids, device_type__in=['ugw', 'udm','uxg'])
        except Exception as e:
            msg = f"error getting unifi routers {e}"
            print(msg)
            _logger.warn(msg, exc_info=True)


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
        msg = f"ERROR getting WAN Summary: {e}"
        print(msg)
        _logger.error(msg, exc_info=True)

    return summary


def get_peplink_device_data(device_id):
    try:
        api = PeplinkAPI(settings.PEPLINK_CLIENT_ID, settings.PEPLINK_CLIENT_SECRET)
        result = api.get_devices(has_status=True, device_ids=[device_id])
        return result
    except:
        _logger.error("ERROR getting peplink device data", exc_info=True)
        return []


def get_peplink_device_bandwidth(device_id):
    try:
        api = PeplinkAPI(settings.PEPLINK_CLIENT_ID, settings.PEPLINK_CLIENT_SECRET)
        result = api.get_bandwidth_per_device(device_ids=[device_id], type='monthly', report_date='2024-07')
        print("\n\n================================================ get_peplink_device_bandwidth\n\n")
        return result
    except:
        print("\n\n========== E R R O R ======================================= get_peplink_device_bandwidth\n\n")
        _logger.error("ERROR getting peplink device bandwidth", exc_info=True)
        return []
