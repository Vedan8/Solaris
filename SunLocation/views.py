from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import JSONParser
import pytz
import numpy as np
import pvlib
import math
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.http import FileResponse
from datetime import datetime, timedelta

class SolarPositionView(APIView):
    # permission_classes = [IsAuthenticated]
    
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
            r = 200

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

    def calculate_theta(self, latitude, longitude, date_time):
        """
        Calculate the solar zenith angle (theta) based on latitude, longitude, and datetime.
        """
        # Convert latitude and longitude to radians
        latitude_rad = math.radians(latitude)

        # Parse date and time
        date_time = datetime.fromisoformat(date_time)  # ISO 8601 format (e.g., "2024-12-06T12:00:00")
        day_of_year = date_time.timetuple().tm_yday

        # Calculate solar declination (\u03b4)
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

        # Calculate solar zenith angle (\u03b8)
        cos_theta = (
            math.sin(latitude_rad) * math.sin(declination_rad) +
            math.cos(latitude_rad) * math.cos(declination_rad) * math.cos(hour_angle)
        )

        # Return \u03b8 (in radians) ensuring cos_theta is clamped between -1 and 1
        return math.acos(max(-1, min(1, cos_theta)))

    def calculate_hourly_potential(self, latitude, longitude, date, solar_irradiance, efficiency, area):
        """
        Calculate hourly solar potential for the specified date and location.
        """
        hourly_potential = []
        
        for hour in range(6, 19):  # 6 AM to 6 PM (18:00)
            # Create datetime for the specific hour
            date_time = datetime.fromisoformat(date).replace(hour=hour, minute=0, second=0)
            
            # Calculate solar zenith angle (theta)
            theta = self.calculate_theta(latitude, longitude, date_time.isoformat())
            
            # Calculate potential for the hour
            potential = (
                area * solar_irradiance * efficiency * abs(math.cos(theta))
            ) / 10
            hourly_potential.append(round(potential, 2))
        
        return hourly_potential

    def post(self, request):
        try:
            # Extract input data
            length = request.data.get('length')
            breadth = request.data.get('breadth')
            height = request.data.get('height')
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            date = request.data.get('date')  # ISO 8601 format (e.g., "2024-12-06")
            solar_irradiance = request.data.get('solar_irradiance')  # kWh/m²/day
            efficiency_bipv = request.data.get('efficiency_bipv', 0.12)  # Default 12%
            efficiency_rooftop = request.data.get('efficiency_rooftop', 0.18)  # Default 18%

            # Validate input
            if not all([length, breadth, height, latitude, longitude, date, solar_irradiance]):
                return Response(
                    {"error": "length, breadth, height, latitude, longitude, date, and solar_irradiance are required."},
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

            # Calculate rooftop area
            rooftop_area = length * breadth

            # Calculate hourly potential for rooftop
            rooftop_hourly = self.calculate_hourly_potential(
                latitude, longitude, date, solar_irradiance, efficiency_rooftop, rooftop_area
            )

            # Calculate BIPV area (using one wall)
            bipv_area = height * breadth

            # Calculate hourly potential for BIPV
            bipv_hourly = self.calculate_hourly_potential(
                latitude, longitude, date, solar_irradiance, efficiency_bipv, bipv_area
            )

            # Prepare response
            result = {
                "rooftop_hourly_potential_kwh": rooftop_hourly,
                "bipv_hourly_potential_kwh": bipv_hourly
            }

            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



import math
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class SolarPotentialEachFaceView(APIView):

    def calculate_theta(self, latitude, longitude, date_time):
        """
        Calculate the solar zenith angle (theta) based on latitude, longitude, and datetime.
        """
        latitude_rad = math.radians(latitude)
        date_time = datetime.fromisoformat(date_time)  # ISO 8601 format (e.g., "2024-12-06T12:00:00")
        day_of_year = date_time.timetuple().tm_yday

        declination = 23.45 * math.sin(math.radians((360 / 365) * (284 + day_of_year)))
        declination_rad = math.radians(declination)

        standard_meridian = round(longitude / 15) * 15  # Nearest time zone meridian
        time_correction = 4 * (longitude - standard_meridian)

        local_time = date_time.hour + date_time.minute / 60 + date_time.second / 3600
        solar_time = local_time + time_correction / 60

        hour_angle = math.radians(15 * (solar_time - 12))

        cos_theta = (
            math.sin(latitude_rad) * math.sin(declination_rad) +
            math.cos(latitude_rad) * math.cos(declination_rad) * math.cos(hour_angle)
        )

        return math.acos(max(-1, min(1, cos_theta)))

    def calculate_sun_position(self, latitude, longitude, date_time):
        """
        Calculate the sun's azimuth angle to determine which face is exposed to sunlight.
        """
        latitude_rad = math.radians(latitude)
        date_time = datetime.fromisoformat(date_time)
        day_of_year = date_time.timetuple().tm_yday

        declination = 23.45 * math.sin(math.radians((360 / 365) * (284 + day_of_year)))
        declination_rad = math.radians(declination)

        standard_meridian = round(longitude / 15) * 15
        time_correction = 4 * (longitude - standard_meridian)

        local_time = date_time.hour + date_time.minute / 60 + date_time.second / 3600
        solar_time = local_time + time_correction / 60

        hour_angle = math.radians(15 * (solar_time - 12))

        cos_theta = (
            math.sin(latitude_rad) * math.sin(declination_rad) +
            math.cos(latitude_rad) * math.cos(declination_rad) * math.cos(hour_angle)
        )
        zenith_angle = math.acos(max(-1, min(1, cos_theta)))

        sin_azimuth = math.cos(declination_rad) * math.sin(hour_angle) / math.sin(zenith_angle)
        cos_azimuth = (
            (math.sin(zenith_angle) * math.sin(latitude_rad) - math.sin(declination_rad)) /
            (math.cos(zenith_angle) * math.cos(latitude_rad))
        )

        azimuth = math.atan2(sin_azimuth, cos_azimuth)
        return math.degrees(azimuth) % 360

    def calculate_exposure_percentages(self, azimuth):
        """
        Calculate the exposure percentages for each face based on the sun's azimuth angle.
        """
        if 0 <= azimuth < 90:  # Northeast
            east_percentage = (90 - azimuth) / 90
            north_percentage = azimuth / 90
            return [north_percentage, 0, 0, east_percentage]
        elif 90 <= azimuth < 180:  # Southeast
            east_percentage = (180 - azimuth) / 90
            south_percentage = (azimuth - 90) / 90
            return [0, south_percentage, 0, east_percentage]
        elif 180 <= azimuth < 270:  # Southwest
            west_percentage = (270 - azimuth) / 90
            south_percentage = (azimuth - 180) / 90
            return [0, south_percentage, west_percentage, 0]
        else:  # Northwest
            west_percentage = (360 - azimuth) / 90
            north_percentage = (azimuth - 270) / 90
            return [north_percentage, 0, west_percentage, 0]

    def calculate_hourly_potential(self, latitude, longitude, date, solar_irradiance, efficiency, areas):
        """
        Calculate hourly solar potential for each face based on the sun's position.
        """
        hourly_potential = {"face1": [], "face2": [], "face3": [], "face4": []}
        
        for hour in range(6, 19):  # 6 AM to 6 PM (18:00)
            date_time = datetime.fromisoformat(date).replace(hour=hour, minute=0, second=0)

            azimuth = self.calculate_sun_position(latitude, longitude, date_time.isoformat())
            exposure_percentages = self.calculate_exposure_percentages(azimuth)

            for i, face in enumerate(["face1", "face2", "face3", "face4"]):
                potential = (
                    areas[i] * solar_irradiance * efficiency * exposure_percentages[i]
                ) / 10
                hourly_potential[face].append(round(potential, 2))

        return hourly_potential

    def post(self, request):
        try:
            length = request.data.get('length')
            breadth = request.data.get('breadth')
            height = request.data.get('height')
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            date = request.data.get('date')  # ISO 8601 format (e.g., "2024-12-06")
            solar_irradiance = request.data.get('solar_irradiance')  # kWh/m²/day
            efficiency_bipv = request.data.get('efficiency_bipv', 0.12)  # Default 12%

            if not all([length, breadth, height, latitude, longitude, date, solar_irradiance]):
                return Response(
                    {"error": "length, breadth, height, latitude, longitude, date, and solar_irradiance are required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            length = float(length)
            breadth = float(breadth)
            height = float(height)
            latitude = float(latitude)
            longitude = float(longitude)
            solar_irradiance = float(solar_irradiance)
            efficiency_bipv = float(efficiency_bipv)

            areas = [height * length, height * breadth, height * length, height * breadth]

            hourly_potential = self.calculate_hourly_potential(
                latitude, longitude, date, solar_irradiance, efficiency_bipv, areas
            )

            return Response(hourly_potential, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
