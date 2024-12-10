# views.py

from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ProcessedModel
from .file_processor import process_3d_model
from datetime import datetime
import os

class Process3DModelView(APIView):
    def post(self, request):
        try:
            # Parse inputs
            solar_irradiance = float(request.data.get('solar_irradiance'))
            datetime_str = request.data.get('datetime')
            timestamp = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

            # Process the 3D model to generate updated OBJ and MTL files
            obj_file, mtl_file = process_3d_model(solar_irradiance, timestamp)

            # Save files directly to the database
            processed_model = ProcessedModel.objects.create(
                obj_file=obj_file,
                mtl_file=mtl_file
            )

            return Response({
                "message": "Files processed successfully.",
                "obj_file_url": processed_model.obj_file.url,
                "mtl_file_url": processed_model.mtl_file.url
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=400)
