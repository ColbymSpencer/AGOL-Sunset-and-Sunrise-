# Import libraries
import arcpy
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo  # Only available in Python 3.9+
import pandas as pd

# Worspace and settings
arcpy.env.workspace = r'C:\Users\Spencer_C\Documents\ArcGIS\Projects\Sunrise Sunset Popups\Sunrise Sunset Popups.gdb'
arcpy.env.overwriteOutput = True

### GENERATE CENTROID TABLE ####
## table with the lat and long of the centroid of each park, the parks name, and the timezone it is in.
# Calculate lat, long coordinates
arcpy.management.CalculateGeometryAttributes("ParkBounds", [["lon", "CENTROID_X"], ["lat", "CENTROID_Y"]], coordinate_format = "DD")

# Join timezones to park boundaries
arcpy.analysis.SpatialJoin(target_features = r'C:\Users\Spencer_C\Documents\ArcGIS\Projects\Sunrise Sunset Popups\Sunrise Sunset Popups.gdb\ParkBounds',
                            join_features = r'C:\Users\Spencer_C\Documents\ArcGIS\Projects\Sunrise Sunset Popups\Sunrise Sunset Popups.gdb\Timezones',
                            out_feature_class = r'C:\Users\Spencer_C\Documents\ArcGIS\Projects\Sunrise Sunset Popups\Sunrise Sunset Popups.gdb\PB_Timezones')

# Create dicitonary for output
centroid_dict = {}

# Fill dictionary
with arcpy.da.SearchCursor("PB_Timezones", ['SITE_NAME', 'lon','lat','IANA_tz']) as cursor:
    for row in cursor:
        site_name = row[0]
        lon = row[1]
        lat = row[2]
        timezone = row[3]

        centroid_dict[site_name] = [(lat,lon),timezone]

print(centroid_dict)


#### CALCULATE SUNSET AND SUNRISE TIMES FOR EACH PARK #####
#function to calculate sunrise and sunset times
def calculate_sunrise_sunset(lat, lon, year, month, day, timezone_str):
    """
    Calculate sunrise and sunset times in local time zone.

    Inputs:
        lat, lon: Latitude and Longitude in degrees
        year, month, day: Date
        timezone_str: IANA time zone string (e.g., "America/New_York")
    Returns:
        (sunrise_local, sunset_local): Strings in "HH:MM" 24-hour format
    """

    def day_of_year(y, m, d):
        return (datetime(y, m, d) - datetime(y, 1, 1)).days + 1

    def format_time_utc_to_local(utc_hour, tz_str):
        dt_utc = datetime(year, month, day, int(utc_hour), int((utc_hour % 1) * 60), tzinfo=ZoneInfo("UTC"))
        dt_local = dt_utc.astimezone(ZoneInfo(tz_str))
        return dt_local.strftime("%I:%M %p").lstrip("0")

    # 1. Day of year
    N = day_of_year(year, month, day)
    lng_hour = lon / 15

    def calculate_event(is_sunrise):
        t = N + ((6 - lng_hour) / 24) if is_sunrise else N + ((18 - lng_hour) / 24)
        M = (0.9856 * t) - 3.289
        L = M + 1.916 * math.sin(math.radians(M)) + 0.020 * math.sin(math.radians(2 * M)) + 282.634
        L = L % 360

        RA = math.degrees(math.atan(0.91764 * math.tan(math.radians(L))))
        RA = RA % 360
        Lquadrant = (math.floor(L / 90)) * 90
        RAquadrant = (math.floor(RA / 90)) * 90
        RA += (Lquadrant - RAquadrant)
        RA /= 15

        sinDec = 0.39782 * math.sin(math.radians(L))
        cosDec = math.cos(math.asin(sinDec))
        cosH = (math.cos(math.radians(90.833)) - sinDec * math.sin(math.radians(lat))) / \
               (cosDec * math.cos(math.radians(lat)))

        if cosH > 1:
            return None  # Sun never rises
        elif cosH < -1:
            return None  # Sun never sets

        H = math.degrees(math.acos(cosH))
        if is_sunrise:
            H = 360 - H
        H = H / 15

        T = H + RA - (0.06571 * t) - 6.622
        UT = (T - lng_hour) % 24
        return UT

    sunrise_utc = calculate_event(is_sunrise=True)
    sunset_utc = calculate_event(is_sunrise=False)

    if sunrise_utc is None:
        sunrise_str = "Sun never rises"
    else:
        sunrise_str = format_time_utc_to_local(sunrise_utc, timezone_str)

    if sunset_utc is None:
        sunset_str = "Sun never sets"
    else:
        sunset_str = format_time_utc_to_local(sunset_utc, timezone_str)

    return sunrise_str, sunset_str

# Get date list
today = date.today()
dates = [today + timedelta(days=i) for i in range(365)]

# List to hold data in
records = []

# Loop through each row in df
for key, val in centroid_dict.items():
    lat,lon = val[0]
    tz = val[1]
    park = key

    for d in dates:
        sunrise, sunset = calculate_sunrise_sunset(lat, lon, d.year, d.month, d.day, tz)
        records.append({
            'park': park,
            #'latitude': lat,
            #'longitude': lon,
            'timezone': tz,
            'date': f'date is |{d}',
            'sunrise': f'sunrise is |{sunrise}',
            'sunset': f'sunset is |{sunset}'
        })

# Create table
sun_df = pd.DataFrame(records)
print(sun_df.head())

#### USE TABLE TO OVERWRITE CURRENT DATA####