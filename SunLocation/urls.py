from django.urls import path
from .views import SolarPositionView

urlpatterns = [
    path('sun_position/', SolarPositionView.as_view(), name='solar_position'),
]