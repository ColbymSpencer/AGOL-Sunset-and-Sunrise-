# AGOL-Sunset-and-Sunrise-
The Florida Parks Service wants to give guests and staff an integrated way to view sunset and sunrise times in maps on ArcGIS Online (AGO) popups. AGO uses the arcade language to perform popup calculations but arcade does not have the functions to find the sunset and sunrise times quickly. Instead, sunrise and sunset times are stored in a one-to-many related table using the park name as a key. When a park is selected on AGO, an arcade expression filters the related table for a match to the current date, and pulls the sunset and sunrise times for the popup.

## The Workflow
<img width="623" height="262" alt="Polygon to Centroid" src="https://github.com/user-attachments/assets/c56174f5-3033-49fc-8140-ab3ffb1877c3" />

* Park boundaries -> park centroids

![Centroid with Timezone Flow](https://github.com/user-attachments/assets/b1561d3d-29fc-4ac7-8951-958f410b9d10)

* park centorids + timezones -> table with park names, centroid coordinates, and the timezone the centroid intersects
* generate a list of dates to get the sunrise/sunset times, for each date in the list calculate the sunset and sunrise times in local time for the park and store them in a dataframe
* remove all the current values in a related table published to AGO and fill the table with the newly generated values

