import logging

from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings

from dashboard import data_sync
from dashboard import models as dm


_logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete Old Records. Retaining the last DATA_RETENTION_DAYS days of data'

    def handle(self, *args, **options):
        try:
            # delete dm.Organization that are older than 7 days
            dm.DataSyncLog.objects.filter(sync_time__lt=datetime.now() - timedelta(days=7)).delete()
            self.stdout.write(self.style.SUCCESS('Successfully deleted old DataSyncLog'))
        except Exception as e:
            msg = f'Error Deleting Old DataSyncLog: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            _logger.error(msg, exc_info=True)

        try:
            dm.RouterGPSHistory.objects.filter(as_of_time__lt=datetime.now() - timedelta(days=settings.DATA_RETENTION_DAYS)).delete()
            self.stdout.write(self.style.SUCCESS('Successfully deleted old RouterGPSHistory'))
        except Exception as e:
            msg = f'Error Deleting Old RouterGPSHistory: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            _logger.error(msg, exc_info=True)
        
        try:
            dm.CellularInfoHistory.objects.filter(as_of_time__lt=datetime.now() - timedelta(days=settings.DATA_RETENTION_DAYS)).delete()
            self.stdout.write(self.style.SUCCESS('Successfully deleted old CellularInfoHistory'))
        except Exception as e:
            msg = f'Error Deleting Old CellularInfoHistory: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            _logger.error(msg, exc_info=True)

        try:
            dm.StarlinkInfoHistory.objects.filter(as_of_time__lt=datetime.now() - timedelta(days=settings.DATA_RETENTION_DAYS)).delete()
            self.stdout.write(self.style.SUCCESS('Successfully deleted old CellularInfoHistory'))
        except Exception as e:
            msg = f'Error Deleting Old StarlinkInfoHistory: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            _logger.error(msg, exc_info=True)
        
        try:
            dm.DeviceStatus.objects.filter(as_of_time__lt=datetime.now() - timedelta(days=settings.DATA_RETENTION_DAYS)).delete()
            self.stdout.write(self.style.SUCCESS('Successfully deleted old DeviceStatus'))
        except Exception as e:
            msg = f'Error Deleting Old DeviceStatus: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            _logger.error(msg, exc_info=True)
        
        try:
            dm.WANInfoHistory.objects.filter(as_of_time__lt=datetime.now() - timedelta(days=settings.DATA_RETENTION_DAYS)).delete()
            self.stdout.write(self.style.SUCCESS('Successfully deleted old WANInfoHistory'))
        except Exception as e:
            msg = f'Error Deleting Old WANInfoHistory: {str(e)}\n'
            self.stdout.write(self.style.ERROR(msg))
            _logger.error(msg, exc_info=True)
