import json
import logging
from dateutil import parser
from dashboard import models as dashboard_models

from incontrol.client import API as PeplinkAPI
from meraki import DashboardAPI as MerakiAPI
from django.conf import settings

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
            name=org['name'],
            org_id=org['id'],
            org_type='M',
            org_url=org['url'],
            api_enabled=org['api']['enabled']
        )


def sync_peplink_networks():
    """syncs peplink networks with dashboard Networks"""

    api = PeplinkAPI(settings.PEPLINK_CLIENT_ID, settings.PEPLINK_CLIENT_SECRET)
    organizations = api.get_organizations()
    print(len(organizations))
    print(organizations)
    for org in organizations:
        # if not org.api_enabled:
        #      continue
        networks = api.get_groups(org['id'])
        print(networks)
        for network in networks:
            #dashboard_network = dashboard_models.Network.objects.filter(network_id=network['id']).first()
                dashboard_network, _ = dashboard_models.Network.objects.get_or_create(
                    name=network['name'],
                    network_id=network['id'],
                    # network_type='P',
                    organization=dashboard_models.Organization.objects.get(org_id=org['id'])
                )

                print(network)
                for k, v in network.items():
                      print(f" {k}: {v}")

                dashboard_network.network_url = org['url']
                dashboard_network.timezone = network['timezone']
                dashboard_network.notes = network.get('notes','')
                dashboard_network.online_device_count = network['online_device_count']
                dashboard_network.offline_device_count = network['offline_device_count']
                dashboard_network.client_count = network['client_count']
                dashboard_network.country_code = network['country']
                dashboard_network.address = network['address']
                dashboard_network.latitude = network['latitude']
                dashboard_network.longitude = network['longitude']
                dashboard_network.custom_cert_perm = network['custom_cert_perm']
                dashboard_network.is_gps_tracking_disabled = network['is_gps_tracking_disabled']
                dashboard_network.is_suspend_config_update = network['is_suspend_config_update']
                dashboard_network.is_suspend_device_reporting = network['is_suspend_device_reporting']
                dashboard_network.is_suspend_live_status = network['is_suspend_live_status']
                dashboard_network.is_suspend_firmware_upgrade = network['is_suspend_firmware_upgrade']
                dashboard_network.favorite = network['favorite']
                dashboard_network.contenthub_threshold_enabled = network.get('contenthub_threshold_enabled','')
                dashboard_network.pepvpn_enabled = network['pepvpn_enabled']
                dashboard_network.pepvpn_refuse_legacy = network['pepvpn_refuse_legacy']
                dashboard_network.auto_portal_cert_update = network['auto_portal_cert_update']
                dashboard_network.contenthub_threshold = network['contenthub_threshold']
                dashboard_network.wan_disconnected_notify_time = network['wan_disconnected_notify_time']
                dashboard_network.is_low_data_usage_mode = network['is_low_data_usage_mode']

                dashboard_network.save()


def sync_meraki_networks():
    """syncs meraki networks with dashboard Networks"""

    api = MerakiAPI(
        api_key=settings.MERAKI_API_KEY,
        base_url=settings.MERAKI_BASE_URL,
        output_log=False
    )
    organizations = api.organizations.getOrganizations()

    for org in organizations:
        if not org['api'].get('enabled', True):
             continue
        networks = api.organizations.getOrganizationNetworks(org['id'])
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




