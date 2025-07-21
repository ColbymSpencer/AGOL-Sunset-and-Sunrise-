# Import libraries
import arcpy
import math
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo  # Only available in Python 3.9+
import pandas as pd

def generate_centroids(host_gdb = r"\\floridadep\data\DRP\GIS\Codes and Scripts\Python3x\Sunset Sunrise Calculator\Sunrise Sunset Testing2\Sunrise Sunset Popups.gdb",
                        park_bounds = 'ParkBounds',
                        timezones = 'Timezones'):
    """
    From park boundaries and timezones feature claasses, create a dictionary with the
    centroids of each park in decimal degrees and the time zone the
    centroid intersects.

    Inputs:
        host_gdb: file path for a geodatabase containing:
            - park boundaries polyon featureclass
            - timezones polygon feature class
        park_bounds: name of the park boundary feature class
        timezones: name of the timezones feature class
    Returns:
        dictionary of the lat, long, and timezone for each park in the format
            park:[(lat,lon),timezone]
            Timezone is the IANA time zone string (e.g., "America/New_York")
    """
    # Worspace and settings
    arcpy.env.workspace = host_gdb
    arcpy.env.overwriteOutput = True

    # Calculate lat, long coordinates
    arcpy.management.CalculateGeometryAttributes(park_bounds, [["lon", "CENTROID_X"], ["lat", "CENTROID_Y"]], coordinate_format = "DD")

    # Join timezones to park boundaries
    arcpy.analysis.SpatialJoin(target_features = park_bounds,
                                join_features = timezones,
                                out_feature_class = 'PB_Timezones')

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
    print('Centroids generated')
    return centroid_dict

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

def generate_suntable(centorid_dict, date_range = 10):
    """
    Calculate sunrise and sunset times in local time zone.

    Inputs:
        centroid_dict (dict):
            in the format park:(lat,lon),timezone]
        date_range (int):
            Number of days from today to calculate the sunset and sunrise for
            less than or equal to 100 due to timeout issues when writing data
            to AGO
    Returns:
        sun_df (pandas dataframe): dataframe containing a record of sunset and sunrise times for every park in
        the input dictionary for every date from now until {date_range} days in the future
    """
    # Get date list
    today = date.today()
    dates = [today + timedelta(days=i) for i in range(date_range)]

    # List to hold data in
    records = []

    # Loop through each item in centroid dictionary
    for key, val in centroid_dict.items():
        lat,lon = val[0]
        tz = val[1]
        park = key

        for d in dates:
            sunrise, sunset = calculate_sunrise_sunset(lat, lon, d.year, d.month, d.day, tz)
            records.append({
                'park': park,
                'timezone': tz,
                'date': f'{d}',
                'sunrise': f'{sunrise}',
                'sunset': f'{sunset}'
            })

    # Create table
    sun_df = pd.DataFrame(records)
    print('Suntable generated')
    return sun_df

#### USE TABLE TO OVERWRITE CURRENT DATA####

def update_AGO_table(replacement_table, item_id = "c1bd4c99f7904eb9b629f0bb55e170eb"):
    # Import packages
    from arcgis.gis import GIS

    # Sign in to ArcGIS Online account
    gis = GIS(
            url="https://fdep.maps.arcgis.com/home/index.html",
            username="FLPARKSGIS",
            password="FLPARKSGIS1"
        )

    # Get suntable from AGO
    suntable_item = gis.content.get(item_id) # item id ('ServiceItemId') for the related table. Found in JSON for the table on AGO
    suntable_ago = suntable_item.tables[0]

    # Delete data in the suntable
    try:
        suntable_ago.manager.truncate()
    except Exception as e:
        print(f'Unable to truncate the related table of sunset and sunrise times: {e}')

    # Replace all the data in the suntable
    try:
        suntable_ago.edit_features(adds=sun_df.spatial.to_featureset())
        print('Related table updated successfully')
    except Exception as e:
        print(f'Unbable to add new data to the related table: {e}')

#local_copy_gdb = r"C:\Users\Spencer_C\Documents\ArcGIS\Projects\Sunrise Sunset Popups\Sunrise Sunset Popups.gdb"

centroid_dict = generate_centroids()
sun_df = generate_suntable(centroid_dict, date_range = 100)
update_AGO_table(replacement_table=sun_df)
