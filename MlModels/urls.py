from django.urls import path
from .views import ShadowRatioPredictionView,EmissionPredictionView

urlpatterns = [
    path('predict-shadow-ratios/', ShadowRatioPredictionView.as_view(), name='predict-shadow-ratios'),
    path('predict-carbon-emission/', EmissionPredictionView.as_view(), name='predict-carbon-emission'),
]
