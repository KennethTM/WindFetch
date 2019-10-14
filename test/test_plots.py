#Plot of test examples
import rasterio
from matplotlib import pyplot as plt
import numpy as np

#plot calculated fetches
fetch = "/home/kenneth/Documents/WindFetch/test/lake_test_fetch.tif"

summary = "/home/kenneth/Documents/WindFetch/test/lake_test_summary.tif"

fetch_open = rasterio.open(fetch)

dirs = [0, 45, 90, 135, 180, 225, 270, 315]

for i, d in enumerate(dirs):
    arr = fetch_open.read(i+1).astype("float")
    arr[arr == 0] = np.nan
    plt.subplot(2, 4, i+1)
    plt.imshow(arr, vmin = 0, vmax=4900)
    plt.title("{} degrees".format(d))
    plt.xticks([])
    plt.yticks([])    

plt.subplots_adjust(top=0.7)

cax = plt.axes([1, 0, 0.1, 0.8])
plt.colorbar(plt.imshow(arr), cax=cax)
#plt.show()
plt.savefig("/home/kenneth/Documents/WindFetch/test/lake_test_fetch.png", bbox_inches= "tight")

#plot calculated fetch summary
summary_open = rasterio.open(summary)

sumvars = ["Min.", "Mean.", "Max."]

for i, d in enumerate(sumvars):
    arr = summary_open.read(i+1).astype("float")
    arr[arr == 0] = np.nan
    plt.subplot(1, 3, i+1)
    plt.imshow(arr, vmin = 0, vmax=4900)
    plt.title("{} fetch".format(d))
    plt.xticks([])
    plt.yticks([])    

plt.subplots_adjust(top=0.7)

cax = plt.axes([1, 0, 0.1, 0.8])
plt.colorbar(plt.imshow(arr), cax=cax)
#plt.show()
plt.savefig("/home/kenneth/Documents/WindFetch/test/lake_test__summary.png", bbox_inches= "tight")


