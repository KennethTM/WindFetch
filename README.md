# WindFetch
WindFetch are some python scripting used to calculate wind fetch length along a direction across a water surface. Wind fetch is the unobstructed length which the wind can travel across a water surface from a given direction. Wind fetch can be determined from all water surface enclosed by land. Wind fetch metrics are used in wave, wind and ecological modeling. Existing tools may calculate these metrics from vector data e.g. points and polygon. This script calculates the wind fetch for each cell in rasters. Similar tools for raster processing exists for use in [ArcGIS](https://umesc.usgs.gov/management/dss/wind_fetch_wave_models_2012update.html). The tool can be used to calculate fetch length in the most simple way (along one direction) or where each length is an average of multiple minor direction spread around each direction. Weighting and calculation of summary statistics can also be performed. 

## Example 
See the waterbody_test.py for some examples of useage. The proces may start with a vector polygon of a lake. The vector is rasterized to a grid where "water" cells share an id value to distinguish between water and land. Using this grid, fetch lengths and other properties can be determined.

```python
from waterbody_refac import Waterbody, Fetch
import gdal
import matplotlib.pyplot as plt
import numpy as np

#Run test of fetch functions
#Danish lake Gurre (source: OpenStreetMap) attached as .sqlite file in projected crs 
lake_vec = "test_files/gurre_lake"

#Rasterize vector file using gdal
lake_rast = gdal.Rasterize(lake_vec+".tif", lake_vec+".sqlite", xRes = 5, yRes = 5, burnValues = [1], noData = 0, outputType = gdal.GDT_Byte, creationOptions = ["COMPRESS=LZW"], )
lake_rast = None

#Read lake from .tif file
lake = Waterbody.read_waterbody(lake_vec+".tif", 1)

dirs = [0, 45, 90, 135, 180, 225, 270, 315]

#Fetch along main directions
fetch_main = lake.fetch(dirs)

#Summary statistics of calculated fetches
fetch_main_summary = fetch_main.summary(["min", "mean", "max"])

#Apply weighting to each direction
dirs_weights = [0.1, 0.3, 0.1, 0.2, 0, 0, 0.2, 0.1]

fetch_main_weight = fetch_main.weighting(dirs_weights)

#Calculated weighted mean
fetch_main_weight_mean = fetch_main_weight.summary(["mean"])

#Fetch along main directions each calculated as the average of 5 directions with a distance of 3 degrees
fetch_minor = lake.fetch(dirs, minor_directions = 5, minor_interval = 3)

#Write to file
fetch_minor.write_waterbody(lake_vec+"_fetch_minor.tif")
```
 
The resulting grids are visualized below:

**Fetch length along main directions**

![alt text](https://github.com/KennethTM/WindFetch/blob/master/test_files/gurre_lake_fetch_main.png)

**Fetch length along main directions with minor direction averaging**

![alt text](https://github.com/KennethTM/WindFetch/blob/master/test_files/gurre_lake_fetch_minor.png)

**Summary of fetch lengths along main directions**

![alt text](https://github.com/KennethTM/WindFetch/blob/master/test_files/gurre_lake_fetch_main_summary.png)
