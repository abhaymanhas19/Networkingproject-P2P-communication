from django.urls import path
from .views import DeviceStatusChartView


urlpatterns = [
    path('device-status-chart/', DeviceStatusChartView.as_view(), name='device_status_chart'),
]
