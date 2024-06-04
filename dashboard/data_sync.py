from dashboard import models as dashboard_models

from incontrol.client import API as PeplinkAPI
from meraki import DashboardAPI as MerakiAPI
from django.conf import settings


def sync_peplink_organizations():
    """syncs peplink organzations with dashboard Organizations"""

    api = PeplinkAPI(settings.PEPLINK_CLIENT_ID, settings.PEPLINK_CLIENT_SECRET)
    organizations = api.get_organizations()

    for org in organizations:
        dashboard_org = dashboard_models.Organization.objects.filter(org_id=org['id']).first()
        if not dashboard_org:
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
