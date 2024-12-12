from django.urls import path
from .views import SolarPositionView,SolarPotentialView,SolarPotentialEachFaceView,FaceColorView,ShadowEachFaceView

urlpatterns = [
    path('sun_position/', SolarPositionView.as_view(), name='solar_position'),
    path('solar_potential/', SolarPotentialView.as_view(), name='solar_potential'),
    path('face_potential/', SolarPotentialEachFaceView.as_view(), name='face_potential'),
    path('face_colors/', FaceColorView.as_view(), name='face_colors'),
    path('face_shadow/', ShadowEachFaceView.as_view(), name='Shadow'),
]