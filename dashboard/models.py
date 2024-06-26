import logging
import json


import pandas as pd
import pytz

from datetime import datetime, timedelta

from django.db import models, connection
from django.db.models import Count, Avg
from django.db.models.functions import TruncHour


from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
from django.utils.translation import gettext as _

from common.utils import calculate_heading


_logger = logging.getLogger(__name__)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)


class Organization(models.Model):

    PROVIDER_CHOICES = [
        ('P', 'Peplink'),
        ('M', 'Meraki'),
    ]
    name = models.CharField(max_length=255)
    org_id = models.CharField("Organization ID",  max_length=100)
    org_type = models.CharField("Organization Type", max_length=255, choices=PROVIDER_CHOICES, default='P')
    org_url = models.URLField("Organization URL", max_length=255, null=True, blank=True)
    api_enabled = models.BooleanField("Enable API", default=True)
    last_updated_at = models.DateTimeField("Last Updated At", auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True, null=True, blank=True)
    class Meta:
        unique_together = ('org_id', 'org_type')
        verbose_name = "Meraki/Peplink Organization"
        verbose_name_plural = "Meraki/Peplink Organizations"

    def __str__(self):
        organization_type = "Peplink" if self.org_type == 'P' else "Meraki"
        return f"{self.name} - [{organization_type}]"

class Customer(models.Model):
    name = models.CharField(max_length=255)

    # peplink_org = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    # meraki_org = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)

    contact_person = models.CharField(max_length=255, null=True, blank=True)
    contact_email = models.EmailField(max_length=255, null=True, blank=True)
    primary_contact_no = models.CharField(max_length=255, null=True, blank=True)
    secondary_contact_no = models.CharField(max_length=255, null=True, blank=True)
    organization = models.ManyToManyField(Organization, through='CustomerOrganization')
    # these are users who have access to Customer data
    users = models.ManyToManyField("auth.User", through="CustomerUsers", related_name="customers")
    customer_peplink_groups = models.ManyToManyField("dashboard.PeplinkGroup", through="CustomerPeplinkGroup", related_name="peplink_groups")
    meraki_networks = models.ManyToManyField("dashboard.Network", through="CustomerNetwork", related_name="meraki_networks")

    last_updated_at = models.DateTimeField("Last Updated At", auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True, null=True, blank=True)
    class Meta:
        verbose_name = "Customer Information"
        verbose_name_plural = "Customer Information"

    @property
    def initials(self):
        first_3_words = self.name.split(" ")[:3]
        initials = "".join([w[0] for w in first_3_words]).upper()
        return initials

    @property
    def basic_info(self):
        info = {}
        info["id"] = self.id
        info["name"] = self.name
        info["email"] = self.contact_email
        info["initials"] = self.initials
        return info
        # return json.dumps(info)

    def __str__(self):
        return self.name


