
from django import forms
from django.contrib import admin
from django.db import models
from django.contrib.auth import models as auth_models
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from dashboard import models as dashboard_models


from semantic_admin import SemanticModelAdmin, SemanticStackedInline, SemanticTabularInline



# admin.site.register(User)
# admin.site.register(Group)

# class ExampleStackedInline(SemanticStackedInline):
#     pass

# class ExampleTabularInline(SemanticTabularInline):
#     pass

# class ExampleAdmin(SemanticModelAdmin):
#     inlines = (ExampleStackedInline, ExampleTabularInline)

# @admin.register(auth_models.User)
# class UserAdmin(SemanticModelAdmin):
#     pass


# @admin.register(auth_models.Group)
# class GroupAdmin(SemanticModelAdmin):
#     pass


class ProfileInline(SemanticStackedInline):  # Or admin.TabularInline
    model = dashboard_models.Profile
    can_delete = False
    verbose_name_plural = 'profile'


class MerakiNetworkDeviceInline(SemanticStackedInline):
    model = dashboard_models.MerakiNetworkDevice
    #readonly_fields = [field.name for field in YourInlineModel._meta.get_fields()]
    extra = 1

class UnifiSiteInline(SemanticStackedInline):
    model = dashboard_models.CustomerUnifiSite
    extra = 1
    autocomplete_fields = ['site']
    can_delete = True


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    # list_display = ('username', 'email', 'first_name', 'last_name', 'profile_photo_tag')
    # readonly_fields = ('profile_photo_tag',) # Don't allow editing in the admin list view



# Re-register UserAdmin to include the profile inline
admin.site.unregister(auth_models.User)
admin.site.register(auth_models.User, UserAdmin)


class CustomerUsersInline(SemanticStackedInline):
    model = dashboard_models.CustomerUsers
    extra = 1
    autocomplete_fields = ['user']

class OrganizationsInline(SemanticStackedInline):
    model = dashboard_models.CustomerOrganization
    can_delete = True
    extra = 1
    autocomplete_fields = ['customer']


class CustomNetworkAutocomplete(forms.ModelChoiceField):
    queryset = dashboard_models.Network.objects.all()
    widget = forms.Select

    def label_from_instance(self, obj):
        return obj.name


class CustomerNetworksInline(SemanticStackedInline):
# class CustomerNetworksInline(admin.StackedInline):
    model = dashboard_models.CustomerNetwork
    extra = 1
    can_delete = True
    formfield_overrides = {
        models.ForeignKey: {'widget': CustomNetworkAutocomplete}
    }


@admin.register(dashboard_models.PeplinkGroup)
class PeplinkGroupAdmin(SemanticModelAdmin):
    list_display = ('name', 'org_id', 'group_id')
    search_fields = ('name', 'org_id', 'group_id')
    # inlines = [OrganizationsInline, CustomerUsersInline]

class PeplinkGroupsInline(SemanticStackedInline):
    model = dashboard_models.CustomerPeplinkGroup
    autocomplete_fields = ['group']
    extra = 1


@admin.register(dashboard_models.Customer)
class CustomerAdmin(SemanticModelAdmin):
    list_display = ('name', 'contact_person', 'contact_email', 'primary_contact_no', 'secondary_contact_no')
    # list_filter = ('org_type', 'api_enabled')
    search_fields = ('name', 'contact_person', 'contact_email', 'primary_contact_no', 'secondary_contact_no')
    inlines = [OrganizationsInline, CustomerNetworksInline, PeplinkGroupsInline, UnifiSiteInline, CustomerUsersInline]
    can_delete = True
    readonly_fields = ['last_updated_at', 'created_at', 'pk']


@admin.register(dashboard_models.Organization)
class OrganizationsAdmin(SemanticModelAdmin):
    list_display = ('name', 'org_id', 'org_type', 'org_url', 'api_enabled')
    search_fields = ('name', 'org_id', 'org_type', 'org_url', 'api_enabled')
    list_filter = ('org_type', 'api_enabled')
    readonly_fields = ['last_updated_at', 'created_at', 'pk']


@admin.register(dashboard_models.Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'network_id', 'organization')
    search_fields = ('name', 'network_id', 'organization__name')
    list_filter = ('organization', 'timezone')
    inlines = [MerakiNetworkDeviceInline]
    readonly_fields = ['last_updated_at', 'created_at', 'pk']

@admin.register(dashboard_models.GroupDevice)
class GroupDeviceAdmin(SemanticModelAdmin):
    list_filter = ['group_name', 'name', 'device_type']
    list_display = ('group_name', 'name', 'sn', 'product_id')
    search_fields = ('name', 'sn', 'product_id')
    readonly_fields = ['last_updated_at', 'created_at', 'pk', 'internal_class']


@admin.register(dashboard_models.MerakiDevice)
class MerakiDevice(SemanticModelAdmin):
    # list_display = ('network.name', 'device.name', 'device.serial')
    list_filter = ('network_id', 'status_text', 'productType')
    search_fields = ('device_name', 'serial')
    list_display = ['network','productType', 'device_name', 'serial', 'mac', 'status_text']
    readonly_fields = ['last_updated_at', 'created_at', 'pk', 'internal_class']

@admin.register(dashboard_models.UnifiSite)
class UnifiSiteAdmin(SemanticModelAdmin):
    list_display = ('name', '_id', 'desc')
    search_fields = ('name', 'desc', '_id')
    readonly_fields = ['last_updated_at', 'created_at', 'pk']

@admin.register(dashboard_models.UnifiDevice)
class UnifiDeviceAdmin(SemanticModelAdmin):
    list_display = ('site', 'device_type', 'name', 'mac')
    list_filter = ('site', 'device_type')
    search_fields = ('name', 'device_type', 'mac','serial')
    readonly_fields = ['last_updated_at', 'created_at', 'pk', 'internal_class']


@admin.register(dashboard_models.DataSyncLog)
class SyslogAdmin(SemanticModelAdmin):
    list_display = ('sync_time', 'data_type', 'result')
    list_filter = ('result', 'data_type')

@admin.register(dashboard_models.DeviceStatus)
class DeviceStatusAdmin(SemanticModelAdmin):
    list_display = ('customer', 'device_name', 'device_type', 'product_type', 'status', 'as_of_time')
    list_filter = ('status', 'customer', 'device_type', 'product_type', 'network_id', 'product_type')
    search_fields = ('serial', 'product_type', 'network_id', 'product_type','device_name')


@admin.register(dashboard_models.CellularInfoHistory)
class CellularInfoHistoryAdmin(SemanticModelAdmin):
    list_display = ('internal_class', 'device_serial', 'as_of_time')
    list_filter = ('device_serial', 'internal_class')
    search_fields = ('device_serial',)


@admin.register(dashboard_models.StarlinkInfoHistory)
class CellularInfoHistoryAdmin(SemanticModelAdmin):
    list_display = ('internal_class', 'device_serial', 'as_of_time')
    list_filter = ('device_serial', 'internal_class')
    search_fields = ['device_serial']
