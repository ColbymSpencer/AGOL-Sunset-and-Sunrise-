#Script to update the PARK NWS Intersect AGOl feature Layer for use in the web map and dashboard
#
#
#
# Importing variables
import arcpy, sys, traceback, os, glob, time
from datetime import datetime, timedelta
import pytz
import zoneinfo
from arcpy import env

print("Libraries Imported")

# overwrite file if it exists
env.overwriteOutput = True

# date format
date = (time.strftime("%m_%d_%Y"))

# Assuming you have a datetime object named 'my_timestamp'
my_timestamp = datetime.now()

# Create a timedelta object representing 4 hours
time_to_add = timedelta(hours=4)

# Add the timedelta to your timestamp
new_timestamp = my_timestamp + time_to_add

from time import strftime
print("AGOL update of Parks in NWS Warnings and Watches Started " + date +  " @ " + str(strftime('%T')))


#Variables
Parks_NWS_Dissolve = "\\\\floridadep\\data\\DRP\\GIS\\Special-Projects\\Hurricanes\\Parks and Warnings Feature Updates\\Park data for NWS Intersect.gdb\\Parks_NWS_Dissolve"
Park_Boundaries_Statewide = "\\\\floridadep\\data\\DRP\\GIS\\Special-Projects\\Hurricanes\\Parks and Warnings Feature Updates\\Park data for NWS Intersect.gdb\\Park_Boundaries_Statewide"
Parks_NWS_Pairwise_Intersect = "\\\\floridadep\\data\\DRP\\GIS\\Special-Projects\\Hurricanes\\Parks and Warnings Feature Updates\\Park data for NWS Intersect.gdb\\Parks_NWS_Pairwise_Intersect"

# Open/Reference ArcPro Project with Park and NWS data loaded
aprx = arcpy.mp.ArcGISProject(r"\\floridadep\data\DRP\GIS\Special-Projects\Hurricanes\Parks and Warnings Feature Updates\Parks and NWS Alerts.aprx")

time.sleep(180)
print("Sleep 180 Seconds - Opening ArcPro Project")

# Selecting existing Map from ArcPro project referenced above with layers to export
m = aprx.listMaps("Map")[0]
Parks_NWS_Layer = m.listLayers("AGOL Parks and NWS") [0]
WWA_Rest_Service_WatchesWarnings = m.listLayers("WatchesWarnings") [0]

time.sleep(45)
print("Sleep 45 Seconds")

# Process: Step 2 Pairwise Intersect (Pairwise Intersect) (analysis)
arcpy.analysis.PairwiseIntersect(in_features=[Park_Boundaries_Statewide, WWA_Rest_Service_WatchesWarnings], out_feature_class=Parks_NWS_Pairwise_Intersect)
print("Pairwise Intersect Complete")

time.sleep(45)
print("Sleep 45 Seconds")

# Process: Step 3 Dissolve (Dissolve) (management)
arcpy.management.Dissolve(in_features=Parks_NWS_Pairwise_Intersect, out_feature_class=Parks_NWS_Dissolve, dissolve_field=["SITE_NAME", "prod_type", "url_1", "DISTRICT"])
print("Dissolve Complete")

time.sleep(45)
print("Sleep 45 Seconds")

# Process: Step 4 Calculate Edited Date Fields (management)
arcpy.management.CalculateField(in_table=Parks_NWS_Dissolve, field="LastEdited", expression="new_timestamp", expression_type="PYTHON3", field_type="DATE")
print("Date Field Calculated")

time.sleep(45)
print("Sleep 45 Seconds")

# Process: Step 1 Delete Rows from Parks_NWS_Dissolve (Delete Rows) (management)
#arcpy.management.DeleteRows(Parks_NWS_Layer)[0]-This had issues so used truncate instead
arcpy.TruncateTable_management(Parks_NWS_Layer)
print("Delete Existing AGOL Parks NWS data")

time.sleep(45)
print("Sleep 45 Seconds")

# Process: Append (Append) (management)
arcpy.management.Append(inputs=[Parks_NWS_Dissolve], target=Parks_NWS_Layer, schema_type="NO_TEST")[0]
print("Append Complete")

print ("Completed @ " + str(strftime('%T')))

# Using sys.exit()
print("Exiting IDLE...")
sys.exit()
