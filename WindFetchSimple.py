#!/usr/bin/env python3

'''
Simple commandline tool to calculate wind fetch for rasters. 

The script calculates wind fetch (the unobstructed length that wind can travel 
across water) from directions/angles/bearings specified by the user. The input
is a raster where all "water" cells share a single id-value. The output is 
saved to a raster file with one band for each direction/angle/bearing 
specified. Optinally, a summary raster with min, mean and max values can be
saved.

The raster should be in a projected coordinate system. Fetch length units are
the same as used in the raster. Water should be enclosed by land if fetch from 
all directions/angles/bearings are calculated. 

Fetch lengths are multiples of cell resolution. The approach is simple and
determines fetch lengths following a rotation.

File I/O are managed using rasterio and should support all GDAL-supported 
formats. Array rotation used scipy and other array manipulation use numpy.
'''

def main():
    import numpy as np
    import rasterio
    from scipy.ndimage.interpolation import rotate
    import argparse
    import os 
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help = "Path to input raster file", 
                        required = True, type = os.path.abspath)
    parser.add_argument("-o", "--output", help = "Path to output raster file", 
                        required = True, type = os.path.abspath)
    parser.add_argument("-d", "--directions", help = "Direction/angles/bearings from which the fetch should be calculated as comma-seperated string e.g. -d '45,90,135'.", required = True)
    parser.add_argument("-id", "--water_id", help = "Id value of water cells used to distinguish water from land", required = True, type = int)
    parser.add_argument("-s", "--summary", help = "Path to output summary (min, mean, max) of the calculated fetch lengths", required = False, type = os.path.abspath)
    
    args = parser.parse_args()
    
    filein = args.input
    fileout = args.output
    strdirs = args.directions
    water_id = args.water_id
    summary = args.summary
        
    dirs = [float(i) for i in strdirs.split(",")]
    
    print("Reading raster file from " + filein)
    with rasterio.open(filein) as ds_in:
        arr_in = ds_in.read(1).astype("float")
        meta_in = ds_in.profile
        resolution = ds_in.res[0]
        nrow, ncol = arr_in.shape
    
    arr_in[arr_in != water_id] = np.nan

    arr_in[arr_in == water_id] = -1

    def fetch_length(array, resolution):
    
        nrow, ncol = array.shape
        
        #fetch = np.full(ncol, np.nan) #-1*resolution
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
    
    def fetch_length_angle(array, resolution, nrow, ncol, angle):
            
        pad_width = estimated_pad(nrow, ncol, resolution)
        
        array_pad = padding(array, pad_width, np.nan)
    
        array_rot = rotate(array_pad, angle=angle, reshape=False, mode = "constant", cval = np.nan, order = 0)
    
        array_fetch = fetch_length(array_rot, resolution)
        
        array_inv_rot = rotate(array_fetch, angle=360-angle, reshape=False, mode = "constant", cval = np.nan, order = 0)
    
        array_inv_pad = padding(array_inv_rot, pad_width, -resolution, inverse = True)
        
        return(array_inv_pad)
        
    dirs_arrays = []
    
    for d in dirs:
        print("Calculating fetch from {} degrees".format(d))
        dirs_arrays.append(fetch_length_angle(arr_in, resolution, nrow, ncol, d))
        
    dirs_stack = np.stack(dirs_arrays)
    
    meta_in["count"] = len(dirs)
    meta_in["dtype"] = "float64"
    meta_in["nodata"] = 0
    
    print("Writing raster file with {} bands to ".format(len(dirs)) + fileout)
    with rasterio.open(fileout, "w", **meta_in) as dst:
        dst.write(dirs_stack)
    
    
    if summary:
        print("Calculating and writing summary to " + summary)
            
        stack_mean = np.mean(dirs_stack, axis = 0)
        stack_min = np.min(dirs_stack, axis = 0)
        stack_max = np.max(dirs_stack, axis = 0)
        
        meta_in["count"] = 3
        
        with rasterio.open(summary, "w", **meta_in) as dst:
            dst.write(np.stack([stack_min, stack_mean, stack_max]))
        
    
if __name__ == "__main__":
    main()
