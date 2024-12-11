from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
import pickle
import os
from datetime import datetime
import pytz
from pysolar.solar import get_altitude, get_azimuth
from django.conf import settings
import joblib

# Load the trained model using BASE_DIR
MODEL_PATH = os.path.join(settings.BASE_DIR, "MlModels", "shadow_ratio_model.pkl")
with open(MODEL_PATH, "rb") as file:
    model = pickle.load(file)

class ShadowRatioPredictionView(APIView):
    """
    API View to predict shadow ratios for North, South, East, and West sides
    based on the input data, including solar Azimuth and Elevation angles.
    """
    def post(self, request, *args, **kwargs):
        try:
            # Get input data from the request
            input_data = request.data
            
            # Ensure the datetime field is provided
            if "datetime" not in input_data:
                return Response(
                    {"error": "The 'datetime' field is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Parse datetime field
            datetime_str = input_data["datetime"]
            try:
                # Parse datetime in the format "YYYY-MM-DD HH:MM:SS"
                naive_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
                # Convert naive datetime to timezone-aware datetime (India Timezone)
                timezone = pytz.timezone("Asia/Kolkata")
                observation_time = timezone.localize(naive_datetime)
            except ValueError:
                return Response(
                    {"error": "Invalid datetime format. Use 'YYYY-MM-DD HH:MM:SS'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Location for solar calculations
            latitude = 23.030357
            longitude = 72.517845
            
            # Calculate Azimuth and Elevation angles
            elevation_angle = get_altitude(latitude, longitude, observation_time)
            azimuth_angle = get_azimuth(latitude, longitude, observation_time)
            
            # Add calculated fields to input data
            input_data["Azimuth_Angle"] = azimuth_angle
            input_data["Elevation_Angle"] = elevation_angle
            
            # Remove datetime field (if not needed in the model)
            input_data.pop("datetime", None)
            
            # Convert input data into a pandas DataFrame
            input_df = pd.DataFrame([input_data])
            
            # Predict shadow ratios using the trained model
            predictions = model.predict(input_df)
            
            # Prepare the response
            response_data = {
                "North_Side_Shadow_Ratio": predictions[0][0],
                "South_Side_Shadow_Ratio": predictions[0][1],
                "East_Side_Shadow_Ratio": predictions[0][2],
                "West_Side_Shadow_Ratio": predictions[0][3],
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Return an error response if something goes wrong
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


# Define the absolute path to the model file
MODEL_PATH = os.path.join(settings.BASE_DIR, "MlModels", "linear_regression_model.pkl")

# Check if the model file exists
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

# Load the trained model
model = joblib.load(MODEL_PATH)

class EmissionPredictionView(APIView):
    """
    API View to predict carbon emissions based on energy produced (kWh).
    """
    def get(self, request, *args, **kwargs):
        """
        Simple welcome message for the API.
        """
        return Response({"message": "Welcome to the Emission Prediction API!"}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Predict carbon emissions from the provided energy produced (kWh).
        """
        try:
            # Extract input data from the request
            data = request.data
            
            # Ensure 'energy_produced' is in the data
            if "energy_produced" not in data:
                return Response(
                    {"error": "'energy_produced' field is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the value of energy produced
            energy_produced = data["energy_produced"]

            # Ensure it's a valid number
            if not isinstance(energy_produced, (int, float)):
                return Response(
                    {"error": "'energy_produced' must be a numeric value."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Make the prediction
            prediction = model.predict([[energy_produced]])
            
            # Return the prediction as JSON
            return Response(
                {"predicted_carbon_emission": prediction[0]},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            # Return an error response if something goes wrong
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
