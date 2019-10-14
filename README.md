# WindFetch
WindFetch are python script used to calculate wind fetch (the unobstructed length which the wind can travel across water) from a given direction/angle/bearing. Existing tools may calculate these metrics from vector data e.g. points and polygon. This script calculates fetch on rasters. Similar tools for raster processing exists for use in [ArcGIS](https://umesc.usgs.gov/management/dss/wind_fetch_wave_models_2012update.html). 

As of now, this tools outputs a raster file containing 1 band for each wind direction. Optionally, a summary raster can also be saved containing min, mean and max values. 

Wind fetch can be determined from all water surface enclosed by land. Wind fetch metrics are used in wave and wind modeling, but may also be used as a variable in species-distribution modeling.

## Usage
An analysis migth start from a vector polygon file or a raster. The only requirement is that "water" cells in the raster share an id-value. This value is used to distinguish between water and land. 

Starting from a vector polygon file of a lake (.kml file in test folder), we rasterize and reproject the polygon to a raster in a project coordinate system. This can be done from the terminal using GDAL:

Re-project:  
`ogr2ogr -t_srs EPSG:25832 lake_test.sqlite lake_test.kml`

Rasterize polygon to raster where water surface is equal to 1:  
`gdal_rasterize -burn 1 -tr 25 25 lake_test.sqlite lake_test.tif`

Calculate fetch length from 8 directions and compute summary:  
`python WindFetchSimple.py -i test/lake_test.tif -o test/lake_test_fetch.tif -d '0,45,90,135,180,225,270,315' -id 1 -s test/lake_test_summary.tif`

Image showing the resulting fetch length rasters:
![alt text](https://github.com/KennethTM/WindFetch/blob/master/test/lake_test_fetch.png)

And the associated summary:
![alt text](https://github.com/KennethTM/WindFetch/blob/master/test/lake_test__summary.png)

## TO DO:
* Speed up calculations of fetch lengths using C or cython maybe?
* Calculate weighted fetch
* Implement fetch derived metrics for wave calculations
