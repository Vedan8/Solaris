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

            # Process the 3D model to generate updated OBJ and MTL contents
            updated_obj_path, updated_mtl_path = process_3d_model(solar_irradiance, timestamp)

            # Read the content of the updated files
            with open(updated_obj_path, 'rb') as obj_file, open(updated_mtl_path, 'rb') as mtl_file:
                obj_content = obj_file.read()
                mtl_content = mtl_file.read()

            # Create a new ProcessedModel instance and save the files in the database
            processed_model = ProcessedModel.objects.create(
                obj_file=ContentFile(obj_content, name="updated.obj"),
                mtl_file=ContentFile(mtl_content, name="updated.mtl")
            )

            # Construct file URLs
            obj_file_url = processed_model.obj_file.url
            mtl_file_url = processed_model.mtl_file.url

            return Response({
                "message": "Files processed successfully.",
                "obj_file_url": obj_file_url,
                "mtl_file_url": mtl_file_url
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=400)
