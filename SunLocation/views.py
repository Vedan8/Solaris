from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser
from datetime import datetime
import pytz
import numpy as np
import pvlib
import math
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.http import FileResponse

class SolarPositionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        # Ensure the request data is in JSON format and contains 'date' and 'time'
        try:
            date_time = request.data.get('datetime')  # expecting 'datetime' key with 'YYYY-MM-DD HH:MM:SS' format
            if not date_time:
                return Response({"error": "Date and time not provided."}, status=status.HTTP_400_BAD_REQUEST)

            # Parse the date and time
            custom_time = date_time
            tz = pytz.timezone('Asia/Kolkata')  # Set the time zone for Ghaziabad

            try:
                # Convert custom time to a datetime object
                now = datetime.strptime(custom_time, '%Y-%m-%d %H:%M:%S')
                now = tz.localize(now)  # Localize the datetime object to the IST time zone
            except ValueError:
                return Response({"error": "Invalid time format. Use 'YYYY-MM-DD HH:MM:SS'."}, status=status.HTTP_400_BAD_REQUEST)

            # Ghaziabad coordinates
            latitude = 23.030357 
            longitude = 72.517845 

            # Create a location object for Ghaziabad
            location = pvlib.location.Location(latitude, longitude, tz=tz)

            # Calculate solar position for the given time
            solar_position = location.get_solarposition(now)

            # Extract the relevant solar position values
            altitude = solar_position['elevation'].values[0]
            azimuth = solar_position['azimuth'].values[0]

            # Assuming a distance of 100 units from the city to the Sun
            r = 100

            # Convert altitude (degrees) and azimuth (degrees) to radians
            altitude_rad = np.radians(altitude)
            azimuth_rad = np.radians(azimuth)

            # Calculate the 3D Cartesian coordinates
            x = r * np.cos(altitude_rad) * np.sin(azimuth_rad)  # East direction (x-axis)
            z = -r * np.cos(altitude_rad) * np.cos(azimuth_rad)  # Horizon, with North as negative and South as positive (y-axis)
            y = r * np.sin(altitude_rad)  # Upward direction (z-axis)

            # Return the calculated coordinates
            return Response({
                'x': round(x, 2),
                'y': round(y, 2),
                'z': round(z, 2),
                'datetime': custom_time
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SolarPotentialView(APIView):
    
    # permission_classes = [IsAuthenticated]

    def calculate_theta(self, latitude, longitude, date_time):
        """
        Calculate the solar zenith angle (theta) based on latitude, longitude, and datetime.
        """
        # Convert latitude and longitude to radians
        latitude_rad = math.radians(latitude)

        # Parse date and time
        date_time = datetime.fromisoformat(date_time)  # ISO 8601 format (e.g., "2024-12-06T12:00:00")
        day_of_year = date_time.timetuple().tm_yday

        # Calculate solar declination (δ)
        declination = 23.45 * math.sin(math.radians((360 / 365) * (284 + day_of_year)))

        # Convert to radians
        declination_rad = math.radians(declination)

        # Calculate time correction factor
        standard_meridian = round(longitude / 15) * 15  # Nearest time zone meridian
        time_correction = 4 * (longitude - standard_meridian)

        # Calculate solar time
        local_time = date_time.hour + date_time.minute / 60 + date_time.second / 3600
        solar_time = local_time + time_correction / 60

        # Calculate hour angle (H)
        hour_angle = math.radians(15 * (solar_time - 12))

        # Calculate solar zenith angle (θ)
        cos_theta = (
            math.sin(latitude_rad) * math.sin(declination_rad) +
            math.cos(latitude_rad) * math.cos(declination_rad) * math.cos(hour_angle)
        )

        # Return θ (in radians) ensuring cos_theta is clamped between -1 and 1
        return math.acos(max(-1, min(1, cos_theta)))

    def post(self, request):
        try:
            # Extract input data
            length = request.data.get('length')
            breadth = request.data.get('breadth')
            height = request.data.get('height')
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            date_time = request.data.get('date_time')  # ISO 8601 format
            solar_irradiance = request.data.get('solar_irradiance')  # kWh/m²/day
            efficiency_bipv = request.data.get('efficiency_bipv', 0.12)  # Default 12%
            efficiency_rooftop = request.data.get('efficiency_rooftop', 0.18)  # Default 18%

            # Validate input
            if not all([length, breadth, height, latitude, longitude, date_time, solar_irradiance]):
                return Response(
                    {"error": "length, breadth, height, latitude, longitude, date_time, and solar_irradiance are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Convert inputs to floats
            length = float(length)
            breadth = float(breadth)
            height = float(height)
            latitude = float(latitude)
            longitude = float(longitude)
            solar_irradiance = float(solar_irradiance)
            efficiency_bipv = float(efficiency_bipv)
            efficiency_rooftop = float(efficiency_rooftop)

            # Calculate θ for BIPV and rooftop
            theta_bipv = self.calculate_theta(latitude, longitude, date_time)
            theta_rooftop = self.calculate_theta(latitude, longitude, date_time)

            # Calculate rooftop area and potential
            rooftop_area = length * breadth
            rooftop_potential = (
                rooftop_area
                * solar_irradiance
                * efficiency_rooftop
                * abs(math.cos(theta_rooftop))  # Use abs() to ensure positive potential
            )

            # Calculate BIPV area and potential (using one wall)
            bipv_area = height * breadth
            bipv_potential = (
                bipv_area
                * solar_irradiance
                * efficiency_bipv
                * abs(math.cos(theta_bipv))  # Use abs() to ensure positive potential
            )

            # Prepare response
            result = {
                "rooftop_potential_kwh": round(rooftop_potential, 2),
                "bipv_potential_kwh": round(bipv_potential, 2)
            }

            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# class HeatMapView(APIView):
#     def get(self, request, *args, **kwargs):
#         # File paths
#         obj_file_path = '/path/to/your/file.obj'
#         mtl_file_path = '/path/to/your/file.mtl'

#         # Ensure files exist
#         if not os.path.exists(obj_file_path) or not os.path.exists(mtl_file_path):
#             return Response({"detail": "One or both files not found."}, status=404)

#         # Provide file URLs or direct file data
#         files = {
#             "obj_file": request.build_absolute_uri(f"/media/{os.path.basename(obj_file_path)}"),
#             "mtl_file": request.build_absolute_uri(f"/media/{os.path.basename(mtl_file_path)}"),
#         }

#         return Response(files)