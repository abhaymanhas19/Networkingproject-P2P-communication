from django.urls import path
from .views import (
    DeviceStatusChartView,
    DeviceLocationHistoryView,
    DeviceDetailView,
    StarlinkDataView
    )



urlpatterns = [
    path('device-status-chart/', DeviceStatusChartView.as_view(), name='device_status_chart'),
    path('device-location-history/', DeviceLocationHistoryView.as_view(), name='device_location_history'),
    path('router-details/', DeviceDetailView.as_view(), name='router_details'),
    path('router-details/<str:internal_class>/<str:serial>/', DeviceDetailView.as_view(), name='router_details'),
    path('router-details/<str:internal_class>/<str:serial>/<str:data_type>', StarlinkDataView.as_view(), name='starlink_chart_data'),
]
