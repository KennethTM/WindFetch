import numpy as np
import rasterio
from scipy.ndimage.interpolation import rotate
import copy

import multiprocessing
from joblib import Parallel, delayed


#The waterbody class
#Requires raster, profile, resolution and id value for water cells
class waterbody():

    def __init__(self, array, profile, water_id = None):
        self.array = np.array(array).astype("float32")
        self.count = array.shape[0]
        self.profile = profile
        self.resolution = profile["transform"][0]
        self.profile["count"] = self.count

        if water_id:
            self.water_id = water_id
            self.landwater = np.where(self.array == self.water_id, -1, np.nan)
      
    #Main function for calculating fetch from several directions
    def fetch(self, directions, weigths = None, minor_directions = None, minor_interval = None, method_vect = None):

        #Function for calculating fetch from one direction
        def fetch_single_dir(self, dir, method_vect = None):

            #Original function used to calculate fetch length
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

            def fetch_length_vect(array, resolution):
                w = array*-1
                v = w.flatten(order = "F")
                n = np.isnan(v)
                a = ~n
                c = np.cumsum(a)
                b = np.concatenate(([0.0], c[n]))
                d = np.diff(b,)
                v[n] = -d
                x=np.cumsum(v)
                y=np.reshape(x, w.shape, order = "F")*w*resolution
                return(y)

            #Function to estimate padding required before rotation
            def estimated_pad(array, resolution):
                nrow, ncol = array.shape
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

            #Prepare array for fetch calculation i.e padding and rotating            
            pad_width = estimated_pad(self.array, self.resolution)
            
            array_pad = padding(self.landwater, pad_width, np.nan)

            array_rot = rotate(array_pad, angle=dir, reshape=False, mode = "constant", cval = np.nan, order = 0)

            if method_vect:
                array_fetch = fetch_length_vect(array_rot, self.resolution)
            else:
                array_fetch = fetch_length(array_rot, self.resolution)
                
            array_inv_rot = rotate(array_fetch, angle=360-dir, reshape=False, mode = "constant", cval = np.nan, order = 0)
        
            array_inv_pad = padding(array_inv_rot, pad_width, -self.resolution, inverse = True)

            return(array_inv_pad)
        
        #if multi is True:
        #    num_cores = multiprocessing.cpu_count()
        #    #if __name__ == "__main__":
        #    dir_arrays = Parallel(n_jobs=num_cores)(delayed(fetch_single_dir)(self, i, method_vect) for i in directions)

        def minor_dir_list(directions, minor_interval, minor_directions):
            minor_seq = [i*minor_interval for i in range(minor_directions)]
            minor_seq_mid = minor_seq[int(len(minor_seq)/2)]
            all_directions = []
            for d in directions:
                for i in minor_seq:
                    all_directions.append((d+(i-minor_seq_mid))%360)
            return(all_directions)

        def divide_chunks(l, n): 
            for i in range(0, len(l), n):  
                yield l[i:i + n] 

        ######Tilføj loop for enkel dir og dir som er average af X minor dirs med Y afstand imellem
        #Calculate fetch length for each direction
        dir_arrays = []

        if minor_interval and minor_directions:
            all_directions = minor_dir_list(directions, minor_interval, minor_directions)
            all_dir_arrays = []
            for d in all_directions:
                array_single_dir = fetch_single_dir(self, dir=d, method_vect = method_vect)
                all_dir_arrays.append(array_single_dir)

            for i in divide_chunks(all_dir_arrays, minor_directions):
                dir_arrays.append(np.mean(np.stack(i), axis = 0))
            
        else:
            for d in directions:
                array_single_dir = fetch_single_dir(self, dir=d, method_vect = method_vect)
                dir_arrays.append(array_single_dir)
        
        #Perform weighting for each direction and mask by orignal landwater array
        if weigths:
            dir_arrays_weighted = [i*w for i, w in zip(dir_arrays, weigths)]
            fetch_array = np.stack(dir_arrays_weighted)*(self.landwater*-1)
        else:
            fetch_array = np.stack(dir_arrays)*(self.landwater*-1)

        #Return new waterbody object
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