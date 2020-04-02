# WindFetch
WindFetch are some python scripting used to calculate wind fetch over water surface. Wind fetch is the unobstructed length which the wind can travel across a water surface from a given direction. Wind fetch can be determined from all water surface enclosed by land. Wind fetch metrics are used in wave, wind and ecological modeling. Existing tools may calculate these metrics from vector data e.g. points and polygon. This script calculates the wind fetch for each cell in rasters. Similar tools for raster processing exists for use in [ArcGIS](https://umesc.usgs.gov/management/dss/wind_fetch_wave_models_2012update.html). The tool simply calculates fetch along a supplied direction(s). It can also create summary grids with minimum, mean and maximum fetch values. A weighted fetch grid can also created by supplying a weighted for each direction.

## Example 
See the waterbody_test.py for an example of useage. This starts with a vector polygon of a lake. The vector is rasterized to a grid where "water" cells share an id value to distinguish between water and land.

From here, fetch can be calculated by supplying directions:
 
![alt text](https://github.com/KennethTM/WindFetch/blob/master/test_files/gurre_lake_fetch.png)

Using the calculated fetch grids a summary can also be computed:  
![alt text](https://github.com/KennethTM/WindFetch/blob/master/test_files/gurre_lake_fetch_summary.png)