class CustomerOrganization(models.Model):
    customer = models.ForeignKey("dashboard.Customer", on_delete=models.CASCADE)
    organization = models.ForeignKey("dashboard.Organization", on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Customer's Organizations"
        verbose_name = "Customer's Organization"

    def __str__(self):
        return self.customer.name


class CustomerUsers(models.Model):
    customer = models.ForeignKey("dashboard.Customer", on_delete=models.CASCADE)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Portal User"
        verbose_name_plural = "Customer's Portal Users"

    def __str__(self):
        name = ""
        # get the first name and last name for the user if it exists
        # if not just return the username

        if self.user:
            name = self.user.username
            if  self.user.first_name != "" and self.user.last_name != "":
                name = self.user.first_name + " " + self.user.last_name

        return name


class Network(models.Model):
    """Meraki Network"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField("Network Name", max_length=255)
    network_id = models.CharField("Network ID", max_length=100)
    network_url = models.URLField("Network URL", max_length=255, null=True, blank=True)
    # network_type = models.CharField("Network Type", max_length=2, choices=PROVIDER_CHOICES, default='P')
    timezone = models.CharField("Timezone", max_length=255, default="UTC")
    notes = models.TextField("Notes", null=True, blank=True, default="")
    product_types = models.CharField("Product Types", max_length=255, null=True, blank=True, default="[]")
    last_updated_at = models.DateTimeField("Last Updated At", auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True, null=True, blank=True)
    class Meta:
        unique_together = ('network_id', 'organization')
        verbose_name = "Meraki Network"
        verbose_name_plural = "Meraki Networks"

    def __str__(self):
        return f"{ self.name } - { self.organization.name }"


class PeplinkGroup(models.Model):
    """Model for Peplink Groups"""
    org_id = models.CharField("Peplink Organization ID", max_length=50, null=True, blank=True, default="")
    group_id = models.IntegerField("Peplink Group ID", null=True, blank=True, default="")
    name = models.CharField(max_length=255)
    online_device_count = models.IntegerField("Online Device Count", null=True, blank=True, default=0)
    offline_device_count = models.IntegerField("Offline Device Count", null=True, blank=True, default=0)
    client_count = models.IntegerField("Client Count", null=True, blank=True, default=0)
    expiry_count = models.IntegerField("Expiry Count", null=True, blank=True, default=0)
    expiry_soon_count = models.IntegerField("Expiry Soon Count", null=True, blank=True, default=0)
    group_type = models.CharField("Group Type", max_length=2, null=True, blank=True, default= 'peplink')
    country_code = models.CharField("Country Code", max_length=4, null=True, blank=True, default="")
    timezone = models.CharField("Timezone", max_length=255, default="UTC")
    address = models.CharField("Address", max_length=255, null=True, blank=True, default="")

    latitude = models.DecimalField("Latitude", max_digits=12, decimal_places=8, null=True, blank=True, default=0)
    longitude = models.DecimalField("Longitude", max_digits=12, decimal_places=8, null=True, blank=True, default=0)
    custom_cert_perm = models.BooleanField("Custom Cert Perm", default=False)
    is_gps_tracking_disabled = models.BooleanField("GPS Tracking Disabled", default=False)
    is_suspend_config_update = models.BooleanField("Suspend Config Update", default=False)
    is_suspend_device_reporting = models.BooleanField("Suspend Device Reporting", default=False)
    is_suspend_live_status = models.BooleanField("Suspend Live Status", default=False)
    is_suspend_firmware_upgrade = models.BooleanField("Suspend Firmware Upgrade", default=False)
    favorite = models.BooleanField("Favorite", default=False)
    contenthub_threshold_enabled = models.BooleanField("Contenthub Threshold Enabled", default=False)
    pepvpn_enabled = models.BooleanField("Pepvpn Enabled", default=False)
    pepvpn_refuse_legacy = models.BooleanField("Pepvpn Refuse Legacy", default=False)
    auto_portal_cert_update = models.BooleanField("Auto Portal Cert Update", default=False)
    contenthub_threshold = models.IntegerField("Contenthub Threshold", default=0)
    wan_disconnected_notify_time = models.IntegerField("Wan Disconnected Notify Time", default=0)
    is_low_data_usage_mode = models.BooleanField("Low Data Usage Mode", default=False)
    gps_location_sampling = models.IntegerField("GPS Location Sampling", default=2)
    min_heartbreak_interval = models.IntegerField("Min Heartbreak Interval", default=0)
    customer = models.ForeignKey(Customer, related_name="peplink_groups", on_delete=models.CASCADE, null=True,blank=True)
    last_updated_at = models.DateTimeField("Last Updated At", auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('org_id', 'group_id')
        verbose_name = "Peplink Group"
        verbose_name_plural = "Peplink Groups"

    def __str__(self):
        return self.name



class GroupDevice(models.Model):
    device_id = models.IntegerField("Device ID",
            help_text="unique identifier of the device",
            unique=True)
    group_id = models.IntegerField(
            "Group ID",
            help_text="unique identifier of the group,",
            default=0)
    group_name = models.CharField(
            _("Group Name"),
            help_text="Name of the group",
            max_length=150, null=True, blank=True)
    sn = models.CharField(
            _("S/N"),
            help_text="Device S/N",
            max_length=150, null=True, blank=True)
    name = models.CharField(
            _("Device name"),
            help_text="Device name",
            max_length=150,
            null=True, blank=True)
    status = models.CharField(
            _("Status"),
            help_text="Status",
            max_length=150,
            null=True, blank=True)
    product_id = models.IntegerField(
            _("Product ID"),
            default=0,
            help_text="Product ID")
    client_count = models.IntegerField(
            _("Client Count"),
            help_text="Current client count",
            default=0)
    fw_ver = models.CharField(
            _("Firmware"),
            help_text="Firmware version using",
            max_length=150,
            null=True, blank=True)
    last_online = models.CharField(
            _("Last Online"),
            help_text="Last online date and time",
            max_length=150,
            null=True, blank=True)
    offline_at = models.CharField(
            _("Last Offline"),
            help_text="Last offline date and time",
            max_length=150,
            null=True, blank=True)
    first_appear = models.CharField(
            _("First Appeared"),
            help_text="First appeared date and time",
            max_length=150,
            null=True, blank=True)
    lan_mac = models.CharField(
            _("LAN MAC"),
            help_text="LAN MAC address",
            max_length=150,
            null=True, blank=True)
    sp_default = models.BooleanField(
            _("SP Default"),
            help_text="SP Default",
            default=False)
    interfaces = ArrayField(
            models.CharField(
                max_length=10000,
                blank=True,
                null=True),
            blank=True,
            null=True,
            verbose_name="Device interfaces",
            help_text="Device interfaces")
    starlink_status = ArrayField(
            models.CharField(
                max_length=10000,
                blank=True,
                null=True),
            blank=True,
            null=True,
            verbose_name="Starlink Status",
            help_text="Starlink Status")
    product_name = models.CharField(
            _("Product Name"),
            help_text="Product name",
            max_length=150,
            null=True, blank=True)
    address = models.CharField(
            _("Address"),
            help_text="Address",
            max_length=150,
            null=True, blank=True)
    expiry_date = models.CharField(
            _("Expiry Date"),
            help_text="Warranty expiry date",
            max_length=150,
            null=True, blank=True)
    gps_support = models.BooleanField(
            _("GPS Support"),
            help_text="GPS Support",
            default=False)
    gps_exist = models.BooleanField(
            _("GPS Support"),
            help_text="GPS Support",
            default=False)
    expired = models.BooleanField(
            _("Expired"),
            help_text="Is Expired",
            default=False)
    hw_expired = models.BooleanField(
            _("HW Expired"),
            help_text="HW Expired",
            default=False)
    support_ssid_count = models.IntegerField(
            _("Supported SSID Count"),
            help_text="Supported number of SSIDs",
            default=1)
    extap_proxy_supported = models.BooleanField(
            _("extap_proxy_supported"),
            help_text="extap_proxy_supported",
            default=False)
    extap_proxy_enabled = models.BooleanField(
            _("extap_proxy_enabled"),
            help_text="extap_proxy_enabled",
            default=False)
    wlan_probe_supported = models.BooleanField(
            _("wlan_probe_supported"),
            help_text="wlan_probe_supported",
            default=False)
    wlan_probe_enabled = models.BooleanField(
            _("wlan_probe_enabled"),
            help_text="wlan_probe_enabled",
            default=False)
    low_data_usage_mode = models.BooleanField(
            _("low_data_usage_mode"),
            help_text="low_data_usage_mode",
            default=False)
    group_type = models.CharField(_("Group type"), max_length=50, null=True, blank=True)
    device_type = models.CharField(_("Device type"), max_length=50, null=True, blank=True)
    last_sync_date = models.CharField(_("last_sync_date"), max_length=50, null=True, blank=True)
    uptime = models.IntegerField("Device up time", default=0)
    uptime_appear = models.CharField(
            _("Uptime Appear"),
            help_text="Retrieval time of the device up time",
            max_length=150,
            null=True,
            blank=True)
    pepvpn_peers = models.IntegerField(
            _("PEP VPN Peers Count"),
            help_text="PEP VPN Peers Count",
            default=0)
    wifi_cfg = models.CharField(
            _("WiFi Config"),
            help_text="WiFi Configuration",
            max_length=150,
            null=True,
            blank=True)
    ddns_enabled = models.BooleanField(
            _("DDNS Enabled"),
            help_text="Is DDNS Enabled",
            default=False)
    onlineStatus = models.CharField(
            _("Online Status"),
            max_length=50,
            default='offline',
            help_text="Current online status")
    wtp_ip = models.CharField(
            _("WTP IP"),
            max_length=50,
            default='',
            help_text="WTP IP")
    hd_version = models.CharField(
            _("Hardware version"),
            default='',
            max_length=150,
            help_text="Hardware version")
    hardware_version = models.CharField(
            _("Hardware version"),
            default='',
            max_length=150,
            help_text="Hardware version")
    mvpn_version = models.CharField(
            _("MVPN version"),
            default='',
            max_length=1000,
            help_text="MVPN version")
    site_id = models.CharField(
            _("Site ID"),
            default='',
            max_length=250,
            help_text="Site ID")
    is_ap_schedule_enabled = models.BooleanField(
            _("AP Schedule Enabled"),
            help_text="Is DDNS Enabled",
            default=False)
    gobi_sim_lock_supported = models.BooleanField(
            _("GOBI SIM lock Support"),
            help_text="Is GOBI SIM lock Supported",
            default=False)

    # location attributes, updated separately
    # though the device location endpoint
    location_timestamp = models.DateTimeField(
            _("Location Timestamp"),
            help_text="Last known location timestamp",
            null=True, blank=True)

    latitude = models.FloatField(
            _("Latitude"),
            default=0.0,
            help_text="Last known location (Latitude)")

    longitude = models.FloatField(
            _("Longitude"),
            default=0.0,
            help_text="Last known location (Longitude)")

    last_updated_at = models.DateTimeField("Last Updated At", auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True, null=True, blank=True)
    internal_class = models.CharField("Internal Classification", help_text="Automatically Set by DataSync Process", null=True, blank=True, default="", max_length=255)

    class Meta:
        verbose_name = "Peplink Group Device"
        verbose_name_plural = "Peplink Group Devices"

    def __str__(self):
        return "{} ({})".format(self.name, self.sn)

    @property
    def last_reported_at(self):
        last_reported = None

        last_offline_date =  datetime(1970, 1, 1)
        last_online_date =  datetime(1970, 1, 1)
        try:
            last_offline_date = datetime.strptime(self.offline_at, "%Y-%m-%dT%H:%M:%S")
        except:
            pass

        try:
            last_online_date = datetime.strptime(self.last_online, "%Y-%m-%dT%H:%M:%S")
        except:
            pass

        if last_online_date > last_offline_date:
            last_reported = self.last_online
        else:
            last_reported = self.offline_at

        return last_reported

    @property
    def serial(self):
        return self.sn

    @property
    def status_list(self):
        return {"model": self.product_name,
                "status": self.status,
                "status_text": self.status,
                "serial": self.serial,
                "name": self.name,
                "device_name": self.name}

    @property
    def interfaces_list(self):
        """converts the stored list of interfaces into Python list"""
        from ast import literal_eval
        tmp = []
        if self.interfaces:
            for interface in self.interfaces:
                try:
                    tmp.append(literal_eval(interface))
                except Exception:
                    _logger.warn("Could not convert interface data to Python data type. {}".format(interface))
                    pass
        return tmp

    @property
    def starlink_statuses(self):

        from ast import literal_eval
        tmp = []
        if self.starlink_status:
            for status in self.starlink_status:
                try:
                    tmp.append(literal_eval(status))
                except Exception:
                    _logger.warn("Could not convert interface data to Python data type. {}".format(status))
                    pass
        return tmp

    @property
    def incontrol_group(self):
        g = None
        try:
            g = PeplinkGroup.objects.get(group_id=self.group_id)
        except Exception:
            pass
        return g


class CustomerPeplinkGroup(models.Model):
    customer = models.ForeignKey("dashboard.Customer", on_delete=models.CASCADE)
    group = models.ForeignKey("dashboard.PeplinkGroup", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Customer Peplink Group"
        verbose_name_plural = "Customer Peplink Groups"

    def __str__(self):
        return "{} ({})".format(self.customer.name, self.group.name)


class MerakiDevice(models.Model):
    #name = models.CharField("Device Name", max_length=255, null=True, blank=True, default=''),
    device_name = models.CharField ("Device Name", max_length=255, null=True, blank=True, default='')
    serial = models.CharField("Serial", max_length=255)
    imei = models.IntegerField("IMEI", null=True, blank=True)
    mac = models.CharField("MAC", max_length=255)
    networkId = models.CharField("Network ID", max_length=255)
    productType = models.CharField("Product Type", max_length=255)
    model = models.CharField("Model", max_length=255)
    address = models.CharField("Address", max_length=255, null=True, blank=True)
    lat = models.FloatField("Latitude", null=True, blank=True)
    lng = models.FloatField("Longitude", null=True, blank=True)
    notes = models.CharField("Notes", max_length=255, null=True, blank=True)
    tags = models.CharField("Notes", max_length=255, null=True, blank=True)
    wan1Ip = models.CharField("WAN1 IP", max_length=255, null=True, blank=True)
    configurationUpdatedAt = models.CharField(max_length=255)
    firmware = models.CharField("Firmware", max_length=255, null=True, blank=True)
    url = models.CharField("URL", max_length=255, null=True, blank=True)
    details = models.CharField("Details", max_length=255, null=True, blank=True)
    network = models.ForeignKey('Network', on_delete=models.CASCADE, null=True, blank=True, default=None)
    status_text = models.CharField("Device Status", max_length=100, null=True, blank=True, default='')
    status_list = models.JSONField("Device Status Details", max_length=10000, null=True, blank=True, default=list)

    publicIp = models.CharField("Public IP Address", max_length=100, null=True, blank=True)
    gateway = models.CharField("Gateway", max_length=100, null=True, blank=True)
    primaryDns = models.CharField("Primary DNS", max_length=100, null=True, blank=True)
    secondaryDns = models.CharField("Secondary DNS", max_length=100, null=True, blank=True)
    last_updated_at = models.DateTimeField("Last Updated At", auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True, null=True, blank=True)
    internal_class = models.CharField("Internal Class", help_text="Automatically Set by DataSync Process", null=True, blank=True, default="", max_length=255)

    class Meta:
        verbose_name = _("Meraki Device")
        verbose_name_plural = _("Meraki Devices")
        unique_together = ('serial', 'networkId')

    def __str__(self):
        return f"{self.device_name} - {self.network_id} - SN: {self.serial}"

    @property
    def last_reported_at(self):
        last_reported = ''
        if self.status_list:
            try:
                last_reported = self.status_list[0].get('lastReportedAt', '')
                return last_reported
            except:
                pass
            # if the status_list does not contain a list
            try:
                last_reported = self.status_list.get('lastReportedAt', '')
                return last_reported
            except:
                pass

        return last_reported
    @property
    def sn(self):
        return self.serial

    @property
    def name(self):
        return self.device_name

    @property
    def status(self):
        return self.status_text

    @property
    def latitude(self):
        return self.lat

    @property
    def longitude(self):
        return self.lng


class CustomerNetwork(models.Model):
    customer = models.ForeignKey("dashboard.Customer", on_delete=models.CASCADE)
    network = models.ForeignKey("dashboard.Network", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Customer's Meraki Network"
        verbose_name_plural = "Customer's Meraki Networks"

    def __str__(self):
        return "{} ({})".format(self.customer.name, self.network.name)


class MerakiNetworkDevice(models.Model):
    network = models.ForeignKey("dashboard.Network", on_delete=models.CASCADE)
    device = models.ForeignKey("dashboard.MerakiDevice", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Meraki Network Device"
        verbose_name_plural = "Meraki Network Devices"

    def __str__(self):
        return "{} ({})".format(self.network, self.device)


class UnifiSite(models.Model):
    name = models.CharField("Site Name", max_length=255)
    _id = models.CharField("Site ID", max_length=255)
    anonymous_id = models.CharField("Anonymous ID", max_length=255)
    desc = models.CharField("Description", max_length=255, null=True, blank=True, default='')
    num_new_alarms = models.IntegerField("Number of New Alarms", null=True, blank=True, default=0)
    health = ArrayField(
            models.CharField(
                max_length=10000,
                blank=True,
                null=True),
            blank=True,
            null=True,
            verbose_name="Site Health",
            help_text="Site Health")
    last_updated_at = models.DateTimeField("Last Updated At", auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True, null=True, blank=True)

    class Meta:
        verbose_name = "Unifi Site"
        verbose_name_plural = "Unifi Sites"
        unique_together = ('_id', 'anonymous_id', 'name')

    def __str__(self):
        return f"{self.name} - {self.desc}"

# Unifi Device data
# { 'adopted': True,
#     'disabled': False,
#     'in_gateway_mode': False,
#     'mac': '74:ac:b9:4c:6d:01',
#     'model': 'US8P60',
#     'name': 'SW01- FL01 - Kitchen',
#     'state': 1,
#     'type': 'usw'}

class UnifiDevice(models.Model):

    name = models.CharField("Device Name", max_length=255)
    mac = models.CharField("MAC", max_length=255)
    model = models.CharField("Model", max_length=255)
    device_type = models.CharField("Type", max_length=255)
    state = models.IntegerField("State", null=True, blank=True)
    in_gateway_mode = models.BooleanField("In Gateway Mode", null=True, blank=True)
    disabled = models.BooleanField("Disabled", null=True, blank=True)
    site = models.ForeignKey("UnifiSite", on_delete=models.CASCADE, null=True, blank=True, default=None)
    serial = models.CharField("Serial", null=True, blank=True, max_length=255, default='')
    last_updated_at = models.DateTimeField("Last Updated At", auto_now=True, null=True, blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True, null=True, blank=True)
    internal_class = models.CharField("Internal Classification", help_text="Automatically Set by DataSync Process", null=True, blank=True, default="", max_length=255)

    class Meta:
        verbose_name = "Unifi Device"
        verbose_name_plural = "Unifi Devices"
        unique_together = ('name', 'mac')

    def __str__(self):
        return f"{self.name} - {self.mac}"

    @property
    def sn(self):
        return self.serial

    @property
    def status(self):
        """
        translate the status code to its name
        ref: https://github.com/Art-of-WiFi/UniFi-API-client/blob/d36a088101e3422e98be1c042afdebaf5f190e8b/src/Client.php#L3379
        """
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

        return STATUS.get(self.state, f'Unknown State {self.state}')

    @property
    def latitude(self):
        return None

    @property
    def longitude(self):
        return None

    @property
    def status_list(self):
        return {"model": self.model,
                "status": self.status,
                "status_text": self.status,
                "serial": self.serial,
                "name": self.name,
                "device_name": self.name}


class CustomerUnifiSite(models.Model):

    customer = models.ForeignKey("dashboard.Customer", on_delete=models.CASCADE)
    site = models.ForeignKey("dashboard.UnifiSite", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Customer's Unifi Site"
        verbose_name_plural = "Customer's Unifi Sites"

    def __str__(self):
        return "{} ({})".format(self.customer.name, self.site.name)


class DataSyncLog(models.Model):
    data_type = models.CharField(verbose_name="Data Type", max_length=255, null=True, blank=True, default='')
    sync_date = models.DateField(verbose_name="Sync Date", auto_now=True)
    sync_time = models.DateTimeField(verbose_name="Sync Time", auto_now=True)
    result = models.CharField(verbose_name="Sync Result", max_length=255, null=True, blank=True, default='')
    message = models.TextField(verbose_name="Message", null=True, blank=True, default='')

    def __str__(self):
        return f"{self.data_type} - {self.sync_time} - {self.result}"

# class NetworkSecurityEvent(models.Model):
#     meraki_network = models.ForeignKey("Network", on_delete=models.CASCADE)
#     event = models.JSONField("Event", null=True, blank=True)


class DeviceStatus(models.Model):
    ROUTER_STATUS_CHOICES = (
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('alerting', 'Alerting'),
        ('dormant', 'Dormant'),
        # Unifi-specific statuses
        ('pending adoption', 'Pending Adoption'),
        ('updating', 'Updating'),
        ('provisioning', 'Provisioning'),
        ('unreachable', 'Unreachable'),
        ('adopting', 'Adopting'),
        ('adoption error', 'Adoption Error'),
        ('adoption failed', 'Adoption Failed'),
        ('isolated', 'Isolated')

    )
    ROUTER_TYPE_CHOICES = (
        ('M', 'Meraki'),
        ('P', 'Peplink'),
        ('U', 'Ubiquiti'),
    )
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE)
    device_name = models.CharField("Device Name", max_length=255, null=True, blank=True, default="")
    device_type = models.CharField("Device Type", max_length=1, choices=ROUTER_TYPE_CHOICES, default='M')
    status = models.CharField("Status", max_length=50, choices=ROUTER_STATUS_CHOICES, default='offline')
    as_of_time = models.DateTimeField("As Of Time", auto_now_add=True)
    network_id = models.CharField(max_length=255, null=True, blank=True, default='')
    serial = models.CharField(max_length=255, null=True, blank=True, default='')
    product_type = models.CharField(max_length=255, null=True, blank=True, default='')
    model = models.CharField(max_length=255, null=True, blank=True, default='')
    mac = models.CharField(max_length=255, null=True, blank=True, default='')
    last_reported_at = models.DateTimeField("Last Reported At", null=True, blank=True, default=None)
    latitude = models.DecimalField("Latitude", max_digits=12, decimal_places=8, null=True, blank=True, default=None)
    longitude = models.DecimalField("Longitude", max_digits=12, decimal_places=8, null=True, blank=True, default=None)
    heading = models.DecimalField("Heading", max_digits=12, decimal_places=8, null=True, blank=True, default=None)

    class Meta:
        verbose_name = "Device Status"
        verbose_name_plural = "Device Statuses"

    def __str__(self):
        return f"{self.device_name} - {self.status} : [{self.as_of_time}]"

    @property
    def status_list(self):
        """
        A property function that returns a dictionary containing various status-related attributes.
        NOTE: this is just for compatibility with some existing template code
        """
        return {"model": self.model,
                "status": self.status,
                "status_text": self.status,
                "serial": self.serial,
                "name": self.device_name,
                "device_name": self.device_name}

    def save(self, *args, **kwargs):
        if not self.pk:
            self.as_of_time = timezone.now()
            previous_record = None
            heading = None

            if self.latitude or self.longitude:
                past_24_hours = self.as_of_time - timedelta(hours=24)
                previous_record = DeviceStatus.objects.filter(
                    mac=self.mac,
                    serial=self.serial,
                    as_of_time__lt=self.as_of_time,
                    as_of_time__gte=past_24_hours
                ).order_by('-as_of_time').first()

            if previous_record:
                try:
                    heading = calculate_heading(previous_record.latitude,
                                                previous_record.longitude,
                                                self.latitude,
                                                self.longitude)
                    self.heading = heading
                except:
                    pass

        super(DeviceStatus, self).save(*args, **kwargs)

    @classmethod
    def get_wan_history_json(cls, customer_id, period='hour', start_date=None, end_date=None):

        if not end_date:
            # default to current time
            end_date = datetime.now(tz=pytz.utc)
        if not start_date:
            # default to 1 month ago
            start_date = end_date - timedelta(days=30)

        #ensure end_date does not exceed current time
        if end_date > datetime.now(tz=pytz.utc):
            end_date = datetime.now(tz=pytz.utc)

        # ensure end_date is not before start_date
        if end_date < start_date:
            end_date = start_date


    @classmethod
    def get_median_device_status(cls, customer_id, time_group='1h', calculation_method='median'):
        interval_mapping = {
            '1h': ('minute', '1 hour'),
            '6h': ('hour', '6 hour'),
            '24h': ('hour', '24 hour'),
            '1w': ('day', '1 week'),
            '1mo': ('week', '1 month'),
        }

        _5_minute_group = "- (EXTRACT(minute FROM as_of_time)::int %% 5) * INTERVAL '1 minute' "
        extra_field = _5_minute_group if time_group == '1h' else ""

        if time_group not in interval_mapping:
            raise ValueError("Invalid interval specified")

        if calculation_method not in ['median', 'average']:
            raise ValueError("Invalid calculation method specified")

        interval_bin = interval_mapping[time_group][0]
        period_start = interval_mapping[time_group][1]
        result = []

        query_params = [interval_bin, int(customer_id)]

        if calculation_method == 'median':
            select_query = f"""
                WITH daily_counts AS (
                    SELECT
                        date_trunc(%s, as_of_time) {extra_field} AS interval,
                        status,
                        COUNT(DISTINCT(serial)) AS count
                    FROM
                        public.dashboard_devicestatus
                    WHERE
                        customer_id = %s AND
                        as_of_time >= now() - interval '{period_start}' AND
                        as_of_time <= now() AND
                        product_type IN ('appliance', 'ugw', 'udm', 'uxg', 'balancemax')
                    GROUP BY
                        1, 2
                ),
                ranked_counts AS (
                    SELECT
                        interval,
                        status,
                        count,
                        ROW_NUMBER() OVER (PARTITION BY interval, status ORDER BY count) AS row_num,
                        COUNT(*) OVER (PARTITION BY interval, status) AS total_counts
                    FROM
                        daily_counts
                ),
                median_counts AS (
                    SELECT
                        interval,
                        status,
                        count
                    FROM
                        ranked_counts
                    WHERE
                        row_num = (total_counts + 1) / 2
                        OR (total_counts %% 2 = 0 AND row_num = (total_counts + 2) / 2)
                )
                SELECT
                    to_char(interval, 'YYYY-MM-DD HH24:MI:SS') AS formatted_interval,
                    COALESCE(MAX(CASE WHEN status = 'online' THEN count END), 0) AS median_online,
                    COALESCE(MAX(CASE WHEN status = 'offline' THEN count END), 0) AS median_offline,
                    COALESCE(MAX(CASE WHEN status = 'alerting' THEN count END), 0) AS median_alerting
                FROM
                    median_counts
                GROUP BY
                    1
                ORDER BY
                    formatted_interval
            """
        else:  # calculation_method == 'average'
            select_query = f"""
                SELECT
                    to_char(date_trunc(%s, as_of_time) {extra_field}, 'YYYY-MM-DD HH24:MI:SS') AS formatted_interval,
                    COALESCE(AVG(CASE WHEN status = 'online' THEN count END), 0) AS avg_online,
                    COALESCE(AVG(CASE WHEN status = 'offline' THEN count END), 0) AS avg_offline,
                    COALESCE(AVG(CASE WHEN status = 'alerting' THEN count END), 0) AS avg_alerting
                FROM (
                    SELECT
                        date_trunc(%s, as_of_time) {extra_field} AS interval,
                        status,
                        COUNT(DISTINCT(serial)) AS count
                    FROM
                        public.dashboard_devicestatus
                    WHERE
                        customer_id = %s AND
                        as_of_time >= now() - interval '{period_start}' AND
                        as_of_time <= now() AND
                        product_type IN ('appliance', 'ugw', 'udm', 'uxg', 'balancemax')
                    GROUP BY
                        1, 2
                ) AS subquery
                GROUP BY
                    1
                ORDER BY
                    formatted_interval
            """
            query_params.append(interval_bin)  # Add interval_bin again for the nested subquery

        with connection.cursor() as cursor:
            try:
                cursor.execute(select_query, params=query_params)
                result = cursor.fetchall()
            except Exception as e:
                _logger.warn("error fetching historical device status: {}".format(e))
                raise e  # Re-raise the exception after logging

        # Formatting result for ChartJS
        labels = []
        online_counts = []
        offline_counts = []
        alerting_counts = []

        for row in result:
            #labels.append(row[0])  # Adjust format as needed
            date_string = row[0]
            if time_group in ('1w', '1mo'):
                date_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
                # Format datetime object into desired string
                formatted_date = date_object.strftime("%d-%b-%y").upper()
                if time_group == '1mo':
                    iso_year, iso_week_num, _ = date_object.isocalendar()
                    formatted_date = formatted_date + f" (W{iso_week_num})"
                labels.append(formatted_date)
            else:
                labels.append(row[0])

            online_counts.append(row[1])
            offline_counts.append(row[2])
            alerting_counts.append(row[3])

        chart_data = {
            'labels': labels,
            'datasets': [
                {
                    'label': 'Online',
                    'data': online_counts,
                    'backgroundColor': 'rgba(28, 180, 84, 0.8)',
                    'borderColor': 'rgba(75, 192, 192, 1)',
                    'borderWidth': 1
                },
                {
                    'label': 'Offline',
                    'data': offline_counts,
                    'backgroundColor': 'rgba(180, 0, 0, 0.8)',
                    'borderColor': 'rgba(255, 99, 132, 1)',
                    'borderWidth': 1
                },
                {
                    'label': 'Alerting',
                    'data': alerting_counts,
                    'backgroundColor': 'rgba(255, 166, 0, 0.8)',
                    'borderColor': 'rgba(255, 206, 86, 1)',
                    'borderWidth': 1
                }
            ]
        }

        return json.dumps(chart_data)
