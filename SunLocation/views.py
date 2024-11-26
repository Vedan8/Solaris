from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser
from datetime import datetime
import pytz
import numpy as np
import pvlib

class SolarPositionView(APIView):
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
