import numpy as np
import rasterio
from scipy.ndimage.interpolation import rotate
import copy
import gdal

class Waterbody():
    '''
    The Waterbody class
    Requires raster, profile, resolution and water_id value for water cells
    '''

    def __init__(self, array, profile, water_id = None):
        self.array = np.array(array).astype("float32")
        self.count = array.shape[0]
        self.profile = profile
        self.resolution = profile["transform"][0]
        self.profile["count"] = self.count

        if water_id:
            self.water_id = water_id
            self.landwater = np.where(self.array == self.water_id, -1, np.nan)

    @classmethod
    def read_waterbody(cls, path, water_id):
        'Read and create waterbody from GDAL supported raster file'
    
        with rasterio.open(path) as src:
            array = src.read(1)
            profile = src.profile
        
        return(cls(array, profile, water_id))

    def write_waterbody(self, path, dst_nodata = -9999):
        'Write array to GDAL supported raster file'

        self.profile["dtype"] = rasterio.float32
        self.profile["nodata"] = dst_nodata

        with rasterio.open(path, "w", **self.profile) as dst:
            dst.write(self.array)

    #Main function for calculating fetch from several directions
    def fetch(self, directions, minor_directions = None, minor_interval = None):
        '''
        Calculates fetch from arbitrary directions supplid as a list.
        
        Optionally, fetch can be calculate as the mean of N minor_directions
        centered around each direction with distance minor_interval.
        '''

        #Function for calculating fetch from one direction
        def fetch_single_dir(self, dir):

            #Function for the length calculation
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

            array_fetch = fetch_length_vect(array_rot, self.resolution)
                
            array_inv_rot = rotate(array_fetch, angle=360-dir, reshape=False, mode = "constant", cval = np.nan, order = 0)

            array_inv_pad = padding(array_inv_rot, pad_width, -self.resolution, inverse = True)

            return(array_inv_pad)
        
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

        #Calculate fetch length for each direction
        dir_arrays = []

        if minor_interval and minor_directions:
            all_directions = minor_dir_list(directions, minor_interval, minor_directions)
            all_dir_arrays = []
            for d in all_directions:
                array_single_dir = fetch_single_dir(self, dir=d)
                all_dir_arrays.append(array_single_dir)

            for i in divide_chunks(all_dir_arrays, minor_directions):
                dir_arrays.append(np.mean(np.stack(i), axis = 0))
            
        else:
            for d in directions:
                array_single_dir = fetch_single_dir(self, dir=d)
                dir_arrays.append(array_single_dir)
        
        fetch_array = np.stack(dir_arrays)

        #Return new fetch object
        fetch_profile = self.profile.copy()
        fetch = Fetch(fetch_array, fetch_profile)
        fetch.directions = directions

        return(fetch)

    def masking(self, waterbody, fill_value = None):
        'Apply mask using an object of class waterbody'

        if fill_value is not None:
            array_masked = np.where(np.isnan(self.array), fill_value, self.array)*(waterbody.landwater*-1)
        else:
            array_masked = self.array*(waterbody.landwater*-1)

        mask_profile = self.profile.copy()
        mask = Fetch(array_masked, mask_profile)
        mask.mask = True

        return(mask)    

class Fetch(Waterbody):
    '''
    The Fetch class - inherits from class Waterbody
    Provides methods for fetch arrays
    '''

    def summary(self, stats):
        '''
        Apply one or multiple summary statistics as a list for summarizing fetch array.
        Valid stats include: mean, min, max, median, range, std and var.
        '''

        stats_dict = {"mean": np.mean, "min": np.min, "max": np.max, "range": np.ptp, "std": np.std, "median": np.median, "var": np.var}

        summary_list = [stats_dict[i](self.array, axis = 0) for i in stats]
        summary_array = np.stack(summary_list)

        summary_profile = self.profile.copy()
        summary = Fetch(summary_array, summary_profile)
        summary.stats = stats

        return(summary)

    def weighting(self, weights):
        'Multiply each direction by a weight. Weights are normalized by the sum of all weights.'
        weight_norm = np.array(weights)/np.array(weights).sum()

        weight_list = [i*w for i, w in zip(self.array, weight_norm)]
        weight_array = np.stack(weight_list)

        weight_profile = self.profile.copy()
        weight = Fetch(weight_array, weight_profile)
        weight.weigths = weight
        weight.weigths_norm = weight_norm

        return(weight)
