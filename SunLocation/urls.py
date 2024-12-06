from django.urls import path
from .views import SolarPositionView,SolarPotentialView

urlpatterns = [
    path('sun_position/', SolarPositionView.as_view(), name='solar_position'),
    path('solar_potential/', SolarPotentialView.as_view(), name='solar_potential'),
]