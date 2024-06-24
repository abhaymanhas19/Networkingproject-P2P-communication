import json
import logging
import pytz

from dateutil import parser
from datetime import datetime, timedelta
from dashboard import models as dashboard_models

from incontrol.client import API as PeplinkAPI
from meraki import DashboardAPI as MerakiAPI
from unifiapi import controller as UnifiCtrl

from django.conf import settings
from django.db.models import Q


_logger = logging.getLogger(__name__)

def sync_peplink_organizations():
    """syncs peplink organzations with dashboard Organizations"""

    api = PeplinkAPI(settings.PEPLINK_CLIENT_ID, settings.PEPLINK_CLIENT_SECRET)
    organizations = api.get_organizations()

    for org in organizations:
            dashboard_org, _ = dashboard_models.Organization.objects.get_or_create(
                name=org['name'],
                org_id=org['id'],
                org_type='P',
                org_url=org['url'],
                api_enabled=True
            )

def sync_meraki_organizations():
    """syncs meraki organizations with dashboard Organizations"""

    api = MerakiAPI(
        api_key=settings.MERAKI_API_KEY,
        base_url=settings.MERAKI_BASE_URL,
        output_log=False
    )
    organizations = api.organizations.getOrganizations()

    for org in organizations:
        dashboard_org, _ = dashboard_models.Organization.objects.get_or_create(
            org_id=org['id'],
            org_type='M'
        )
        dashboard_org.name = org['name']
        dashboard_org.api_enabled = org['api']['enabled']
        dashboard_org.org_type = 'M'
        dashboard_org.org_url = org['url']
        dashboard_org.save()


def sync_peplink_networks():
    """syncs peplink groups with dashboard Networks"""

    api = PeplinkAPI(settings.PEPLINK_CLIENT_ID, settings.PEPLINK_CLIENT_SECRET)
    organizations = api.get_organizations()

    for org in organizations:
        # if not org.api_enabled:
        #      continue
        peplink_groups = api.get_groups(org['id'])
        # print(networks)
        for group in peplink_groups:
            #dashboard_network = dashboard_models.Network.objects.filter(network_id=network['id']).first()
                dashboard_network, _ = dashboard_models.Network.objects.get_or_create(
                    name=group['name'],
                    network_id=group['id'],
                    # network_type='P',
                    organization=dashboard_models.Organization.objects.get(org_id=org['id'])
                )

                # print(network)
                # for k, v in network.items():
                #       print(f" {k}: {v}")

                dashboard_network.network_url = org['url']
                dashboard_network.timezone = group['timezone']
                dashboard_network.notes = group.get('notes','')
                dashboard_network.online_device_count = group['online_device_count']
                dashboard_network.offline_device_count = group['offline_device_count']
                dashboard_network.client_count = group['client_count']
                dashboard_network.country_code = group['country']
                dashboard_network.address = group['address']
                dashboard_network.latitude = group['latitude']
                dashboard_network.longitude = group['longitude']
                dashboard_network.custom_cert_perm = group['custom_cert_perm']
                dashboard_network.is_gps_tracking_disabled = group['is_gps_tracking_disabled']
                dashboard_network.is_suspend_config_update = group['is_suspend_config_update']
                dashboard_network.is_suspend_device_reporting = group['is_suspend_device_reporting']
                dashboard_network.is_suspend_live_status = group['is_suspend_live_status']
                dashboard_network.is_suspend_firmware_upgrade = group['is_suspend_firmware_upgrade']
                dashboard_network.favorite = group['favorite']
                dashboard_network.contenthub_threshold_enabled = group.get('contenthub_threshold_enabled','')
                dashboard_network.pepvpn_enabled = group['pepvpn_enabled']
                dashboard_network.pepvpn_refuse_legacy = group['pepvpn_refuse_legacy']
                dashboard_network.auto_portal_cert_update = group['auto_portal_cert_update']
                dashboard_network.contenthub_threshold = group['contenthub_threshold']
                dashboard_network.wan_disconnected_notify_time = group['wan_disconnected_notify_time']
                dashboard_network.is_low_data_usage_mode = group['is_low_data_usage_mode']

                dashboard_network.save()


