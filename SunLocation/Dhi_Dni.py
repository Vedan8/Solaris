import pvlib
import pandas as pd
import numpy as np

# Example usage:
latitude = 23.037454
longitude = 72.569816
ghi = 800 
time = '2023-10-10 12:00:00' 

# Create a Location object
location = pvlib.location.Location(latitude, longitude)

# Create a DataFrame with the time and GHI
times = pd.DatetimeIndex([time])
ghi_series = pd.Series([ghi], index=times)

# Get solar position
solar_position = location.get_solarposition(times)

# Print the zenith angle
print(f"Zenith Angle: {solar_position['zenith'].values[0]} degrees")

# Estimate DHI using the Erbs model
dhi_series = pvlib.irradiance.erbs(ghi_series, solar_position['zenith'], times)['dhi']

# Calculate DNI
dni_series = (ghi_series - dhi_series) / np.cos(np.radians(solar_position['zenith']))

return (
    dhi_series.values[0],
    dni_series.values[0]
)