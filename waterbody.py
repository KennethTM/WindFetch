import numpy as np
import rasterio
from scipy.ndimage.interpolation import rotate
import copy

#The waterbody class
#Requires raster, profile, resolution and id value for water cells
class waterbody():

    def __init__(self, array, profile, water_id = None):
        self.array = np.array(array).astype("float32")
        self.count = self.array.shape[0]
        
        self.profile = profile
        self.nrow = self.profile["height"]
        self.ncol = self.profile["width"]
        self.resolution = self.profile["transform"][0]
        self.profile["count"] = self.count

        if water_id:
            self.water_id = water_id
            self.landwater = np.where(self.array == self.water_id, -1, np.nan)
      
    #Main function for calculating fetch from several directions
    def fetch(self, directions, weigths = None):

        #Function to calculate length
        def fetch_length(array, resolution):
            nrow, ncol = array.shape
            fetch = [np.nan]*ncol
            list_fetch = []

            for row in range(nrow):
            
                land = array[row]
                
                for col in range(ncol):
                    if np.isnan(land[col]):
                        fetch[col] = 0
                    else:
                        if fetch[col] >= 0:
                            fetch[col] = fetch[col] + resolution
                        else:
                            fetch[col] = fetch[col] - resolution
                            
                list_fetch.append(list(fetch))
                
            return(np.array(list_fetch))

        #Function to estimate padding required before rotation
        def estimated_pad(nrow, ncol, resolution):
            xlen = resolution*ncol
            ylen = resolution*nrow
            padwidth = np.sqrt(xlen**2+ylen**2) - min([xlen, ylen])
            return(int(padwidth/2/resolution)+1)

        #Function performing the padding
        def padding(array, pad_width, fill_value, inverse = False):
            if inverse == False:
                arr = np.pad(array, pad_width = pad_width, mode = "constant", constant_values = fill_value)
            else:
                arr = array[pad_width:-pad_width, pad_width:-pad_width]
            return(arr)

        pad_width = estimated_pad(self.nrow, self.ncol, self.resolution)
            
        array_pad = padding(self.landwater, pad_width, np.nan)
            
        dir_arrays = []

        for d in directions:
            array_rot = rotate(array_pad, angle=d, reshape=False, mode = "constant", cval = np.nan, order = 0)
        
            array_fetch = fetch_length(array_rot, self.resolution)
            
            array_inv_rot = rotate(array_fetch, angle=360-d, reshape=False, mode = "constant", cval = np.nan, order = 0)
        
            array_inv_pad = padding(array_inv_rot, pad_width, -self.resolution, inverse = True)
        
            dir_arrays.append(array_inv_pad)

        if weigths:
            dir_arrays_weighted = [i*w for i, w in zip(dir_arrays, weigths)]
            fetch_array = np.stack(dir_arrays_weighted)*(self.landwater*-1)
        else:
            fetch_array = np.stack(dir_arrays)*(self.landwater*-1)

        fetch_profile = self.profile.copy()
        waterbody_fetch = waterbody(fetch_array, fetch_profile)
        waterbody_fetch.directions = directions

        if weigths:
            waterbody_fetch.weights = weigths

        return(waterbody_fetch)        

    def summary(self, stats):

        stats_dict = {"mean": np.mean, "min": np.min, "max": np.max, "range": np.ptp, "std": np.std, "median": np.median, "var": np.var}

        summary_list = [stats_dict[i](self.array, axis = 0) for i in stats]
        summary_array = np.stack(summary_list)

        summary_profile = self.profile.copy()
        waterbody_summary = waterbody(summary_array, summary_profile)
        waterbody_summary.stats = stats

        return(waterbody_summary)

#Function for reading a raster and convert to object waterbody
def read_waterbody(path, water_id):
    
    with rasterio.open(path) as src:
        array = src.read(1)
        profile = src.profile
        
    return(waterbody(array, profile, water_id))

#Write waterbody object to raster with one layer for each fetch direction
def save_waterbody(waterbody, path, dst_nodata = -9999):
    
    waterbody.profile["dtype"] = rasterio.float32
    waterbody.profile["nodata"] = dst_nodata
    
    with rasterio.open(path, "w", **waterbody.profile) as dst:
        dst.write(waterbody.array)