def sync_meraki_networks():
    """syncs meraki networks with dashboard Networks"""

    api = MerakiAPI(
        api_key=settings.MERAKI_API_KEY,
        base_url=settings.MERAKI_BASE_URL,
        output_log=False
    )
    organizations = api.organizations.getOrganizations()
    #meraki_org_processed = 0
    for org in organizations:
        if not org['api'].get('enabled', True):
             continue
        # skip newly created organizations
        try:
            networks = api.organizations.getOrganizationNetworks(organizationId=org['id'], perPage=1000)
        except Exception as e:
            _logger.warn(f"Skipping syncing Meraki Networks due to API error: {e}")
            continue

        django_org = dashboard_models.Organization.objects.get(org_type='M', org_id=org['id'])
        for network in networks:

            dashboard_network, _ = dashboard_models.Network.objects.get_or_create(
                name=network['name'],
                network_id=network['id'],
                organization=django_org
            )

            dashboard_network.network_url = network['url']
            dashboard_network.timezone = network['timeZone']
            dashboard_network.notes = network.get('notes','')
            dashboard_network.product_types = json.dumps(network['productTypes'])
            dashboard_network.save()
        # meraki_org_processed += 1




def sync_peplink_groups():
    """syncs peplink networks with dashboard Networks"""

    api = PeplinkAPI(settings.PEPLINK_CLIENT_ID, settings.PEPLINK_CLIENT_SECRET)
    organizations = api.get_organizations()
    # print(len(organizations))
    # print(organizations)
    for org in organizations:
        groups = api.get_groups(org['id'])
        # print(groups)
        for group in groups:
            #dashboard_network = dashboard_models.Network.objects.filter(network_id=network['id']).first()
                peplink_group, _ = dashboard_models.PeplinkGroup.objects.get_or_create(
                    name=group['name'],
                    group_id=group['id'],
                    org_id=org['id'],
                    group_type='P'
                    #organization=dashboard_models.Organization.objects.get(org_id=org['id'])
                )
                # print("------------------------------------------------")
                # print(group)
                for k, v in group.items():
                      print(f" {k}: {v}")
                # print("------------------------------------------------")
                peplink_group.network_url = org['url']
                peplink_group.timezone = group['timezone']
                peplink_group.notes = group.get('notes','')
                peplink_group.online_device_count = group['online_device_count']
                peplink_group.offline_device_count = group['offline_device_count']
                peplink_group.client_count = group['client_count']
                peplink_group.country_code = group['country']
                peplink_group.address = group['address']
                peplink_group.latitude = group['latitude']
                peplink_group.longitude = group['longitude']
                peplink_group.custom_cert_perm = group['custom_cert_perm']
                peplink_group.is_gps_tracking_disabled = group['is_gps_tracking_disabled']
                peplink_group.is_suspend_config_update = group['is_suspend_config_update']
                peplink_group.is_suspend_device_reporting = group['is_suspend_device_reporting']
                peplink_group.is_suspend_live_status = group['is_suspend_live_status']
                peplink_group.is_suspend_firmware_upgrade = group['is_suspend_firmware_upgrade']
                peplink_group.favorite = group['favorite']
                peplink_group.contenthub_threshold_enabled = group.get('contenthub_threshold_enabled','')
                peplink_group.pepvpn_enabled = group['pepvpn_enabled']
                peplink_group.pepvpn_refuse_legacy = group['pepvpn_refuse_legacy']
                peplink_group.auto_portal_cert_update = group['auto_portal_cert_update']
                peplink_group.contenthub_threshold = group['contenthub_threshold']
                peplink_group.wan_disconnected_notify_time = group['wan_disconnected_notify_time']
                peplink_group.is_low_data_usage_mode = group['is_low_data_usage_mode']

                peplink_group.save()



