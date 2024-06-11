from django.core.management.base import BaseCommand
from dashboard import data_sync
class Command(BaseCommand):
    help = 'syncs all devices with dashboard Devices'

    def handle(self, *args, **options):
        try:
            data_sync.sync_all_data()
            self.stdout.write(self.style.SUCCESS('Successfully synced all device data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}\n'))
