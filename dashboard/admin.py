
from django.contrib import admin
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


class MerakiNetworkDeviceInline(SemanticTabularInline):
    model = dashboard_models.MerakiNetworkDevice
    #readonly_fields = [field.name for field in YourInlineModel._meta.get_fields()]
    extra = 1

class UnifiSiteInline(SemanticTabularInline):
    model = dashboard_models.CustomerUnifiSite
    extra = 1
    autocomplete_fields = ['site']


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    # list_display = ('username', 'email', 'first_name', 'last_name', 'profile_photo_tag')
    # readonly_fields = ('profile_photo_tag',) # Don't allow editing in the admin list view



# Re-register UserAdmin to include the profile inline
admin.site.unregister(auth_models.User)
admin.site.register(auth_models.User, UserAdmin)


class CustomerUsersInline(SemanticTabularInline):
    model = dashboard_models.CustomerUsers
    extra = 1
    autocomplete_fields = ['user']

class OrganizationsInline(SemanticTabularInline):
    model = dashboard_models.CustomerOrganization
    extra = 1
    autocomplete_fields = ['customer']

class CustomerNetworksInline(SemanticTabularInline):
    model = dashboard_models.CustomerNetwork
    extra = 1
    autocomplete_fields = ['network']

@admin.register(dashboard_models.PeplinkGroup)
class PeplinkGroupAdmin(SemanticModelAdmin):
    list_display = ('name', 'org_id', 'group_id')
    search_fields = ('name', 'org_id', 'group_id')
    # inlines = [OrganizationsInline, CustomerUsersInline]

class PeplinkGroupsInline(SemanticTabularInline):
    model = dashboard_models.CustomerPeplinkGroup
    autocomplete_fields = ['group']
    extra = 1


@admin.register(dashboard_models.Customer)
class CustomerAdmin(SemanticModelAdmin):
    list_display = ('name', 'contact_person', 'contact_email', 'primary_contact_no', 'secondary_contact_no')
    # list_filter = ('org_type', 'api_enabled')
    search_fields = ('name', 'contact_person', 'contact_email', 'primary_contact_no', 'secondary_contact_no')
    inlines = [OrganizationsInline, CustomerNetworksInline, PeplinkGroupsInline, UnifiSiteInline, CustomerUsersInline]



@admin.register(dashboard_models.Organization)
class OrganizationsAdmin(SemanticModelAdmin):
    list_display = ('name', 'org_id', 'org_type', 'org_url', 'api_enabled')
    search_fields = ('name', 'org_id', 'org_type', 'org_url', 'api_enabled')

@admin.register(dashboard_models.Network)
class NetworkAdmin(admin.ModelAdmin):
    list_display = ('name', 'network_id', 'organization')
    search_fields = ('name', 'network_id', 'organization')
    list_filter = ('organization', 'timezone')
    inlines = [MerakiNetworkDeviceInline]

@admin.register(dashboard_models.GroupDevice)
class GroupDeviceAdmin(SemanticModelAdmin):
    list_filter = ['group_name', 'name']
    list_display = ('group_name', 'name', 'sn', 'product_id')
    search_fields = ('name', 'sn', 'product_id')



@admin.register(dashboard_models.MerakiDevice)
class MerakiDevice(SemanticModelAdmin):
    # list_display = ('network.name', 'device.name', 'device.serial')
    list_filter = ('network_id',)
    search_fields = ('device_name', 'serial')
    list_display = ['network', 'networkId','device_name', 'serial', 'mac']

@admin.register(dashboard_models.UnifiSite)
class UnifiSiteAdmin(SemanticModelAdmin):
    list_display = ('name', '_id', 'desc')
    search_fields = ('name', 'desc', '_id')


@admin.register(dashboard_models.UnifiDevice)
class UnifiDeviceAdmin(SemanticModelAdmin):
    list_display = ('site', 'name', 'mac', 'model')
    list_filter = ('site', 'device_type')
    search_field = ('name', 'model')