def sync_peplink_group_devices(organization_id=None, group_id=None):
    """syncs peplink group devices with dashboard GroupDevices"""
    api = PeplinkAPI(settings.PEPLINK_CLIENT_ID, settings.PEPLINK_CLIENT_SECRET)

    if not api:
        _logger.warn("Skipping InControl Devices syncing due to previous ERROR.")
        return
    if not organization_id:
        organization_id = api._org_id

    group_devices = api.get_group_devices(organization_id=organization_id, group_id=group_id)

    for devices in group_devices:
        if devices is None:
            continue

        for device in devices:
            gd = dashboard_models.GroupDevice.objects.filter(device_id=device.get("id"))
            device_loc = api.get_device_location(organization_id, device.get("group_id"), device.get("id"))

            device_fields = [fld.name for fld in dashboard_models.GroupDevice._meta.get_fields()]

            dkeys = list(device.keys())
            for k in dkeys:
                if k not in device_fields:
                    device.pop(k, None)

            mdevice_id = device.pop('id')
            device['device_id'] = mdevice_id

            if device_loc:
                device["latitude"] = device_loc.get("latitude", 0.0)
                device["longitude"] = device_loc.get("longitude", 0.0)

                if device_loc.get("location_timestamp", None):
                    device["location_timestamp"] = parser.parse(device_loc.get("location_timestamp")+"+00:00")
            if gd:
                gd.update(**device)
            else:
                dashboard_models.GroupDevice.objects.create(**device)



def sync_meraki_devices():
    """syncs meraki networks with dashboard Networks"""

    api = MerakiAPI(
        api_key=settings.MERAKI_API_KEY,
        base_url=settings.MERAKI_BASE_URL,
        output_log=False
    )
    organizations = api.organizations.getOrganizations()
    # run_summary = {
    #     "org-id": {
    #         "network-id": {
    #             "device-id": 0
    #         }
    #     }
    # }
    # print("=====================================================")
    # print("===================== merkaki devices ===============")
    # print("=====================================================")
    for org in organizations:
        # skip API-disabled organizations

        # print(f"\n\n ==========>> ORGANIZATION: {org['id']}\n")
        if not org['api'].get('enabled', True):
            #  print(f"============== = = = = SKIPPING ORG {org['id']}")
             continue
        # run_summary[org['id']] = {}
        # skip newly created organizations:
        try:
            networks = api.organizations.getOrganizationNetworks(org['id'])
        except Exception as e:
            _logger.warn(f"Skipping syncing Meraki Devices due to API error: {e}")
            continue

        # get Organization's device statuses
        device_statuses = api.organizations.getOrganizationDevicesStatuses(org['id'], perPage=1000)

        django_org = dashboard_models.Organization.objects.get(org_type='M', org_id=org['id'])

        org_devices = api.organizations.getOrganizationDevices(org['id'])


        for network in networks:
            # print(f"\n=======Network: {network['name']}\n")
            # run_summary[org['id']][network['id']] = 0
            django_network = dashboard_models.Network.objects.get(network_id=network['id'])
            devices = api.networks.getNetworkDevices(network['id'])

            for device in devices:
                try:
                    dashboard_device = dashboard_models.MerakiDevice.objects.get(
                        serial=device['serial'],
                        networkId=device['networkId']
                    )
                except:
                    dashboard_device = dashboard_models.MerakiDevice()
                status = [s for s in device_statuses if s['serial'] == device['serial']]
                status_text = ""
                productType = ""
                publicIp = ""
                gateway = ""
                primaryDns = ""
                secondaryDns = ""
                if status:
                    status_text = status[0].get('status', '')
                    productType = status[0].get('productType', '')
                    publicIp = status[0].get('publicIp', '')
                    gateway = status[0].get('gateway', '')
                    primaryDns = status[0].get('primaryDns', '')
                    secondaryDns = status[0].get('secondaryDns', '')



                dashboard_device.status_text = status_text
                dashboard_device.status_list = status
                dashboard_device.publicIp = publicIp
                dashboard_device.gateway = gateway
                dashboard_device.primaryDns = primaryDns
                dashboard_device.secondaryDns = secondaryDns

                dashboard_device.productType = productType
                dashboard_device.network = django_network
                dashboard_device.serial = device['serial']
                dashboard_device.networkId = device['networkId']
                dashboard_device.url = network['url']
                dashboard_device.device_name = device.get('name', '')
                dashboard_device.serial = device['serial']
                dashboard_device.mac = device['mac']

                #dashboard_device.productType = device.get('productType', '')
                dashboard_device.lat = device['lat']
                dashboard_device.lng = device['lng']
                dashboard_device.model = device['model']
                dashboard_device.firmware = device['firmware']
                dashboard_device.wan1Ip = device.get('wan1Ip', '')
                dashboard_device.save()

                # run_summary[org['id']][network['id']] += 1

                meraki_network_device, _ = dashboard_models.MerakiNetworkDevice.objects.get_or_create(
                    network=django_network,
                    device=dashboard_device
                )
    # print("\n\nRun Summary:")
    # print(run_summary)

