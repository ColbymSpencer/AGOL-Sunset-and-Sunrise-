# AGOL-Sunset-and-Sunrise-
The Florida Parks Service wants to give guests and staff an integrated way to view sunset and sunrise times in maps on ArcGIS Online (AGO) popup. AGO uses the arcade language to perform popup calculations but arcade does not have the functions to find the sunset and sunrise times quickly. Instead, sunrise and sunset times are stored in a one-to-many related table using the park name as a key. When a park is selected on AGO, an arcade expression filters the related table for a match to the current date, and pulls the sunset and sunrise times for the popup.

## The Workflow
Park boundaries -> park centroids
park centorids + timezones -> table with park names, centroid coordinates, and the timezone the centroid intersects -> convert to dictionary
generate a list of dates to get the sunrise/sunset times for
for each date in the list calculate the sunset and sunrise times in local time for the park and store them in a dataframe
remove all the current values in a related table published to AGO and fill the table with the newly generated values

