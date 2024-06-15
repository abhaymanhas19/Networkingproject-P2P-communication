from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from dashboard import data_sync
from dashboard import models as dm

class Command(BaseCommand):
    help = 'syncs all devices with dashboard Devices'

    def handle(self, *args, **options):
        try:
            data_sync.sync_peplink_organizations()
            dm.DataSyncLog.objects.create(data_type='Peplink Organizations', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced all Peplink Organizations'))
        except Exception as e:
            msg = f'Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Peplink Organizations', result='failed', message=msg)

        try:
            data_sync.sync_peplink_groups()
            dm.DataSyncLog.objects.create(data_type='Peplink Groups', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced all Peplink Groups'))
        except Exception as e:
            msg = f'Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Peplink Groups', result='failed', message=msg)

        try:
            data_sync.sync_peplink_group_devices()
            dm.DataSyncLog.objects.create(data_type='Peplink Group Devices', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced all Peplink Gruup Devices'))
        except Exception as e:
            msg = f'Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Peplink Group Devices', result='failed', message=msg)

        try:
            data_sync.sync_meraki_organizations()
            dm.DataSyncLog.objects.create(data_type='Meraki Organizations', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced all Meraki Organizations'))
        except Exception as e:
            msg = f'Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Meraki Organizations', result='failed', message=msg)

        try:
            data_sync.sync_meraki_networks()
            dm.DataSyncLog.objects.create(data_type='Meraki Networks', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced all Meraki Networks'))
        except Exception as e:
            msg = f'Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Meraki Networks', result='failed', message=msg)

        try:
            data_sync.sync_meraki_devices()
            dm.DataSyncLog.objects.create(data_type='Meraki Devices', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced all Meraki Devices'))
        except Exception as e:
            msg = f'Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Meraki Devices', result='failed', message=msg)

        try:
            data_sync.sync_unifi_sites()
            dm.DataSyncLog.objects.create(data_type='Unifi Sites', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced all Unifi Sites'))
        except Exception as e:
            msg = f'Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Unifi Sites', result='failed', message=msg)

        try:
            data_sync.sync_unifi_devices()
            dm.DataSyncLog.objects.create(data_type='Unifi Devices', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced all Unifi Devices'))
        except Exception as e:
            msg = f'Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Unifi Devices', result='failed', message=msg)

        # delete dm.Organization that are older than 7 days
        dm.DataSyncLog.objects.filter(sync_time__lt=datetime.now() - timedelta(days=7)).delete()