def sync_peplink_groups():
    """syncs peplink networks with dashboard Networks"""

    api = PeplinkAPI(settings.PEPLINK_CLIENT_ID, settings.PEPLINK_CLIENT_SECRET)
    organizations = api.get_organizations()
    print(len(organizations))
    print(organizations)
    for org in organizations:
        groups = api.get_groups(org['id'])
        print(groups)
        for group in groups:
            #dashboard_network = dashboard_models.Network.objects.filter(network_id=network['id']).first()
                peplink_group, _ = dashboard_models.PeplinkGroup.objects.get_or_create(
                    name=group['name'],
                    group_id=group['id'],
                    org_id=org['id'],
                    group_type='P'
                    #organization=dashboard_models.Organization.objects.get(org_id=org['id'])
                )
                print("------------------------------------------------")
                print(group)
                for k, v in group.items():
                      print(f" {k}: {v}")
                print("------------------------------------------------")
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
    print(f"--------------------------> got {len(group_devices)} group_devices")
    for devices in group_devices:
        if devices is None:
            continue
        print(f"---------------------- -- - -> got {len(devices)} devices")
        for device in devices:
            gd = dashboard_models.GroupDevice.objects.filter(device_id=device.get("id"))
            device_loc = api.get_device_location(organization_id, device.get("group_id"), device.get("id"))
            # popping out attributes that are not in the Model
            device_fields = [fld.name for fld in dashboard_models.GroupDevice._meta.get_fields()]
            print(f"------------>> getting fields for device{device['name']} :{device_fields}")
            dkeys = list(device.keys())
            for k in dkeys:
                if k == 'starlink_status':
                     print("----------------------->> found starlink status")
                if k not in device_fields:
                    print(f"----------------------->> removing {k} from device")
                    device.pop(k, None)

            mdevice_id = device.pop('id')
            device['device_id'] = mdevice_id

            if device.get('starlink_status', None):
                 print(f"----------------------->> starlink status is {device['starlink_status']}")
            if device_loc:
                device["latitude"] = device_loc.get("latitude", 0.0)
                device["longitude"] = device_loc.get("longitude", 0.0)

                if device_loc.get("location_timestamp", None):
                    device["location_timestamp"] = parser.parse(device_loc.get("location_timestamp")+"+00:00")
            if gd:
                gd.update(**device)
            else:
                # gd_id = device.pop("id")
                # device["device_id"] = gd_id
                dashboard_models.GroupDevice.objects.create(**device)



def sync_meraki_devices():
    """syncs meraki networks with dashboard Networks"""

    api = MerakiAPI(
        api_key=settings.MERAKI_API_KEY,
        base_url=settings.MERAKI_BASE_URL,
        output_log=False
    )
    organizations = api.organizations.getOrganizations()

    for org in organizations:
        # skip API-disabled organizations
        if not org['api'].get('enabled', True):
             continue
        networks = api.organizations.getOrganizationNetworks(org['id'])
        django_org = dashboard_models.Organization.objects.get(org_type='M', org_id=org['id'])
        for network in networks:
            django_network = dashboard_models.Network.objects.get(network_id=network['id'])
            devices = api.networks.getNetworkDevices(network['id'])
            # devices_extra = api.networks.get
            for device in devices:
                print(f"----->> {device}")


                # dashboard_device, _ = dashboard_models.MerakiDevice.objects.get_or_create(
                #     serial=device['serial'],
                #     networkId=network['id']
                # )

                try:
                    dashboard_device = dashboard_models.MerakiDevice.objects.get(
                        serial=device['serial'],
                        networkId=device['networkId']
                    )
                except:
                    dashboard_device = dashboard_models.MerakiDevice()

                dashboard_device.network = django_network
                dashboard_device.serial = device['serial']
                dashboard_device.networkId = device['networkId']
                dashboard_device.url = network['url']
                dashboard_device.device_name = device.get('name', '')
                dashboard_device.serial = device['serial']
                dashboard_device.mac = device['mac']

                dashboard_device.productType = device.get('productType', '')
                dashboard_device.lat = device['lat']
                dashboard_device.lng = device['lng']
                dashboard_device.model = device['model']
                dashboard_device.firmware = device['firmware']
                dashboard_device.wan1Ip = device.get('wan1Ip', '')
                dashboard_device.save()
                # import pdb; pdb.set_trace()
                # dashboard_device.save(update_fields=['device_name', 'url', 'serial', 'mac', 'networkId', 'productType', 'lat', 'lng', 'model', 'firmware', 'wan1Ip'])
                # meraki_network_device, _ = dashboard_models.MerakiNetworkDevice.objects.get_or_create(
                #     network=django_network,
                #     device=dashboard_device
                # )
#TODO: sync unifi sites and devices
#TODO: add websocket service (django-channels)
# TODO: websocket endpoints to provide:
#       1) WAN status
#       2) Device status

def sync_all_data():

    sync_peplink_organizations()
    sync_peplink_groups()
    sync_peplink_group_devices()

    sync_meraki_organizations()
    sync_meraki_networks()
    sync_meraki_devices()

