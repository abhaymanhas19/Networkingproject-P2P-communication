import logging

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext as _

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

    class Meta:
        verbose_name = "Customer Information"
        verbose_name_plural = "Customer Information"

    @property
    def initials(self):
        first_3_words = self.name.split(" ")[:3]
        initials = "".join([w[0] for w in first_3_words]).upper()
        return initials
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

    class Meta:
        verbose_name = "Peplink Group Device"
        verbose_name_plural = "Peplink Group Devices"

    def __str__(self):
        return "{} ({})".format(self.name, self.sn)

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
    class Meta:
        verbose_name = _("Meraki Device")
        verbose_name_plural = _("Meraki Devices")
        unique_together = ('serial', 'networkId')

    def __str__(self):
        return f"{self.device_name} - {self.network_id} - SN: {self.serial}"


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
