
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

@admin.register(dashboard_models.Customer)
class CustomerAdmin(SemanticModelAdmin):
    list_display = ('name', 'contact_person', 'contact_email', 'primary_contact_no', 'secondary_contact_no')
    # list_filter = ('org_type', 'api_enabled')
    search_fields = ('name', 'contact_person', 'contact_email', 'primary_contact_no', 'secondary_contact_no')
    inlines = [OrganizationsInline, CustomerUsersInline]


@admin.register(dashboard_models.Organization)
class OrganizationsAdmin(SemanticModelAdmin):
    list_display = ('name', 'org_id', 'org_type', 'org_url', 'api_enabled')
    search_fields = ('name', 'org_id', 'org_type', 'org_url', 'api_enabled')
