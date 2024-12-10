from django.urls import path
from .views import Process3DModelView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('heatmap/', Process3DModelView.as_view(), name='process-3d-model'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
