import numpy as np
import rasterio
from scipy.ndimage.interpolation import rotate

class waterbody():
    
    def __init__(self, raster, profile, resolution, water):
        self.array = np.asarray(raster)
        self.landwater = np.where(raster == water, -1, np.nan)
        self.profile = profile
        self.nrow = profile["height"]
        self.ncol = profile["width"]
        self.resolution = resolution
        
    def fetch_length_angle(self, directions):
        
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
    
        def estimated_pad(nrow, ncol, resolution):
            xlen = resolution*ncol
            ylen = resolution*nrow
            padwidth = np.sqrt(xlen**2+ylen**2) - min([xlen, ylen])
            return(int(padwidth/2/resolution)+1)
            
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
        
        dirs_stack = np.stack(dirs_arrays)

        self.directions = dirs_stack
        
        return(self)

def read_waterbody(path, water):
    
    with rasterio.open(path) as data:
        raster = data.read(1).astype("float")
        profile = data.profile
        resolution = data.res[0]
        
    return(waterbody(raster, profile, resolution, water))

def save_waterbody(waterbody, path):
    
    waterbody.profile["count"] = waterbody.directions.shape[0]
    waterbody.profile["dtype"] = "float64"
    waterbody.profile["nodata"] = 0
    
    with rasterio.open(path, "w", **waterbody.profile) as dst:
        dst.write(waterbody.directions)



    
#Test
path_test = '/home/kenneth/Documents/WindFetch/test/lake_test.tif'
path_test_out = '/home/kenneth/Documents/WindFetch/test/lake_test_out.tif'

lake = read_waterbody(path_test, 1)

fetch = lake.fetch_length_angle([45, 135])

save_waterbody(fetch, path_test_out)

from matplotlib import pyplot as plt
plt.imshow(fetch[,:,:]) 


