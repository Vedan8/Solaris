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
import random
import colorsys

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
            )
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


class SolarPotentialEachFaceView(APIView):

    def calculate_hourly_potential(self, latitude, longitude, date, solar_irradiance, efficiency, areas):
        """
        Calculate hourly solar potential for each face based on manually defined exposure percentages.
        """
        hourly_potential = {"face1": [], "face2": [], "face3": [], "face4": []}

        # Manually defined exposure percentages for each face
        east_exposure = [1, 1, 1, 0.8, 0.7, 0.5, 0.3, 0.2, 0.1, 0, 0, 0, 0]
        west_exposure = list(reversed(east_exposure))
        south_exposure = [0, 0, 0, 0.8, 0.9, 1, 1, 1, 0.9, 0.8, 0.7, 0.6, 0.5]
        north_exposure = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.5, 0.4, 0.3, 0.2, 0, 0, 0]

        exposures = [east_exposure, south_exposure, west_exposure, north_exposure]

        for hour in range(6, 19):  # 6 AM to 6 PM
            hour_index = hour - 6

            for i, face in enumerate(["face1", "face2", "face3", "face4"]):
                potential_at_hour = areas[i] * solar_irradiance * efficiency / 1000
                adjusted_potential = potential_at_hour * exposures[i][hour_index]
                hourly_potential[face].append(round(adjusted_potential, 2))

            # Debug logs for hourly potential
            print(f"Hourly Potential (Hour {hour}): {hourly_potential}")

        # Calculate average potential for each face
        average_potential = {
            face: round(sum(potentials) / len(potentials), 2) if potentials else 0
            for face, potentials in hourly_potential.items()
        }

        # Calculate period of non-zero potential for each face in 12-hour format
        def convert_to_12_hour(hour):
            if hour == 0:
                return "12 AM"
            elif hour < 12:
                return f"{hour} AM"
            elif hour == 12:
                return "12 PM"
            else:
                return f"{hour - 12} PM"

        def consolidate_periods(potentials):
            periods = []
            start = None
            for i, p in enumerate(potentials):
                if p > 0 and start is None:
                    start = i
                elif p == 0 and start is not None:
                    periods.append({"start": convert_to_12_hour(6 + start), "end": convert_to_12_hour(6 + i - 1)})
                    start = None
            if start is not None:
                periods.append({"start": convert_to_12_hour(6 + start), "end": convert_to_12_hour(6 + len(potentials) - 1)})
            return periods

        non_zero_periods = {
            face: consolidate_periods(potentials) for face, potentials in hourly_potential.items()
        }

        return hourly_potential, average_potential, non_zero_periods

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

            hourly_potential, average_potential, non_zero_periods = self.calculate_hourly_potential(
                latitude, longitude, date, solar_irradiance, efficiency_bipv, areas
            )

            response_data = {
                "hourly_potential": hourly_potential,
                "average_potential": average_potential,
                "non_zero_periods": non_zero_periods
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import random
import colorsys

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import random
import colorsys

class FaceColorView(APIView):
    color_patterns = {}  # Map to store color patterns for dimensions

    def post(self, request):
        # Retrieve data from the request
        length = float(request.data.get('length'))
        breadth = float(request.data.get('breadth'))
        height = float(request.data.get('height'))

        # Calculate face areas
        areas = [height * length, height * breadth, height * length, height * breadth]

        # Generate or retrieve color patterns for each face
        face1_colors = self.generate_face_colors(areas[0], 20, 20)
        face2_colors = self.generate_face_colors(areas[1], 20, 20)
        face3_colors = self.generate_face_colors(areas[2], 20, 20)
        face4_colors = self.generate_face_colors(areas[3], 20, 20)

        # Return the color arrays in the response
        response_data = {
            "face1_colors": face1_colors,
            "face2_colors": face2_colors,
            "face3_colors": face3_colors,
            "face4_colors": face4_colors
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def generate_face_colors(self, face_area, num_rows, num_cols):
        num_rows=20
        num_cols=20
        # Check if a pattern exists for these dimensions
        key = f"{face_area}_{num_rows}_{num_cols}"
        if key in self.color_patterns:
            return self.color_patterns[key]

        # Generate a new color pattern
        colors = []
        for row in range(num_rows):
            row_colors = []
            for col in range(num_cols):
                # Adjust hue for the first 6 rows to be pure red
                hue = 0 if row < 6 else 0.08 + (row - 6) * 0.09 / (num_rows - 6)

                # Calculate RGB values based on hue and intensity
                red, green, blue = colorsys.hsv_to_rgb(hue, 1, 1)  # Full saturation and value for brighter colors
                red = int(255 * red)
                green = int(255 * green)
                blue = int(255 * blue)

                # Convert RGB to hex
                hex_color = '#{:02x}{:02x}{:02x}'.format(red, green, blue)

                row_colors.append(hex_color)
            colors.append(row_colors)

        # Store the generated pattern in the map
        self.color_patterns[key] = colors
        return colors