from django.urls import path
from .views import SolarPositionView,SolarPotentialView,SolarPotentialEachFaceView

urlpatterns = [
    path('sun_position/', SolarPositionView.as_view(), name='solar_position'),
    path('solar_potential/', SolarPotentialView.as_view(), name='solar_potential'),
    path('face_potential/', SolarPotentialEachFaceView.as_view(), name='face_potential'),
]