from WindFetch import Waterbody, Fetch
import gdal
import matplotlib.pyplot as plt
import numpy as np

#Examples of functionality in WindFetch.py script
#Danish lake Gurre (source: OpenStreetMap) attached as .sqlite file in projected crs 
lake_vec = "test_files/gurre_lake"

#Rasterize vector file using gdal
lake_rast = gdal.Rasterize(lake_vec+".tif", lake_vec+".sqlite", xRes = 5, yRes = 5, burnValues = [1], noData = 0, outputType = gdal.GDT_Byte, creationOptions = ["COMPRESS=LZW"])
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

#Plot fetch along main directions and save as .png
fetch_max = np.nanmax(fetch_main.array)
for i, d in enumerate(dirs):
    arr = fetch_main.array[i]
    plt.subplot(2, 4, i+1)
    plt.imshow(arr, vmin = 0, vmax=fetch_max)
    plt.title("{} degrees".format(d))
    plt.xticks([])
    plt.yticks([])    

plt.subplots_adjust(right=0.9)

cax = plt.axes([0.95, 0.35, 0.025, 0.3])
plt.colorbar(cax=cax)
plt.savefig(lake_vec+"_fetch_main.png", bbox_inches= "tight")

#Plot fetch along main directions with minor direction averaging and save as .png
for i, d in enumerate(dirs):
    arr = fetch_minor.array[i]
    plt.subplot(2, 4, i+1)
    plt.imshow(arr, vmin = 0, vmax=fetch_max)
    plt.title("{} degrees".format(d))
    plt.xticks([])
    plt.yticks([])    

plt.subplots_adjust(right=0.9)

cax = plt.axes([0.95, 0.35, 0.025, 0.3])
plt.colorbar(cax=cax)
plt.savefig(lake_vec+"_fetch_minor.png", bbox_inches= "tight")

#Plot summary of fetch along main directions
for i, d in enumerate(["min", "mean", "max"]):
    arr = fetch_main_summary.array[i]
    #arr[arr == 0] = np.nan
    plt.subplot(1, 3, i+1)
    plt.imshow(arr, vmin = 0, vmax=fetch_max)
    plt.title("{} fetch".format(d))
    plt.xticks([])
    plt.yticks([])    

plt.subplots_adjust(right=0.9)

plt.colorbar(cax=cax)
plt.savefig(lake_vec+"_fetch_main_summary.png", bbox_inches= "tight")
