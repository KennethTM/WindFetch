import numpy as np
import rasterio
from scipy.ndimage.interpolation import rotate
import copy

#The waterbody class
#Requires raster, profile, resolution and id value for water cells
class waterbody():

    def __init__(self, raster, profile, resolution, water_id):
        self.array = np.asarray(raster)
        self.landwater = np.where(raster == water_id, -1, np.nan)
        self.water_id = water_id
        self.profile = profile
        self.nrow = profile["height"]
        self.ncol = profile["width"]
        self.resolution = resolution

    #Main function for calculating fetch from several directions
    def wind_fetch(self, directions):

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
            
        dirs_arrays = []

        for d in directions:
            array_rot = rotate(array_pad, angle=d, reshape=False, mode = "constant", cval = np.nan, order = 0)
        
            array_fetch = fetch_length(array_rot, self.resolution)
            
            array_inv_rot = rotate(array_fetch, angle=360-d, reshape=False, mode = "constant", cval = np.nan, order = 0)
        
            array_inv_pad = padding(array_inv_rot, pad_width, -self.resolution, inverse = True)
        
            dirs_arrays.append(array_inv_pad)

        waterbody_copy = copy.copy(self)

        waterbody_copy.layers = np.stack(dirs_arrays)
        waterbody_copy.directions = directions
        
        return(waterbody_copy)

    def summary(self):
        stack_min = np.min(self.layers, axis = 0)
        stack_mean = np.mean(self.layers, axis = 0)
        stack_max = np.max(self.layers, axis = 0)

        waterbody_copy = copy.copy(self)

        waterbody_copy.layers = np.stack([stack_min, stack_mean, stack_max])

        return(waterbody_copy)

    def weighted_fetch(self, weights):
        weights = np.array(weights)

        if len(weights) != len(self.directions):
            print('Error: Number of weights not equal to number of fetch directions')
            return(1)
            
        if sum(weights) > 1.01 or sum(weights) < 0.99:
            print('Error: Sum of weights not equal to 1. The sum of the supplied weights is {}'.format(sum(weights)))
            return(1)

        waterbody_copy = copy.copy(self)

        waterbody_copy.layers = np.expand_dims(np.tensordot(self.layers, weights, axes = ([0],[0])), axis=0)

        return(waterbody_copy)

#Function for reading a raster and convert to object waterbody
def read_waterbody(path, water_id):
    
    with rasterio.open(path) as data:
        raster = data.read(1).astype("float")
        profile = data.profile
        resolution = data.res[0]
        
    return(waterbody(raster, profile, resolution, water_id))

#Write waterbody object to raster with one layer for each fetch direction
def save_waterbody(waterbody, path):
    
    waterbody.profile["count"] = waterbody.layers.shape[0]
    waterbody.profile["dtype"] = rasterio.float32
    waterbody.profile["nodata"] = 0
    
    with rasterio.open(path, "w", **waterbody.profile) as dst:
        dst.write(waterbody.layers.astype(rasterio.float32))