#TODO: sync unifi sites and devices
#TODO: add websocket service (django-channels)
# TODO: websocket endpoints to provide:
#       1) WAN status
#       2) Device status


def sync_unifi_sites():
    controller = UnifiCtrl(endpoint=settings.UNIFI_ENDPOINT_URL,
                           username=settings.UNIFI_USERNAME,
                           password=settings.UNIFI_PASSWORD,
                           verify=False)

    sites = controller.get('api/stat/sites')

    for site in sites:
        unifi_site, _  = dashboard_models.UnifiSite.objects.get_or_create(
            name=site['name'],
            _id=site['_id'],
            anonymous_id=site['anonymous_id']
        )
        unifi_site.desc = site.get('desc', '')
        unifi_site.num_new_alarms = site.get('num_new_alarms', 0)
        unifi_site.health = site.get('health', [])
        unifi_site.save()

def sync_unifi_devices():
    controller = UnifiCtrl(endpoint=settings.UNIFI_ENDPOINT_URL,
                           username=settings.UNIFI_USERNAME,
                           password=settings.UNIFI_PASSWORD,
                           verify=False)

    # sites = controller.get('api/stat/sites')
    sites = dashboard_models.UnifiSite.objects.all()


    for site in sites:
        # get devices
        devices = controller.get(f"/api/s/{site.name}/stat/device-basic")
        devices_full = controller.get(f"/api/s/{site.name}/stat/device")
        # https://13.92.211.202:8443/api/s/niowoodv/stat/device

        for device in devices:
            dvc = {}
            try:
                dvc_info = [info for info in devices_full if info['mac'] == device.get('mac','') ]
                dvc = dvc_info[0]
            except Exception as e:
                pass

            # If serial is not available in the API endpoint
            # we will just combine the device_id and MAC address
            serial_num = f"{dvc.get('_id','')}_{dvc.get('mac','')}"

            # import pdb;pdb.set_trace()
            unifi_device, _ = dashboard_models.UnifiDevice.objects.get_or_create(
                name=device.get('name', ''),
                mac=device['mac']
            )
            unifi_device.model=device['model']
            unifi_device.device_type=device['type']
            unifi_device.state=device['state']
            # import pdb;pdb.set_trace()
            unifi_device.in_gateway_mode=device['in_gateway_mode']
            unifi_device.disabled=device['disabled']
            unifi_device.serial=dvc.get('serial', serial_num)
            unifi_device.site = site
            unifi_device.save()



