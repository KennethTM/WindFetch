from waterbody import *
import gdal
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid
import time

#Run test of fetch functions
#Danish lake Gurre (source: OpenStreetMap) attached as .sqlite file in projected crs 
lake_vec = "test_files/gurre_lake"

#Rasterize vector file using gdal
lake_rast = gdal.Rasterize(lake_vec+".tif", lake_vec+".sqlite", xRes = 10, yRes = 10, burnValues = [1], noData = 0, outputType = gdal.GDT_Byte, creationOptions = ["COMPRESS=LZW"], )
lake_rast = None

#Read lake from .tif file
lake = read_waterbody(lake_vec+".tif", 1)

#Calculate fetch
fetch_dirs = [0, 45, 90, 135, 180, 225, 270, 315]
fetch_weigths = [1.0]*8
lake_fetch = lake.fetch(directions = fetch_dirs, weigths=fetch_weigths, method_vect=True, minor_directions= 3, minor_interval= 5)

t0 = time.time()
fetch_old = lake.fetch(fetch_dirs, fetch_weigths)
t1 = time.time()

t2 = time.time()
fetch_new = lake.fetch(fetch_dirs, fetch_weigths, method_vect=True)
t3 = time.time()

#t4 = time.time()
#fetch_new = lake.fetch(fetch_dirs, fetch_weigths, method_vect=True, multi=True)
#t5 = time.time()

print("Old method: %s" % (t1-t0))
print("New method: %s" % (t3-t2))
#print("New method and multicore: %s" % (t5-t4))

#Calculate fetch summary
summary_stats = ["min", "mean", "max"]
lake_fetch_summary = lake_fetch.summary(summary_stats)

#Save fetch directions as raster band
save_waterbody(lake_fetch, lake_vec+"_fetch.tif")

#Save fetch summary
save_waterbody(lake_fetch_summary, lake_vec+"_fetch_summary.tif")

#Plot fetch layers and save .png file
fetch_max = np.nanmax(lake_fetch.array)
for i, d in enumerate(fetch_dirs):
    arr = lake_fetch.array[i]
    arr[arr == 0] = np.nan
    plt.subplot(2, 4, i+1)
    plt.imshow(arr, vmin = 0, vmax=fetch_max)
    plt.title("{} degrees".format(d))
    plt.xticks([])
    plt.yticks([])    

plt.subplots_adjust(right=0.9)

cax = plt.axes([0.95, 0.35, 0.025, 0.3])
plt.colorbar(cax=cax)
plt.savefig(lake_vec+"_fetch.png", bbox_inches= "tight")

#Repeat for fetch summary
for i, d in enumerate(["min", "mean", "max"]):
    arr = lake_fetch_summary.array[i]
    arr[arr == 0] = np.nan
    plt.subplot(1, 3, i+1)
    plt.imshow(arr, vmin = 0, vmax=fetch_max)
    plt.title("{} fetch".format(d))
    plt.xticks([])
    plt.yticks([])    

plt.subplots_adjust(right=0.9)

plt.colorbar(cax=cax)
plt.savefig(lake_vec+"_fetch_summary.png", bbox_inches= "tight")
