import snowflake.connector
import os

from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

required_vars = ["SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD", "SNOWFLAKE_ACCOUNT"]
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

try:
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "WEATHER_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "WEATHER_DB"),
        schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW")
    )

    cur = conn.cursor()
    print("Connected to snowflake!")

    cur.execute("TRUNCATE TABLE DAILY_WEATHER")
    cur.execute("TRUNCATE TABLE HOURLY_WEATHER")

    print("Old data removed")

    cur.execute("REMOVE @WEATHER_STAGE")

    cur.execute("PUT file:///opt/airflow/logs/daily_weather.csv @WEATHER_STAGE OVERWRITE=TRUE")
    cur.execute("PUT file:///opt/airflow/logs/hourly_weather.csv @WEATHER_STAGE OVERWRITE=TRUE")

    print("Files uploaded to stage")

    cur.execute("""
    COPY INTO DAILY_WEATHER
    FROM @WEATHER_STAGE/daily_weather.csv
    FILE_FORMAT = (
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    )
    """)

    cur.execute("""
    COPY INTO HOURLY_WEATHER
    FROM @WEATHER_STAGE/hourly_weather.csv
    FILE_FORMAT = (
    TYPE = CSV
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    )
    """)

    print("Data loaded into tables")

    print("Pipeline completed")

    print(datetime.now(), "Pipeline completed successfully")

except Exception as e:
    print("An error occurred:", e)

finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
