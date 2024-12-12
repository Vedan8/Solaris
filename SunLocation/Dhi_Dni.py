# import math
# from datetime import datetime

# def calculate_solar_radiation(latitude, longitude, altitude, date_time, ghi_kwh_per_day):
#     """
#     Comprehensive solar radiation calculation for a given location.
    
#     Parameters:
#     - latitude: Latitude of the location in decimal degrees
#     - longitude: Longitude of the location in decimal degrees
#     - altitude: Altitude in meters
#     - date_time: Datetime object
#     - ghi_kwh_per_day: Global Horizontal Irradiance in kWh/m²/day
    
#     Returns:
#     - Dictionary with solar radiation components in kWh/m²/day
#     """
#     # Day of Year
#     day_of_year = date_time.timetuple().tm_yday
    
#     # Solar Declination
#     solar_declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
    
#     # Calculate Solar Time
#     def calculate_solar_time(date_time, longitude):
#         standard_meridian = 0
#         time_equation = 229.18 * (0.000075 + 0.001868 * math.cos(math.radians(360 * day_of_year / 365.25)) - 
#                                    0.032077 * math.sin(math.radians(360 * day_of_year / 365.25)) - 
#                                    0.014615 * math.cos(2 * math.radians(360 * day_of_year / 365.25)) - 
#                                    0.040849 * math.sin(2 * math.radians(360 * day_of_year / 365.25)))
        
#         lstm = standard_meridian * 15
#         time_offset = 4 * (longitude - lstm) + time_equation
#         solar_time = date_time.hour + (date_time.minute + time_offset) / 60
        
#         return solar_time
    
#     solar_time = calculate_solar_time(date_time, longitude)
    
#     # Hour Angle
#     hour_angle = 15 * (solar_time - 12)
    
#     # Solar Zenith Angle Calculation
#     def calculate_zenith_angle(latitude, solar_declination, hour_angle):
#         latitude_rad = math.radians(latitude)
#         declination_rad = math.radians(solar_declination)
#         hour_angle_rad = math.radians(hour_angle)
        
#         zenith = math.acos(
#             math.sin(latitude_rad) * math.sin(declination_rad) + 
#             math.cos(latitude_rad) * math.cos(declination_rad) * math.cos(hour_angle_rad)
#         )
        
#         return math.degrees(zenith)
    
#     solar_zenith_angle = calculate_zenith_angle(latitude, solar_declination, hour_angle)
    
#     # Clearness Index Calculation
#     def calculate_clearness_index(ghi):
#         # Typical solar constant (converted to kWh/m²/day)
#         solar_constant = 1.367 * 24 / 1000  # 1.367 kW/m² * 24 hours / 1000 to get kWh/m²/day
        
#         # Earth orbit correction
#         earth_orbit_correction = 1 + 0.033 * math.cos(math.radians(360 * day_of_year / 365))
        
#         # Extraterrestrial radiation
#         extraterrestrial_radiation = solar_constant * earth_orbit_correction
        
#         # Clearness index
#         return min(ghi / extraterrestrial_radiation, 1)
    
#     clearness_index = calculate_clearness_index(ghi_kwh_per_day)
    
#     # DNI (Direct Normal Irradiance) Calculation
#     def calculate_dni(ghi, zenith):
#         # Prevent division by zero and handle extreme angles
#         zenith_rad = math.radians(zenith)
        
#         # Calculate DNI
#         dni = ghi / max(math.cos(zenith_rad), 1e-6)  # Avoid division by zero
        
#         return dni
    
#     dni_kwh_per_day = calculate_dni(ghi_kwh_per_day, solar_zenith_angle)
    
#     # DHI (Diffuse Horizontal Irradiance) Calculation
#     def calculate_dhi(ghi, dni, zenith):
#         zenith_rad = math.radians(zenith)
        
#         # Calculate DHI using the rearranged equation
#         dhi = ghi - (dni * math.cos(zenith_rad))
        
#         return max(dhi, 0)  # Ensure DHI is not negative
    
#     dhi_kwh_per_day = calculate_dhi(ghi_kwh_per_day, dni_kwh_per_day, solar_zenith_angle)
    
#     # Return results as a dictionary
#     return {
#         'GHI': ghi_kwh_per_day,
#         'DNI': dni_kwh_per_day,
#         'DHI': dhi_kwh_per_day,
#         'Solar Zenith Angle': solar_zenith_angle,
#         'Clearness Index': clearness_index
#     }

# # Example usage:
# latitude = 23.0225   # Ahmedabad latitude
# longitude = 72.5714   # Ahmedabad longitude
# altitude = 53         # Altitude in meters
# date_time = datetime(2024, 12, 12)   # Example date
# ghi_kwh_per_day = 5.5   # Example GHI value

# solar_radiation_results = calculate_solar_radiation(latitude, longitude, altitude, date_time, ghi_kwh_per_day)

# # Print the results
# print(solar_radiation_results)