def sync_meraki_device_statuses():
    """
    A function that syncs Meraki device statuses with the dashboard Networks.
    It retrieves organizations, filters out API-disabled ones, fetches device statuses,
    iterates over networks and devices, creates device status records in the database,
    and deletes old device status records based on a data retention period.
    """


    api = MerakiAPI(
        api_key=settings.MERAKI_API_KEY,
        base_url=settings.MERAKI_BASE_URL,
        output_log=False
    )

    organizations = api.organizations.getOrganizations()
    fetch_time = datetime.now(tz=pytz.utc)
    for org in organizations:
        # skip API-disabled organizations
        if not org['api'].get('enabled', True):
             continue

        organization = dashboard_models.Organization.objects.filter(org_id=org['id']).first()
        # get the customer associated with the organization.
        # if org has no associated customer, we will try to get it from the network later
        org_customer =  organization.customer_set.all().first()

        try:
            networks = api.organizations.getOrganizationNetworks(org['id'])
        except Exception as e:
            _logger.warn(f"Skipping syncing Meraki Devices due to API error: {e}")
            continue

        # get Organization's device statuses
        device_statuses = api.organizations.getOrganizationDevicesStatuses(org['id'])
        org_devices = api.organizations.getOrganizationDevices(org['id'])

        for network in networks:
            customer = None
            if not org_customer:
                dashboard_network = dashboard_models.Network.objects.filter(network_id=network['id']).first()
                if dashboard_network:
                    try:
                        customer = dashboard_network.customernetwork_set.all().first().customer
                    except:
                        pass
            else:
                customer = org_customer

            if not customer:
                msg = f"\n\n=======>> skipping this network as it has no customer {network['id']}"
                #skip this network be cause it is not associated with a customer
                print(msg)
                _logger.warn(msg, exc_info=True)
                continue

            devices = api.networks.getNetworkDevices(network['id'])
            for device in devices:
                # find the device status from the statuses listpyt
                device_status = [ ds for ds in device_statuses if ds.get('serial','x') == device.get('serial','y') ]
                if not device_status:
                    msg = f"\n\n=======>> skipping this device as it has no status {device.get('serial','--no-serial--')}\n\n"
                    print(msg)
                    _logger.warn(msg, exc_info=True)
                    continue

                device_status = device_status[0]
                # print("================================================================")
                # print(device_status)
                # print("================================================================")

                last_reported_at = None
                try:
                    date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
                    last_reported_at = datetime.strptime(device_status.get('lastReportedAt', ''), date_format)
                except:
                    pass

                try:
                    # print("===================== D E V I C E ===========================================")
                    # print (device)
                    # print("================================================================")

                    wan_status = dashboard_models.DeviceStatus.objects.create(
                        customer=customer,
                        device_name=device.get('name', ''),
                        device_type='M',
                        status=device_status.get('status', ''),
                        network_id=device_status.get('networkId', ''),
                        serial=device_status.get('serial', ''),
                        product_type=device_status.get('productType', ''),
                        model=device_status.get('model',''),
                        mac=device_status.get('mac',''),
                        last_reported_at=last_reported_at,
                        as_of_time=fetch_time,
                        latitude=device.get('lat', None),
                        longitude=device.get('lng', None)
                    )
                except Exception as e:
                     _logger.warn(f"Device Status Not Created: {e}", exc_info=True)
    try:
        dashboard_models.DeviceStatus.objects.filter(as_of_time__lt=datetime.now(tz=pytz.utc) - timedelta(days=settings.DATA_RETENTION_DAYS)).delete()
    except Exception as e:
        _logger.warn(f"Device Status Not Deleted: {e}")



def sync_peplink_device_statuses():
    """
    A function that syncs peplink device statuses with the dashboard Networks.
    It retrieves organizations, filters out API-disabled ones, fetches device statuses,
    iterates over networks and devices, creates device status records in the database,
    and deletes old device status records based on a data retention period.
    """

    api = PeplinkAPI(settings.PEPLINK_CLIENT_ID, settings.PEPLINK_CLIENT_SECRET)

    if not api:
        _logger.warn("Skipping InControl Devices syncing due to previous ERROR.")
        return
    # if not organization_id:
    organization_id = api._org_id
    group_id = None
    group_devices = api.get_group_devices(organization_id=organization_id, group_id=group_id)

    fetch_time = datetime.now(tz=pytz.utc)
    api_group_devices = [devices for devices in group_devices if devices]
    #api_group_device_ids = [dev.get('id') for dev in api_group_devices if dev]

    api_group_device_ids = [dev.get('id') for sublist in api_group_devices for dev in sublist]

    # get all dashboard.models.GroupDevices that are not in group_devices list
    group_device_qset = dashboard_models.GroupDevice.objects.filter(~Q(device_id__in=api_group_device_ids))
    if  len(group_device_qset) == 0:
        _logger.info(f"======== sync_peplink_device_statuses: ALL GROUP DEVICES ARE IN SYNC  ========", exc_info=True)
    else:
        _logger.warn(f"======== sync_peplink_device_statuses: SOME GROUP DEVICES ARE NOT IN SYNC: {group_device_qset} ========", exc_info=True)

    for devices in group_devices:
        if not devices:
            continue

        dev = devices[0]
        customer = None
        try:
            customer_qset = dashboard_models.CustomerPeplinkGroup.objects.filter(group__group_id=dev['group_id']).first()
            if not customer_qset:
                print(f"customer not found for Peplink Group id={dev['group_id']}")
                continue
            customer = customer_qset.customer
        except Exception as e:
            print(f"got error: {e}")
            _logger.error(f"Error while getting Customer for CustomerPeplinkGroup:  {e}", exc_info=True)
            continue

        for device in devices:

            device_loc = (api.get_device_location(organization_id=organization_id,
                                                  group_id=device.get("group_id"),
                                                  device_id=device.get("id")))
            latitude = None
            longitude = None

            if device_loc:
                latitude = device_loc.get("latitude", None)
                longitude = device_loc.get("longitude", None)

            last_reported_at = None
            try:
                # get the last report timestamp
                # by comparing the device's 'last_online' and 'offline_at'
                last_online_time = datetime.fromisoformat(device.get('last_online', ''))
                offline_at = datetime.fromisoformat(device.get('offline_at', ''))
                if last_online_time > offline_at:
                    last_reported_at = last_online_time
                else:
                    last_reported_at = offline_at
            except:
                pass

            try:
                wan_status = dashboard_models.DeviceStatus.objects.create(
                    customer=customer,
                    device_name=device.get('name', ''),
                    device_type='P',
                    status=device.get('status', ''),
                    network_id=device.get('group_id', ''),
                    serial=device.get('sn', ''),
                    product_type=device.get('product_type', ''),
                    model=device.get('model',''),
                    # mac=device.get('mac',''),
                    last_reported_at=last_reported_at,
                    as_of_time=fetch_time,
                    latitude=latitude,
                    longitude=longitude,
                )
            except Exception as e:
                _logger.error(f"Device Status Not Created: {e}", exc_info=True)
    try:
        dashboard_models.DeviceStatus.objects.filter(as_of_time__lt=datetime.now(tz=pytz.utc) - timedelta(days=settings.DATA_RETENTION_DAYS)).delete()
    except Exception as e:
        _logger.error(f"Device Status Not Deleted: {e}", exc_info=True)


