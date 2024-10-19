import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from dashboard import data_sync
from dashboard import models as dm


_logger =  logging.getLogger(__name__)

# TODO: add command to sync the device location at closer intervals

class Command(BaseCommand):
    help = 'Syncs all Device Statuses. This should be called every 5 minutes via cron or scheduler'

    def handle(self, *args, **options):
        try:
            data_sync.sync_peplink_device_statuses()
            dm.DataSyncLog.objects.create(data_type='Peplink Device Statuses', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced Peplink Device Statuses'))
        except Exception as e:
            msg = f'sync_peplink_device_statuses Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Peplink Device Statuses', result='failed', message=msg)
            _logger.error(msg, exc_info=True)

        try:
            data_sync.sync_meraki_device_statuses()
            dm.DataSyncLog.objects.create(data_type='Meraki Device Statuses', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced Meraki Device Statuses'))
        except Exception as e:
            msg = f'sync_meraki_device_statuses Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Meraki Device Statuses', result='failed', message=msg)
            _logger.error(msg, exc_info=True)

        try:
            data_sync.sync_unifi_device_statuses()
            dm.DataSyncLog.objects.create(data_type='Unifi Device Statuses', result='success')
            self.stdout.write(self.style.SUCCESS('Successfully synced Unifi Device Statuses'))
        except Exception as e:
            msg = f'sync_unifi_device_statuses Error: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            dm.DataSyncLog.objects.create(data_type='Unifi Device Statuses', result='failed', message=msg)
            _logger.error(msg, exc_info=True)

        # delete dm.Organization that are older than 7 days
        dm.DataSyncLog.objects.filter(sync_time__lt=datetime.now() - timedelta(days=7)).delete()
