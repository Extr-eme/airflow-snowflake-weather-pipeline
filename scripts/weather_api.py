import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 27.7017,
	"longitude": 85.3206,
	"daily": ["sunrise", "sunset", "rain_sum", "wind_speed_10m_max", "wind_gusts_10m_max"],
	"hourly": ["temperature_2m", "wind_speed_80m", "relative_humidity_2m", "apparent_temperature", "precipitation_probability", "precipitation", "rain"],
	"current": ["temperature_2m", "is_day", "rain", "precipitation"],
	"timezone": "Asia/Kathmandu",
	"past_days": 0,
	"forecast_days": 7,
}
responses = openmeteo.weather_api(url, params = params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process current data. The order of variables needs to be the same as requested.
current = response.Current()
current_time = pd.to_datetime(current.Time(), unit="s", utc=True).tz_convert("Asia/Kathmandu")


current_temperature_2m = current.Variables(0).Value()
current_is_day = current.Variables(1).Value()
current_rain = current.Variables(2).Value()
current_precipitation = current.Variables(3).Value()

print(f"Current time: {current_time}")
print(f"Current temperature_2m: {current_temperature_2m}")
print(f"Current is_day: {current_is_day}")
print(f"Current rain: {current_rain}")
print(f"Current precipitation: {current_precipitation}")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
hourly_wind_speed_80m = hourly.Variables(1).ValuesAsNumpy()
hourly_relative_humidity_2m = hourly.Variables(2).ValuesAsNumpy()
hourly_apparent_temperature = hourly.Variables(3).ValuesAsNumpy()
hourly_precipitation_probability = hourly.Variables(4).ValuesAsNumpy()
hourly_precipitation = hourly.Variables(5).ValuesAsNumpy()
hourly_rain = hourly.Variables(6).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time() + response.UtcOffsetSeconds(), unit = "s", utc = True),
	end =  pd.to_datetime(hourly.TimeEnd() + response.UtcOffsetSeconds(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}

hourly_data["temperature_2m"] = hourly_temperature_2m
hourly_data["wind_speed_80m"] = hourly_wind_speed_80m
hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
hourly_data["apparent_temperature"] = hourly_apparent_temperature
hourly_data["precipitation_probability"] = hourly_precipitation_probability
hourly_data["precipitation"] = hourly_precipitation
hourly_data["rain"] = hourly_rain

hourly_dataframe = pd.DataFrame(data = hourly_data)
hourly_dataframe["city"] = "Kathmandu"
hourly_dataframe["date"] = hourly_dataframe["date"].dt.tz_convert("Asia/Kathmandu")
print("\nHourly data\n", hourly_dataframe)

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_sunrise = daily.Variables(0).ValuesInt64AsNumpy()
daily_sunset = daily.Variables(1).ValuesInt64AsNumpy()
daily_rain_sum = daily.Variables(2).ValuesAsNumpy()
daily_wind_speed_10m_max = daily.Variables(3).ValuesAsNumpy()
daily_wind_gusts_10m_max = daily.Variables(4).ValuesAsNumpy()

daily_data = {"date": pd.date_range(
	start = pd.to_datetime(daily.Time() + response.UtcOffsetSeconds(), unit = "s", utc = True),
	end =  pd.to_datetime(daily.TimeEnd() + response.UtcOffsetSeconds(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = daily.Interval()),
	inclusive = "left"
)}

daily_data["sunrise"] = daily_sunrise
daily_data["sunset"] = daily_sunset
daily_data["rain_sum"] = daily_rain_sum
daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
daily_data["wind_gusts_10m_max"] = daily_wind_gusts_10m_max

daily_dataframe = pd.DataFrame(data = daily_data)
daily_dataframe["city"] = "Kathmandu"
daily_dataframe["date"] = daily_dataframe["date"].dt.tz_convert("Asia/Kathmandu")

daily_dataframe["sunrise"] = pd.to_datetime(
    daily_dataframe["sunrise"], unit="s", utc=True
).dt.tz_convert("Asia/Kathmandu").dt.time

daily_dataframe["sunset"] = pd.to_datetime(
    daily_dataframe["sunset"], unit="s", utc=True
).dt.tz_convert("Asia/Kathmandu").dt.time


daily_dataframe["date"] = daily_dataframe["date"].dt.date

hourly_dataframe["date"] = hourly_dataframe["date"].dt.tz_localize(None)
hourly_dataframe.to_csv("/opt/airflow/logs/hourly_weather.csv", index=False)
daily_dataframe.to_csv("/opt/airflow/logs/daily_weather.csv", index=False)