def sync_unifi_device_statuses():

    controller = UnifiCtrl(endpoint=settings.UNIFI_ENDPOINT_URL,
                           username=settings.UNIFI_USERNAME,
                           password=settings.UNIFI_PASSWORD,
                           verify=False)

    customer_sites = dashboard_models.CustomerUnifiSite.objects.all()

    fetch_time = datetime.now(tz=pytz.utc)

    STATUS = {0: "offline",
              1: "online",
              2: "pending adoption",
              4: "updating",
              5: "provisioning",
              6: "unreachable",
              7: "adopting",
              9: "adoption error",
              10: "adoption failed",
              11: "isolated"}

    for customer_site in customer_sites:
        customer = customer_site.customer
        site = customer_site.site

        devices = controller.get(f"/api/s/{site.name}/stat/device-basic")
        devices_full = controller.get(f"/api/s/{site.name}/stat/device")
        for device in devices:
            try:
                # find the matching mac in devices_full
                dvc = {}
                try:
                    dvc_info = [info for info in devices_full if info['mac'] == device.get('mac','') ]
                    dvc = dvc_info[0]
                except Exception as e:
                    pass

                device_status = dashboard_models.DeviceStatus.objects.create(
                    customer=customer,
                    device_name=device.get('name', ''),
                    device_type='U',
                    status=STATUS.get(device.get('state', 0), 'Unknown'),
                    network_id=site._id,
                    serial=dvc.get('serial', ''),
                    mac=device.get('mac',''),
                    product_type=device.get('type', ''),
                    model=device.get('model',''),
                    last_reported_at=fetch_time,
                    as_of_time=fetch_time,
                    latitude=None,
                    longitude=None,
                )
            except Exception as e:
                _logger.warn(f"Device Status Not Created: {e}", exc_info=True)
    try:
        dashboard_models.DeviceStatus.objects.filter(as_of_time__lt=datetime.now(tz=pytz.utc) - timedelta(days=settings.DATA_RETENTION_DAYS)).delete()
    except Exception as e:
        _logger.warn(f"Device Status Not Deleted: {e}")



            # unifi_device, _ = dashboard_models.UnifiDevice.objects.get_or_create(
            #     name=device.get('name', ''),
            #     mac=device['mac']
            # )
            # unifi_device.model=device['model']
            # unifi_device.device_type=device['type']
            # unifi_device.state=device['state']
            # # import pdb;pdb.set_trace()
            # unifi_device.in_gateway_mode=device['in_gateway_mode']
            # unifi_device.disabled=device['disabled']

            # unifi_device.site = site

def sync_all_data():

    sync_peplink_organizations()
    sync_peplink_groups()
    sync_peplink_group_devices()

    sync_meraki_organizations()
    sync_meraki_networks()
    sync_meraki_devices()

    sync_unifi_sites()
    sync_unifi_devices()

