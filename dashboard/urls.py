from django.urls import path
from .views import DeviceStatusChartView, DeviceLocationHistoryView


urlpatterns = [
    path('device-status-chart/', DeviceStatusChartView.as_view(), name='device_status_chart'),
    path('device-location-history/', DeviceLocationHistoryView.as_view(), name='device_location_history'),
]
